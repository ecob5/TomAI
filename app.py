import os
import sqlite3
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_app


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE=app.instance_path + "/tomai.db",
    )

    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    init_app(app)

    def current_user():
        user_id = session.get("user_id")
        if user_id is None:
            return None
        return get_db().execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    @app.route("/")
    def index():
        user = current_user()
        if user is None:
            return render_template("index.html")

        db = get_db()
        medications = db.execute(
            """
            SELECT id, name, dosage, instructions, stock_quantity
            FROM medications
            WHERE user_id = ? AND active = 1
            ORDER BY name
            """,
            (user["id"],),
        ).fetchall()

        today = date.today().isoformat()
        schedules = db.execute(
            """
            SELECT schedules.id AS schedule_id,
                   schedules.reminder_time,
                   medications.name,
                   medications.dosage,
                   COALESCE(dose_records.status, 'pending') AS status
            FROM schedules
            JOIN medications ON medications.id = schedules.medication_id
            LEFT JOIN dose_records
                ON dose_records.schedule_id = schedules.id
                AND date(dose_records.scheduled_for) = ?
            WHERE medications.user_id = ? AND medications.active = 1
            ORDER BY schedules.reminder_time
            """,
            (today, user["id"]),
        ).fetchall()

        return render_template(
            "index.html",
            medications=medications,
            schedules=schedules,
            today=date.today().strftime("%d/%m/%Y"),
        )

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not name or not email or len(password) < 4:
                flash(
                    "Preencha todos os campos. A senha deve ter pelo menos 4 caracteres.",
                    "error",
                )
            else:
                try:
                    db = get_db()
                    cursor = db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    db.commit()
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    return redirect(url_for("index"))
                except sqlite3.IntegrityError:
                    flash("Este e-mail já está cadastrado.", "error")
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

            valid_password = user and check_password_hash(
                user["password_hash"], password
            )
            if not valid_password:
                flash("E-mail ou senha incorretos.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("index"))
        return render_template("auth.html", mode="login")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    @app.post("/medications")
    def add_medication():
        user = current_user()
        if user is None:
            return redirect(url_for("login"))
        name = request.form.get("name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        reminder_time = request.form.get("reminder_time", "").strip()
        instructions = request.form.get("instructions", "").strip()
        stock_value = request.form.get("stock_quantity", "").strip()

        if not name or not dosage or not reminder_time:
            flash("Informe medicamento, dosagem e horário.", "error")
            return redirect(url_for("index"))

        try:
            datetime.strptime(reminder_time, "%H:%M")
        except ValueError:
            flash("Informe um horário válido.", "error")
            return redirect(url_for("index"))

        stock_quantity = None
        if stock_value:
            try:
                stock_quantity = int(stock_value)
                if stock_quantity < 0:
                    raise ValueError
            except ValueError:
                flash("O estoque deve ser um número inteiro igual ou maior que zero.", "error")
                return redirect(url_for("index"))

        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO medications
                (user_id, name, dosage, instructions, stock_quantity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], name, dosage, instructions, stock_quantity),
        )
        db.execute(
            "INSERT INTO schedules (medication_id, reminder_time) VALUES (?, ?)",
            (cursor.lastrowid, reminder_time),
        )
        db.commit()
        flash("Medicamento adicionado.", "success")
        return redirect(url_for("index"))

    @app.post("/medications/<int:medication_id>/delete")
    def delete_medication(medication_id):
        user = current_user()
        if user is None:
            return redirect(url_for("login"))
        db = get_db()
        result = db.execute(
            "DELETE FROM medications WHERE id = ? AND user_id = ?",
            (medication_id, user["id"]),
        )
        db.commit()
        if result.rowcount:
            flash("Medicamento removido.", "success")
        else:
            flash("Medicamento não encontrado.", "error")
        return redirect(url_for("index"))

    @app.post("/doses/<int:schedule_id>/<status>")
    def update_dose(schedule_id, status):
        user = current_user()
        if user is None:
            return redirect(url_for("login"))
        if status not in {"taken", "skipped"}:
            return redirect(url_for("index"))

        db = get_db()
        schedule = db.execute(
            """
            SELECT schedules.id, schedules.reminder_time
            FROM schedules
            JOIN medications ON medications.id = schedules.medication_id
            WHERE schedules.id = ? AND medications.user_id = ?
            """,
            (schedule_id, user["id"]),
        ).fetchone()

        if schedule:
            today = date.today().isoformat()
            dose = db.execute(
                "SELECT id FROM dose_records WHERE schedule_id = ? AND date(scheduled_for) = ?",
                (schedule_id, today),
            ).fetchone()

            if dose:
                db.execute(
                    """
                    UPDATE dose_records
                    SET status = ?, responded_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, dose["id"]),
                )
            else:
                scheduled_for = f"{today} {schedule['reminder_time']}:00"
                db.execute(
                    """
                    INSERT INTO dose_records
                        (schedule_id, scheduled_for, status, responded_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (schedule_id, scheduled_for, status),
                )
            db.commit()
            flash("Dose atualizada.", "success")
        else:
            flash("Horário de medicamento não encontrado.", "error")
        return redirect(url_for("index"))

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
