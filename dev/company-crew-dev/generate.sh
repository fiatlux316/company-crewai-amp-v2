#!/bin/bash
crew_name=$1

if [ -z "${crew_name}" ]; then
    echo "Usage : generate.sh [crew_name]"
    exit 1
fi

echo uv run generate.py "${crew_name}"
uv run generate.py "${crew_name}"
