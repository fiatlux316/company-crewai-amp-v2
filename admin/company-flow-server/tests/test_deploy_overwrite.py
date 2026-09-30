import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

from company_flow_server.app import app

class TestDeployOverwriteAPI(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.registry_root = Path(self.tmp_dir.name) / "registry"
        os.environ["CREW_REGISTRY_ROOT"] = str(self.registry_root)
        os.environ["AUTH_DISABLED"] = "true"

        from unittest.mock import patch
        self.audit_patcher = patch("company_flow_server.app.audit")
        self.mock_audit = self.audit_patcher.start()

        from company_flow_server.app import app, CrewRegistry
        import company_flow_server.app as app_module
        app_module.registry = CrewRegistry(self.registry_root)
        self.client = TestClient(app)

        # Create dummy crew package
        self.package_dir = Path(self.tmp_dir.name) / "pkg"
        (self.package_dir / "src" / "demo").mkdir(parents=True)
        self.manifest = {
            "schema_version": 1,
            "crew_id": "test.overwrite",
            "version": "1.0.0",
            "name": "Test Overwrite",
            "owner": "tester",
            "entrypoint": "demo.entrypoint:run",
            "input_schema": {"type": "object", "required": [], "properties": {}},
            "output_schema": {"type": "object", "required": [], "properties": {}},
        }
        (self.package_dir / "crew-manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.package_dir / "src" / "demo" / "entrypoint.py").write_text("def run(inputs, runtime): return {}\n", encoding="utf-8")
        self.crewpkg_path = Path(self.tmp_dir.name) / "test.overwrite.crewpkg"
        with zipfile.ZipFile(self.crewpkg_path, "w") as zf:
            zf.write(self.package_dir / "crew-manifest.json", "crew-manifest.json")
            zf.write(self.package_dir / "src" / "demo" / "entrypoint.py", "src/demo/entrypoint.py")
        self.pkg_bytes = self.crewpkg_path.read_bytes()

    def tearDown(self):
        self.audit_patcher.stop()
        self.tmp_dir.cleanup()

    def test_deploy_duplicate_fails_without_overwrite(self):
        headers = {"X-Crew-Filename": "test.overwrite.crewpkg"}
        # 1st deploy -> 200 OK
        resp1 = self.client.post("/api/v1/crews/deploy", content=self.pkg_bytes, headers=headers)
        self.assertEqual(resp1.status_code, 200)

        # 2nd deploy without overwrite -> 409 Conflict
        resp2 = self.client.post("/api/v1/crews/deploy", content=self.pkg_bytes, headers=headers)
        self.assertEqual(resp2.status_code, 409)

    def test_deploy_duplicate_succeeds_with_query_param(self):
        headers = {"X-Crew-Filename": "test.overwrite.crewpkg"}
        resp1 = self.client.post("/api/v1/crews/deploy", content=self.pkg_bytes, headers=headers)
        self.assertEqual(resp1.status_code, 200)

        # 2nd deploy with ?overwrite=true -> 200 OK
        resp2 = self.client.post("/api/v1/crews/deploy?overwrite=true", content=self.pkg_bytes, headers=headers)
        self.assertEqual(resp2.status_code, 200)

    def test_deploy_duplicate_succeeds_with_header(self):
        headers = {"X-Crew-Filename": "test.overwrite.crewpkg"}
        resp1 = self.client.post("/api/v1/crews/deploy", content=self.pkg_bytes, headers=headers)
        self.assertEqual(resp1.status_code, 200)

        # 2nd deploy with X-Crew-Overwrite: true header -> 200 OK
        headers_overwrite = {"X-Crew-Filename": "test.overwrite.crewpkg", "X-Crew-Overwrite": "true"}
        resp2 = self.client.post("/api/v1/crews/deploy", content=self.pkg_bytes, headers=headers_overwrite)
        self.assertEqual(resp2.status_code, 200)

if __name__ == "__main__":
    unittest.main()
