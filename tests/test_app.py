import os
import tempfile
import unittest

from app import create_app
from database import get_db, init_db


class TomAITestCase(unittest.TestCase):
    def setUp(self):
        descriptor, self.database_path = tempfile.mkstemp()
        os.close(descriptor)
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE": self.database_path,
            }
        )
        with self.app.app_context():
            init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        os.unlink(self.database_path)

    def register(self):
        return self.client.post(
            "/register",
            data={"name": "Ada", "email": "ada@example.com", "password": "cs50"},
            follow_redirects=True,
        )

    def test_landing_pages_load(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/about").status_code, 200)

    def test_complete_medication_flow(self):
        response = self.register()
        self.assertIn("Olá, Ada".encode(), response.data)

        response = self.client.post(
            "/medications",
            data={
                "name": "Vitamina D",
                "dosage": "1 comprimido",
                "reminder_time": "08:30",
                "stock_quantity": "30",
                "instructions": "Após o café",
            },
            follow_redirects=True,
        )
        self.assertIn("Vitamina D".encode(), response.data)

        with self.app.app_context():
            schedule_id = get_db().execute("SELECT id FROM schedules").fetchone()["id"]

        response = self.client.post(
            f"/doses/{schedule_id}/taken", follow_redirects=True
        )
        self.assertIn("Tomada".encode(), response.data)

        with self.app.app_context():
            dose = get_db().execute("SELECT * FROM dose_records").fetchone()
            self.assertEqual(dose["status"], "taken")
            self.assertTrue(str(dose["scheduled_for"]).endswith("08:30:00"))

    def test_rejects_invalid_stock(self):
        self.register()
        response = self.client.post(
            "/medications",
            data={
                "name": "Teste",
                "dosage": "1 unidade",
                "reminder_time": "08:00",
                "stock_quantity": "-1",
            },
            follow_redirects=True,
        )
        self.assertIn("igual ou maior que zero".encode(), response.data)
        with self.app.app_context():
            count = get_db().execute("SELECT COUNT(*) FROM medications").fetchone()[0]
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
