# Crew Package Contract v1

- Artifact: `.crewpkg` (ZIP)
- Required file: `crew-manifest.json`
- Required directory: `src/`
- Manifest: `schema_version = 1`
- Entrypoint format: `module:function`
- Runtime call: `run(inputs: dict, runtime) -> dict`
- Recommended result: `{ "outputs": {...}, "metadata": {...} }`
- Flow server validates input/output against the manifest contract.
- Crew source must not import modules from the Flow server repository.
- Production Flow pins an exact immutable `crew_id@version`.
