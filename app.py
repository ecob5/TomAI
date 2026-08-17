"""TomAI demonstration application."""

import os
from datetime import date

from flask import Flask, render_template


def create_app(test_config=None):
    """Create the small, interface-only Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "demo-key"),
    )
    if test_config is not None:
        app.config.update(test_config)

    @app.route("/")
    def index():
        medications = [
            {"name": "Vitamin D", "dosage": "1 capsule", "instructions": "After breakfast"},
            {"name": "Blood pressure medicine", "dosage": "1 tablet", "instructions": "With water"},
        ]
        schedules = [
            {"reminder_time": "08:00", "name": "Vitamin D", "dosage": "1 capsule", "status": "taken"},
            {"reminder_time": "13:00", "name": "Blood pressure medicine", "dosage": "1 tablet", "status": "pending"},
            {"reminder_time": "20:00", "name": "Vitamin D", "dosage": "1 capsule", "status": "pending"},
        ]
        return render_template(
            "index.html",
            medications=medications,
            schedules=schedules,
            today=date.today().strftime("%B %d, %Y"),
        )

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
