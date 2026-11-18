import unittest
from unittest.mock import patch

import mysql.connector

from app import app


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "healthy")

    def test_reject_empty_employee(self):
        response = self.client.post(
            "/employees",
            data={"name": "", "role": ""},
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_long_name(self):
        response = self.client.post(
            "/employees",
            data={"name": "a" * 101, "role": "Engineer"},
        )

        self.assertEqual(response.status_code, 400)

    @patch("app.get_connection")
    def test_readiness_failure(self, mock_connection):
        mock_connection.side_effect = mysql.connector.Error(
            "Database unavailable"
        )

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
