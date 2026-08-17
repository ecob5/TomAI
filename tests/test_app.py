import unittest

from app import create_app


class TomAITestCase(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_demo_pages_load(self):
        home = self.client.get("/")
        about = self.client.get("/about")
        self.assertEqual(home.status_code, 200)
        self.assertEqual(about.status_code, 200)
        self.assertIn(b"Demo mode", home.data)
        self.assertIn(b"Good morning", home.data)

    def test_account_routes_do_not_exist(self):
        self.assertEqual(self.client.get("/register").status_code, 404)
        self.assertEqual(self.client.get("/login").status_code, 404)


if __name__ == "__main__":
    unittest.main()
