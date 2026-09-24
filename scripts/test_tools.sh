#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== 1. Danbooru Tag Search Test ==="
python3 tools/images/search_tag.py "smile" "katana"

echo -e "\n=== 2. Scene Composer Demo Test ==="
python3 tools/images/compose_scene.py --demo

echo -e "\n=== 3. Crop Backgrounds Unit Tests ==="
python3 -m unittest discover -s tools/images/tests -v

echo -e "\n=== 4. Checker Unit Tests ==="
python3 -m unittest discover -s scripts/checks/tests -v

echo -e "\n=== All Tool Tests Passed Successfully ==="
