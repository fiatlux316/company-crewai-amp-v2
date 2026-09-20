from pathlib import Path
import zipfile

from company_crew_devkit.packager import build_package


def test_package_contains_manifest_and_src(tmp_path: Path):
    root = Path(__file__).parents[1] / "crew_packages" / "incident_report_crew"
    artifact = build_package(root, tmp_path)
    assert artifact.is_file()
    with zipfile.ZipFile(artifact) as zf:
        assert "crew-manifest.json" in zf.namelist()
        assert any(name.startswith("src/") for name in zf.namelist())
