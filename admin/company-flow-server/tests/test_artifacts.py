import os
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from company_flow_server.app import app

class TestArtifactsAPI(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.artifacts_root = Path(self.tmp_dir.name)
        os.environ["ARTIFACTS_ROOT"] = str(self.artifacts_root)
        self.client = TestClient(app)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_download_artifact_success(self):
        run_id = "test-run-123"
        run_dir = self.artifacts_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        file_path = run_dir / "spec.md"
        file_path.write_text("# Persona Spec\nSample output content.", encoding="utf-8")

        response = self.client.get(f"/api/v1/runs/{run_id}/artifacts/spec.md")
        self.assertEqual(response.status_code, 200)
        self.assertIn("# Persona Spec", response.text)

    def test_download_artifact_not_found(self):
        response = self.client.get("/api/v1/runs/nonexistent-run/artifacts/spec.md")
        self.assertEqual(response.status_code, 404)

    def test_download_artifact_path_traversal_blocked(self):
        run_id = "test-run-123"
        run_dir = self.artifacts_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        response = self.client.get(f"/api/v1/runs/{run_id}/artifacts/../other_file.txt")
        self.assertIn(response.status_code, (400, 404))

if __name__ == "__main__":
    unittest.main()
