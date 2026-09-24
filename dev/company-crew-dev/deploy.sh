crew_name=$1
ver=1.0.0

echo uv run crew-dev package crew_packages/${crew_name} --output dist
uv run crew-dev package crew_packages/${crew_name} --output dist
sleep 1
echo uv run crew-dev deploy dist/ops.${crew_name}-${ver}.crewpkg --server-url http://localhost:8080
uv run crew-dev deploy dist/ops.${crew_name}-${ver}.crewpkg --server-url http://localhost:8080
