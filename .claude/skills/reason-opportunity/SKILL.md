---
name: reason-opportunity
description: Perform multi-hop reasoning over an opportunity's OKF knowledge graph to answer a question (e.g. risks, missing requirements, contradictions, dependencies) and write a reasoning report. Use when the user wants insight or analysis across an opportunity's accumulated knowledge, not just a single node.
---

# reason-opportunity

Args: `<opportunity_id> "<question>"`

## Process

1. Ensure the graph cache is fresh: run `python3 scripts/build_graph.py <opportunity_id>` (repo root) and read the resulting `okf/_graph/nodes.json` and `okf/_graph/edges.json`.
2. Read the full content (not just frontmatter) of every node referenced by the question's topic, plus anything reachable from them by 1-2 hops along `derives_from` / `impacts` / `supports` / `blocks` edges. For a broad question ("what are the risks"), read all nodes.
3. Reason over the graph to answer the question. Specifically look for:
   - **risks** — requirements with no supporting solution node, decisions that block other decisions, unresolved actions tied to confirmed requirements
   - **missing requirements** — context nodes with no requirement derived from them where one would be expected
   - **contradictions** — two decisions/requirements that conflict, or a `superseded` node still linked as if active
   - **dependencies** — chains of `impacts`/`blocks` edges that gate solution nodes
4. Write `opportunities/{opportunity_id}/output/reasoning/{slug-of-question}-{YYYY-MM-DD}.md` containing:
   - The question
   - Direct answer (a few sentences)
   - Supporting evidence, citing node IDs (e.g. `REQ-003`, `DEC-002`) and the file each came from
   - Any risks/contradictions/gaps found, even if not directly asked, if material
5. Do not modify any OKF node — this skill only reads and reports.
6. Print the report's file path and a short summary in the response.
