#!/usr/bin/env bash
# Fetch the official Discord OpenAPI spec into specs/openapi.json.
#
# Downloads to a temporary file first, validates it is a parseable OpenAPI
# document, and only then replaces specs/openapi.json.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC_DIR="${REPO_ROOT}/specs"
SPEC_FILE="${SPEC_DIR}/openapi.json"
SPEC_URL="https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json"

mkdir -p "${SPEC_DIR}"
curl -fsSL "${SPEC_URL}" -o "${SPEC_FILE}.new"

python3 - "${SPEC_FILE}.new" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    spec = json.load(fh)

if "paths" not in spec or "info" not in spec:
    raise SystemExit(f"{path} is not a valid OpenAPI document")

print(
    f"valid OpenAPI {spec.get('openapi')} document "
    f"(info.version={spec['info'].get('version')}, paths={len(spec['paths'])})"
)
PY

mv "${SPEC_FILE}.new" "${SPEC_FILE}"
echo "spec updated: ${SPEC_FILE}"
