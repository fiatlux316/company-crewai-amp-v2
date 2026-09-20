from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

from company_crew_sdk.manifest import CrewManifest


def build_package(project_dir: str | Path, output_dir: str | Path) -> Path:
    project = Path(project_dir).resolve()
    manifest = CrewManifest.load(project / "crew-manifest.json")
    src = project / "src"
    if not src.is_dir():
        raise ValueError("crew project must contain src/")

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / f"{manifest.crew_id}-{manifest.version}.crewpkg"
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(project / "crew-manifest.json", "crew-manifest.json")
        for path in sorted(src.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                zf.write(path, path.relative_to(project).as_posix())
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.with_suffix(artifact.suffix + ".sha256").write_text(digest + "\n", encoding="utf-8")
    return artifact
