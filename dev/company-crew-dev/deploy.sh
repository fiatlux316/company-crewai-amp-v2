#!/bin/bash

crew_name=$1
ver=$2

if [ -z "${crew_name}" ]; then
    echo "Usage : deploy.sh [crew_name] [version]"
    exit 1
fi

if [ -z "${ver}" ]; then
    ver="1.0.0"
fi

# ver 이 1.0.0 아닐 경우  
# 해당 crew 의 crew-manifest.json 의 version 정보를 입력값에 맞게 수정해야 한다.
echo uv run crew-dev package crew_packages/${crew_name} --output dist
uv run crew-dev package crew_packages/${crew_name} --output dist
sleep 1
echo uv run crew-dev deploy dist/ops.${crew_name}-${ver}.crewpkg --overwrite
uv run crew-dev deploy dist/ops.${crew_name}-${ver}.crewpkg --overwrite
