"""Tests for the main TomAI user flows."""

import os
import tempfile
import unittest

from app import create_app
from database import get_db, init_db


class TomAITestCase(unittest.TestCase):
    def setUp(self):
        file_descriptor, self.database_path = tempfile.mkstemp()
        os.close(file_descriptor)

        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE": self.database_path,
            }
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.unlink(self.database_path)

    def register(self, name="Ada", email="ada@example.com"):
        return self.client.post(
            "/register",
            data={"name": name, "email": email, "password": "cs50test"},
            follow_redirects=True,
        )

    def add_medication(self, name="Vitamin D"):
        return self.client.post(
            "/medications",
            data={
                "name": name,
                "dosage": "1 capsule",
                "reminder_time": "08:30",
                "instructions": "After breakfast",
            },
            follow_redirects=True,
        )

    def test_public_pages_and_account_pages_load(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/about").status_code, 200)
        self.assertEqual(self.client.get("/register").status_code, 200)
        self.assertEqual(self.client.get("/login").status_code, 200)

    def test_registration_starts_a_session(self):
        response = self.register()

        self.assertIn(b"Hello, Ada", response.data)
        with self.client.session_transaction() as user_session:
            self.assertIn("user_id", user_session)

        with self.app.app_context():
            saved_password = get_db().execute(
                "SELECT password_hash FROM users"
            ).fetchone()["password_hash"]
            self.assertNotEqual(saved_password, "cs50test")

    def test_user_can_log_out_and_log_in_again(self):
        self.register()
        self.client.post("/logout")

        response = self.client.post(
            "/login",
            data={"email": "ada@example.com", "password": "cs50test"},
            follow_redirects=True,
        )

        self.assertIn(b"Hello, Ada", response.data)

    def test_duplicate_email_is_rejected(self):
        self.register()
        self.client.post("/logout")
        response = self.register(name="Another Ada")

        self.assertIn(b"already exists", response.data)
        with self.app.app_context():
            users = get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]
            self.assertEqual(users, 1)

    def test_medication_is_saved_and_displayed_after_reload(self):
        self.register()
        self.add_medication()

        response = self.client.get("/")
        self.assertIn(b"Vitamin D", response.data)
        self.assertIn(b"08:30", response.data)

        with self.app.app_context():
            medication = get_db().execute(
                "SELECT name, dosage FROM medications"
            ).fetchone()
            self.assertEqual(medication["name"], "Vitamin D")
            self.assertEqual(medication["dosage"], "1 capsule")

    def test_dose_can_be_marked_as_taken(self):
        self.register()
        self.add_medication()

        with self.app.app_context():
            schedule_id = get_db().execute("SELECT id FROM schedules").fetchone()["id"]

        response = self.client.post(
            f"/doses/{schedule_id}/taken", follow_redirects=True
        )
        self.assertIn(b"Taken", response.data)

        with self.app.app_context():
            dose = get_db().execute("SELECT status FROM dose_records").fetchone()
            self.assertEqual(dose["status"], "taken")

    def test_medication_can_be_removed(self):
        self.register()
        self.add_medication("Ibuprofen")

        with self.app.app_context():
            medication_id = get_db().execute(
                "SELECT id FROM medications"
            ).fetchone()["id"]

        response = self.client.post(
            f"/medications/{medication_id}/delete", follow_redirects=True
        )
        self.assertNotIn(b"Ibuprofen", response.data)

        with self.app.app_context():
            medications = get_db().execute(
                "SELECT COUNT(*) FROM medications"
            ).fetchone()[0]
            schedules = get_db().execute(
                "SELECT COUNT(*) FROM schedules"
            ).fetchone()[0]
            self.assertEqual(medications, 0)
            self.assertEqual(schedules, 0)

    def test_private_actions_redirect_to_login(self):
        response = self.client.post("/medications", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
