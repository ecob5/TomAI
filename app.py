"""TomAI medication reminder application.

AI was used to help review and reorganize parts of this project. The final
choices, testing, and understanding of the code remain the author's work.
"""

import os
import sqlite3
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_app


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-in-production"),
        DATABASE=os.path.join(app.instance_path, "tomai.db"),
    )

    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    init_app(app)

    def logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            return None

        return get_db().execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if logged_in_user() is None:
                flash("Please sign in to continue.", "error")
                return redirect(url_for("login"))
            return view(**kwargs)

        return wrapped_view

    @app.context_processor
    def add_user_to_templates():
        return {"current_user": logged_in_user()}

    @app.route("/")
    def index():
        user = logged_in_user()
        if user is None:
            return render_template("index.html")

        db = get_db()
        medications = db.execute(
            """
            SELECT medications.id, medications.name, medications.dosage,
                   medications.instructions, schedules.reminder_time
            FROM medications
            JOIN schedules ON schedules.medication_id = medications.id
            WHERE medications.user_id = ?
            ORDER BY schedules.reminder_time, medications.name
            """,
            (user["id"],),
        ).fetchall()

        schedules = db.execute(
            """
            SELECT schedules.id AS schedule_id, schedules.reminder_time,
                   medications.name, medications.dosage,
                   COALESCE(dose_records.status, 'pending') AS status
            FROM schedules
            JOIN medications ON medications.id = schedules.medication_id
            LEFT JOIN dose_records
                ON dose_records.schedule_id = schedules.id
                AND date(dose_records.scheduled_for) = ?
            WHERE medications.user_id = ?
            ORDER BY schedules.reminder_time
            """,
            (date.today().isoformat(), user["id"]),
        ).fetchall()

        return render_template(
            "index.html",
            medications=medications,
            schedules=schedules,
            today=date.today().strftime("%B %d, %Y"),
        )

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET":
            return render_template("auth.html", mode="register")

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in every field.", "error")
            return render_template("auth.html", mode="register")
        if len(password) < 6:
            flash("Your password must have at least 6 characters.", "error")
            return render_template("auth.html", mode="register")

        try:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
            return render_template("auth.html", mode="register")

        session.clear()
        session["user_id"] = cursor.lastrowid
        return redirect(url_for("index"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("auth.html", mode="login")

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
            return render_template("auth.html", mode="login")

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("index"))

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    @app.post("/medications")
    @login_required
    def add_medication():
        name = request.form.get("name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        reminder_time = request.form.get("reminder_time", "").strip()
        instructions = request.form.get("instructions", "").strip()

        if not name or not dosage or not reminder_time:
            flash("Medication, dosage, and reminder time are required.", "error")
            return redirect(url_for("index"))

        try:
            datetime.strptime(reminder_time, "%H:%M")
        except ValueError:
            flash("Please enter a valid reminder time.", "error")
            return redirect(url_for("index"))

        db = get_db()
        medication = db.execute(
            """
            INSERT INTO medications (user_id, name, dosage, instructions)
            VALUES (?, ?, ?, ?)
            """,
            (logged_in_user()["id"], name, dosage, instructions),
        )
        db.execute(
            "INSERT INTO schedules (medication_id, reminder_time) VALUES (?, ?)",
            (medication.lastrowid, reminder_time),
        )
        db.commit()

        flash(f"{name} was added.", "success")
        return redirect(url_for("index"))

    @app.post("/medications/<int:medication_id>/delete")
    @login_required
    def delete_medication(medication_id):
        db = get_db()
        result = db.execute(
            "DELETE FROM medications WHERE id = ? AND user_id = ?",
            (medication_id, logged_in_user()["id"]),
        )
        db.commit()

        if result.rowcount == 0:
            flash("Medication not found.", "error")
        else:
            flash("Medication removed.", "success")
        return redirect(url_for("index"))

    @app.post("/doses/<int:schedule_id>/<status>")
    @login_required
    def update_dose(schedule_id, status):
        if status not in {"taken", "skipped"}:
            flash("Invalid dose status.", "error")
            return redirect(url_for("index"))

        db = get_db()
        schedule = db.execute(
            """
            SELECT schedules.id, schedules.reminder_time
            FROM schedules
            JOIN medications ON medications.id = schedules.medication_id
            WHERE schedules.id = ? AND medications.user_id = ?
            """,
            (schedule_id, logged_in_user()["id"]),
        ).fetchone()

        if schedule is None:
            flash("Reminder not found.", "error")
            return redirect(url_for("index"))

        scheduled_for = (
            f"{date.today().isoformat()} {schedule['reminder_time']}:00"
        )
        db.execute(
            """
            INSERT INTO dose_records (schedule_id, scheduled_for, status, responded_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(schedule_id, scheduled_for) DO UPDATE SET
                status = excluded.status,
                responded_at = CURRENT_TIMESTAMP
            """,
            (schedule_id, scheduled_for, status),
        )
        db.commit()

        flash("Dose status updated.", "success")
        return redirect(url_for("index"))

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
