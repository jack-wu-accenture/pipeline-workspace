---
name: rebuild-okf-graph
description: Regenerate the derived graph cache (okf/_graph/) for an opportunity from the links declared in its OKF node frontmatter. Run after bulk ingestion or manual node edits, or whenever the graph cache looks stale.
---

# rebuild-okf-graph

Args: `<opportunity_id>`

The graph is a derived cache, never hand-edited.

1. Run `python3 scripts/build_graph.py <opportunity_id>` from the repo root.
2. The script reads every node under `okf/{context,requirements,decisions,actions,solution}/`, parses its YAML frontmatter, and writes:
   - `okf/_graph/nodes.json` — all nodes with id/type/title/status/source
   - `okf/_graph/edges.json` — one edge per link (derives_from/impacts/supports/blocks), each `{from, to, relation}`
3. If the script reports parse errors (bad frontmatter), fix the offending node file's YAML and re-run rather than ignoring the error.
4. Report the node/edge counts.
