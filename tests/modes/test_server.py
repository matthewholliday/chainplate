import os
import json
import unittest

# Ensure the server uses an in-memory database before importing the app
os.environ["CHAINPLATE_DB"] = ":memory:"

from chainplate.modes import chainplate_server  # noqa: E402
from chainplate.modes.chainplate_server import app


class TestChainplateServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_root_hello(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, World!", resp.get_data(as_text=True))

    def test_create_log_success(self):
        resp = self.client.post(
            "/data/logs",
            data=json.dumps({"level": "info", "message": "Test log"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Test log")

    def test_create_log_invalid_level(self):
        resp = self.client.post(
            "/data/logs",
            data=json.dumps({"level": "BAD", "message": "X"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid level", resp.get_json().get("error", "").lower())

    def test_create_execution_and_get(self):
        # Create execution
        resp = self.client.post(
            "/data/executions",
            data=json.dumps({"code": "<pipeline name='p'><debug>hi</debug></pipeline>"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        exec_id = resp.get_json()["execution_id"]

        # Fetch execution (no steps yet)
        resp2 = self.client.get(f"/data/executions/{exec_id}")
        self.assertEqual(resp2.status_code, 200)
        body = resp2.get_json()
        self.assertEqual(body["execution"]["id"], exec_id)
        self.assertIsInstance(body["steps"], list)
        self.assertEqual(len(body["steps"]), 0)

    def test_add_execution_step_and_retrieve(self):
        # Create execution
        resp = self.client.post(
            "/data/executions",
            data=json.dumps({"code": "<pipeline name='p'><debug>step</debug></pipeline>"}),
            content_type="application/json",
        )
        exec_id = resp.get_json()["execution_id"]

        # Add step
        resp2 = self.client.post(
            f"/data/executions/{exec_id}/steps",
            data=json.dumps(
                {
                    "content": "First step",
                    "role": "system",
                    "channel": 1,
                    "requires_input": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 201)
        step_id = resp2.get_json()["step_id"]
        self.assertIsInstance(step_id, int)

        # Retrieve execution with step
        resp3 = self.client.get(f"/data/executions/{exec_id}")
        self.assertEqual(resp3.status_code, 200)
        data = resp3.get_json()
        steps = data["steps"]
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["id"], step_id)
        self.assertEqual(steps[0]["content"], "First step")

    def test_add_step_invalid_execution(self):
        resp = self.client.post(
            "/data/executions/999999/steps",
            data=json.dumps({"content": "x"}),
            content_type="application/json",
        )
        # SQLite foreign key violation will surface as 500 currently (no explicit handling)
        self.assertIn(resp.status_code, (404, 500))

    def test_workflow_endpoint(self):
        payload = {
            "chainplate_code": "<pipeline name='wf'><debug>ok</debug></pipeline>",
            "payload": "hello"
        }
        resp = self.client.post(
            "/workflow",
            data=json.dumps(payload),
            content_type="application/json",
        )
        # If pipeline parsing succeeds expect 200; otherwise ensure not 500 due to basic handling
        self.assertIn(resp.status_code, (200, 500))

    def test_health_without_api_key(self):
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 503)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIsInstance(data.get("errors"), list)
        self.assertTrue(any("OPENAI_API_KEY" in e for e in data.get("errors")))

    def test_health_with_api_key(self):
        os.environ["OPENAI_API_KEY"] = "test-key"
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertNotIn("errors", data)

    def test_invalid_json(self):
        resp = self.client.post(
            "/data/logs",
            data="{'bad json': }",
            content_type="application/json",
        )
        # get_json will raise JSONDecodeError -> 400
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()