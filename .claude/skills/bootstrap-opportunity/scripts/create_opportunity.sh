#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: create_opportunity.sh <opportunity_id> <opportunity_name>" >&2
  exit 1
fi

OPP_ID="$1"
OPP_NAME="$2"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OPP_DIR="$REPO_ROOT/opportunities/$OPP_ID"

if [ -d "$OPP_DIR" ]; then
  echo "Opportunity already exists: $OPP_DIR" >&2
  exit 1
fi

mkdir -p \
  "$OPP_DIR/input/meetings" \
  "$OPP_DIR/input/rfp" \
  "$OPP_DIR/input/notes" \
  "$OPP_DIR/input/references" \
  "$OPP_DIR/okf/context" \
  "$OPP_DIR/okf/requirements" \
  "$OPP_DIR/okf/decisions" \
  "$OPP_DIR/okf/actions" \
  "$OPP_DIR/okf/solution" \
  "$OPP_DIR/okf/_graph" \
  "$OPP_DIR/output/proposal" \
  "$OPP_DIR/output/reasoning" \
  "$OPP_DIR/output/salesforce"

cat > "$OPP_DIR/meta.yaml" <<EOF
id: $OPP_ID
name: "$OPP_NAME"
created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF

# keep empty dirs tracked by git
find "$OPP_DIR" -type d -empty -exec touch {}/.gitkeep \;

echo "Created opportunity workspace: $OPP_DIR"
