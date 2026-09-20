from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone

from company_flow_server.contracts.manifest import CrewManifest


class CrewRegistry:
    """Versioned team registry for independently developed Crew packages."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def deploy(self, artifact: str | Path, *, overwrite: bool = False) -> CrewManifest:
        artifact = Path(artifact).resolve()
        if artifact.suffix != ".crewpkg":
            raise ValueError("artifact must use .crewpkg extension")

        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            with zipfile.ZipFile(artifact) as zf:
                names = zf.namelist()
                if "crew-manifest.json" not in names:
                    raise ValueError("package missing crew-manifest.json")
                if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                    raise ValueError("unsafe path in package")
                zf.extractall(temp)
            manifest = CrewManifest.load(temp / "crew-manifest.json")

            target = self.root / manifest.crew_id / manifest.version
            if target.exists() and not overwrite:
                raise FileExistsError(f"crew already deployed: {manifest.crew_id}@{manifest.version}")
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(artifact, target / "package.crewpkg")
            shutil.copytree(temp / "src", target / "src")
            shutil.copy2(temp / "crew-manifest.json", target / "crew-manifest.json")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            (target / "deployment.json").write_text(
                json.dumps({"sha256": digest, "deployed_at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8"
            )
        return manifest

    def delete(self, crew_id: str, version: str) -> None:
        target = self.resolve(crew_id, version)
        shutil.rmtree(target)
        parent = target.parent
        if parent.exists() and not any(parent.iterdir()): parent.rmdir()

    def resolve(self, crew_id: str, version: str) -> Path:
        target = self.root / crew_id / version
        if not (target / "crew-manifest.json").is_file():
            raise KeyError(f"crew not deployed: {crew_id}@{version}")
        return target

    def manifest(self, crew_id: str, version: str) -> CrewManifest:
        return CrewManifest.load(self.resolve(crew_id, version) / "crew-manifest.json")

    def list_versions(self, crew_id: str) -> list[str]:
        path = self.root / crew_id
        if not path.exists():
            return []
        return sorted(p.name for p in path.iterdir() if p.is_dir())

    def list_deployments(self) -> list[dict]:
        items: list[dict] = []
        if not self.root.exists():
            return items
        for crew_dir in sorted(p for p in self.root.iterdir() if p.is_dir()):
            for version_dir in sorted((p for p in crew_dir.iterdir() if p.is_dir()), reverse=True):
                manifest_file = version_dir / "crew-manifest.json"
                if not manifest_file.is_file():
                    continue
                raw = json.loads(manifest_file.read_text(encoding="utf-8"))
                deployment = {}
                dep_file = version_dir / "deployment.json"
                if dep_file.is_file(): deployment = json.loads(dep_file.read_text(encoding="utf-8"))
                items.append({
                    "crew_id": raw.get("crew_id", crew_dir.name),
                    "version": raw.get("version", version_dir.name),
                    "name": raw.get("name", crew_dir.name),
                    "owner": raw.get("owner", ""),
                    "description": raw.get("description", ""),
                    "tags": raw.get("tags", []),
                    "input_schema": raw.get("input_schema", {}),
                    "output_schema": raw.get("output_schema", {}),
                    "deployed_at": deployment.get("deployed_at", ""),
                })
        return items
