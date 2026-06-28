#!/usr/bin/env python3
"""Rebuild okf/_graph/{nodes,edges}.json from OKF node frontmatter. Cache only — safe to delete and regenerate."""
import json
import re
import sys
from pathlib import Path

NODE_TYPES = ["context", "requirements", "decisions", "actions", "solution"]
LINK_RELATIONS = ["derives_from", "impacts", "supports", "blocks"]


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        raise ValueError("missing YAML frontmatter")
    try:
        import yaml
        return yaml.safe_load(m.group(1)) or {}
    except ImportError:
        return _parse_simple_yaml(m.group(1))


def _parse_simple_yaml(block: str) -> dict:
    """Minimal fallback parser for the fixed okf_node.md schema if PyYAML is unavailable."""
    data: dict = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        key_match = re.match(r"^(\w+):\s*(.*)$", line)
        if not key_match:
            i += 1
            continue
        key, val = key_match.group(1), key_match.group(2).strip()
        if val.startswith("#"):
            val = ""
        if val == "" or val == "[]":
            sub_items = []
            j = i + 1
            if val == "[]":
                data[key] = []
                i += 1
                continue
            while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                sub_items.append(re.sub(r"^\s+-\s+", "", lines[j]).strip())
                j += 1
            if sub_items:
                data[key] = sub_items
                i = j
                continue
            nested, j = _parse_nested_block(lines, i + 1)
            data[key] = nested
            i = j
            continue
        data[key] = val.strip('"')
        i += 1
    return data


def _parse_nested_block(lines, start):
    nested = {}
    i = start
    base_indent = None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        if base_indent is None:
            base_indent = indent
        if indent < base_indent:
            break
        key_match = re.match(r"^\s+(\w+):\s*(\[\])?\s*$", line)
        if not key_match:
            break
        key = key_match.group(1)
        if key_match.group(2) == "[]":
            nested[key] = []
            i += 1
            continue
        items = []
        j = i + 1
        while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
            items.append(re.sub(r"^\s+-\s+", "", lines[j]).strip())
            j += 1
        nested[key] = items
        i = j
    return nested, i


def main():
    if len(sys.argv) < 2:
        print("usage: build_graph.py <opportunity_id>", file=sys.stderr)
        sys.exit(1)

    opp_id = sys.argv[1]
    repo_root = Path(__file__).resolve().parents[1]
    opp_dir = repo_root / "opportunities" / opp_id
    if not opp_dir.is_dir():
        print(f"no such opportunity: {opp_dir}", file=sys.stderr)
        sys.exit(1)

    nodes = []
    edges = []
    errors = []

    for type_dir in NODE_TYPES:
        d = opp_dir / "okf" / type_dir
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                meta = parse_frontmatter(f.read_text())
            except ValueError as e:
                errors.append(f"{f}: {e}")
                continue
            node_id = meta.get("id")
            if not node_id:
                errors.append(f"{f}: missing id")
                continue
            nodes.append({
                "id": node_id,
                "type": meta.get("type"),
                "title": meta.get("title"),
                "status": meta.get("status"),
                "source": meta.get("source") or [],
                "file": str(f.relative_to(opp_dir)),
            })
            links = meta.get("links") or {}
            for relation in LINK_RELATIONS:
                for target in links.get(relation) or []:
                    edges.append({"from": node_id, "to": target, "relation": relation})

    graph_dir = opp_dir / "okf" / "_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "nodes.json").write_text(json.dumps(nodes, indent=2))
    (graph_dir / "edges.json").write_text(json.dumps(edges, indent=2))

    print(f"nodes: {len(nodes)}  edges: {len(edges)}")
    if errors:
        print("errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
