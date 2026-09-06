import unittest

from app import app


class WebSmartQuotesTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_checkbox_is_off_by_default(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('name="smart_quotes"', html)
        self.assertNotIn('name="smart_quotes" checked', html)


if __name__ == "__main__":
    unittest.main()
