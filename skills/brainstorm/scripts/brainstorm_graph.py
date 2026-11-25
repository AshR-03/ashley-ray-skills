#!/usr/bin/env python3
"""Keep a brainstorm knowledge graph in a JSON file.

The graph is directed and may contain cycles. Nodes are ideas the product
owner has given (purpose, users, goals, features...). Edges say how two
ideas relate ("feature serves stakeholder"). A node with open questions is
still to be explored.

The brainstorm is done when `check` passes:
  1. no node has open questions,
  2. no node is isolated (every node has at least one edge),
  3. every node is connected to the seed idea (one connected graph),
  4. the core node types are covered, plus milestones for long-term projects.

Standard library only. Run with --help on any command for details.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_GRAPH = "docs/brainstorm/graph.json"
SEED_ID = "idea"

NODE_TYPES = {
    "idea": "The seed: the project idea in the owner's words",
    "purpose": "Why the project exists: business, research or personal",
    "stakeholder": "Someone who uses, pays for, or is affected by the product",
    "goal": "An outcome someone wants from the project",
    "vision": "How the owner pictures the product or an experience in it",
    "feature": "A capability the product has",
    "constraint": "A fixed limit: time, budget, skills, platform, policy",
    "risk": "Something that could stop the project or a goal",
    "milestone": "A step on the roadmap",
    "measure": "How success of a goal is judged",
    "assumption": "Something taken as true without the owner confirming it",
}

EDGE_TYPES = {
    "motivates": "purpose/goal -> goal/feature: gives the reason for",
    "serves": "feature/vision -> stakeholder: is used by or helps",
    "achieves": "feature/milestone -> goal: moves the goal forward",
    "requires": "A needs B to exist or work",
    "part-of": "A is a piece of B",
    "refines": "vision/feature -> feature/idea: describes in more detail",
    "precedes": "milestone -> milestone: comes before on the roadmap",
    "delivers": "milestone -> feature: ships",
    "constrains": "constraint -> anything: limits",
    "threatens": "risk -> anything: could stop or harm",
    "mitigates": "feature/decision -> risk: reduces",
    "measures": "measure -> goal: judges success of",
    "conflicts-with": "A pulls against B; needs a trade-off",
    "relates-to": "Fallback when no other type fits; prefer a specific type",
}

CORE_TYPES = ["purpose", "stakeholder", "goal", "vision", "feature"]
HORIZONS = ["short", "long", "unknown"]


# --------------------------------------------------------------------------- io

def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"No graph at {path}. Run `init` first.")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save(path: Path, graph: dict) -> None:
    graph["updated"] = now()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp.replace(path)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "node"


def node_or_die(graph: dict, node_id: str) -> dict:
    node = graph["nodes"].get(node_id)
    if node is None:
        known = ", ".join(sorted(graph["nodes"])) or "none"
        sys.exit(f"Unknown node '{node_id}'. Known nodes: {known}")
    return node


# ------------------------------------------------------------------- analysis

def degrees(graph: dict) -> dict[str, int]:
    deg = {n: 0 for n in graph["nodes"]}
    for e in graph["edges"]:
        deg[e["from"]] += 1
        deg[e["to"]] += 1
    return deg


def components(graph: dict) -> list[set[str]]:
    """Weakly connected components (edge direction ignored)."""
    adj: dict[str, set[str]] = defaultdict(set)
    for e in graph["edges"]:
        adj[e["from"]].add(e["to"])
        adj[e["to"]].add(e["from"])
    seen: set[str] = set()
    comps = []
    for start in graph["nodes"]:
        if start in seen:
            continue
        comp, queue = set(), deque([start])
        seen.add(start)
        while queue:
            cur = queue.popleft()
            comp.add(cur)
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        comps.append(comp)
    return comps


def evaluate(graph: dict) -> dict:
    nodes = graph["nodes"]
    deg = degrees(graph)
    comps = components(graph)
    main = next((c for c in comps if SEED_ID in c), set())

    open_questions = [
        (nid, q) for nid, n in nodes.items() for q in n.get("open_questions", [])
    ]
    isolated = [nid for nid, d in deg.items() if d == 0]
    detached = [sorted(c) for c in comps if c is not main and len(c) > 1]

    present = {n["type"] for n in nodes.values()}
    missing = [t for t in CORE_TYPES if t not in present]
    horizon = graph.get("horizon", "unknown")
    if horizon == "unknown":
        missing.append("horizon (ask whether this is short- or long-term)")
    elif horizon == "long" and "milestone" not in present:
        missing.append("milestone (long-term project needs a roadmap)")

    done = not open_questions and not isolated and not detached and not missing
    return {
        "done": done,
        "nodes": len(nodes),
        "edges": len(graph["edges"]),
        "components": len(comps),
        "open_questions": open_questions,
        "isolated": isolated,
        "detached_components": detached,
        "missing_coverage": missing,
        "horizon": horizon,
    }


# ------------------------------------------------------------------- commands

def cmd_init(args) -> None:
    path = Path(args.graph)
    if path.exists() and not args.force:
        sys.exit(f"{path} already exists. Use --force to start over, or keep adding to it.")
    graph = {
        "title": args.title,
        "horizon": args.horizon,
        "created": now(),
        "updated": now(),
        "nodes": {
            SEED_ID: {
                "type": "idea",
                "label": args.idea,
                "detail": "",
                "status": "explored",
                "open_questions": [],
            }
        },
        "edges": [],
        "log": [],
    }
    save(path, graph)
    print(f"Created {path} with seed node '{SEED_ID}'.")


def cmd_add_node(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    node_id = args.id or slug(f"{args.type}-{args.label}")
    if node_id in graph["nodes"]:
        sys.exit(f"Node '{node_id}' already exists. Use update-node to change it.")
    graph["nodes"][node_id] = {
        "type": args.type,
        "label": args.label,
        "detail": args.detail or "",
        "status": "parked" if args.parked else "explored",
        "open_questions": list(args.question or []),
    }
    save(path, graph)
    print(f"Added {args.type} '{node_id}'. Connect it with add-edge.")


def cmd_update_node(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    node = node_or_die(graph, args.id)
    for field in ("type", "label", "detail"):
        value = getattr(args, field)
        if value is not None:
            node[field] = value
    if args.parked is not None:
        node["status"] = "parked" if args.parked else "explored"
    save(path, graph)
    print(f"Updated '{args.id}'.")


def cmd_remove_node(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    if args.id == SEED_ID:
        sys.exit("The seed idea cannot be removed; update it instead.")
    node_or_die(graph, args.id)
    del graph["nodes"][args.id]
    before = len(graph["edges"])
    graph["edges"] = [e for e in graph["edges"] if args.id not in (e["from"], e["to"])]
    save(path, graph)
    print(f"Removed '{args.id}' and {before - len(graph['edges'])} edge(s).")


def cmd_add_question(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    node_or_die(graph, args.id)["open_questions"].append(args.question)
    save(path, graph)
    print(f"Added open question to '{args.id}'.")


def cmd_close_question(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    node = node_or_die(graph, args.id)
    qs = node["open_questions"]
    if args.all:
        closed, node["open_questions"] = qs, []
    else:
        if not 1 <= args.index <= len(qs):
            sys.exit(f"'{args.id}' has {len(qs)} open question(s); index must be 1..{len(qs)}.")
        closed = [qs.pop(args.index - 1)]
    save(path, graph)
    print(f"Closed {len(closed)} question(s) on '{args.id}'.")


def cmd_add_edge(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    node_or_die(graph, args.source)
    node_or_die(graph, args.target)
    if args.source == args.target:
        sys.exit("An edge must join two different nodes.")
    for e in graph["edges"]:
        if (e["from"], e["to"], e["type"]) == (args.source, args.target, args.type):
            sys.exit("That edge already exists.")
    graph["edges"].append(
        {"from": args.source, "to": args.target, "type": args.type, "note": args.note or ""}
    )
    save(path, graph)
    print(f"{args.source} -[{args.type}]-> {args.target}")


def cmd_remove_edge(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    before = len(graph["edges"])
    graph["edges"] = [
        e for e in graph["edges"]
        if not (e["from"] == args.source and e["to"] == args.target
                and (args.type is None or e["type"] == args.type))
    ]
    save(path, graph)
    print(f"Removed {before - len(graph['edges'])} edge(s).")


def cmd_set(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    if args.horizon:
        graph["horizon"] = args.horizon
    if args.title:
        graph["title"] = args.title
    save(path, graph)
    print("Updated graph settings.")


def cmd_record(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    graph["log"].append(
        {"at": now(), "question": args.question, "answer": args.answer,
         "nodes": list(args.node or [])}
    )
    save(path, graph)
    print(f"Logged answer ({len(graph['log'])} so far).")


def cmd_show(args) -> None:
    graph = load(Path(args.graph))
    print(f"# {graph['title']}  (horizon: {graph.get('horizon', 'unknown')})")
    by_type = defaultdict(list)
    for nid, n in graph["nodes"].items():
        by_type[n["type"]].append((nid, n))
    for t in NODE_TYPES:
        for nid, n in by_type.get(t, []):
            flag = " [parked]" if n.get("status") == "parked" else ""
            print(f"{t:<11} {nid}: {n['label']}{flag}")
            for q in n.get("open_questions", []):
                print(f"{'':<11}   ? {q}")
    print("\nEdges:")
    for e in graph["edges"]:
        note = f"  ({e['note']})" if e.get("note") else ""
        print(f"  {e['from']} -[{e['type']}]-> {e['to']}{note}")


def cmd_check(args) -> None:
    graph = load(Path(args.graph))
    report = evaluate(graph)
    if args.json:
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["done"] else 1)

    print(f"Nodes: {report['nodes']}  Edges: {report['edges']}  "
          f"Components: {report['components']}  Horizon: {report['horizon']}")
    print(f"\nOpen questions ({len(report['open_questions'])}):")
    for nid, q in report["open_questions"]:
        print(f"  - {nid}: {q}")
    print(f"\nIsolated nodes ({len(report['isolated'])}):")
    for nid in report["isolated"]:
        print(f"  - {nid}: {graph['nodes'][nid]['label']}")
    print(f"\nGroups not linked to the seed idea ({len(report['detached_components'])}):")
    for comp in report["detached_components"]:
        print(f"  - {', '.join(comp)}")
    print(f"\nMissing coverage ({len(report['missing_coverage'])}):")
    for m in report["missing_coverage"]:
        print(f"  - {m}")
    print("\nDONE: definition of done met." if report["done"]
          else "\nNOT DONE: keep asking.")
    sys.exit(0 if report["done"] else 1)


def mermaid_label(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ")


def cmd_render(args) -> None:
    path = Path(args.graph)
    graph = load(path)
    out = Path(args.out) if args.out else path.with_name("BRAINSTORM.md")
    report = evaluate(graph)
    ids = {nid: f"n{i}" for i, nid in enumerate(graph["nodes"])}

    lines = [f"# {graph['title']}", ""]
    lines.append(f"- **Horizon:** {graph.get('horizon', 'unknown')}")
    lines.append(f"- **Status:** {'complete' if report['done'] else 'in progress'} "
                 f"({report['nodes']} ideas, {report['edges']} links)")
    lines.append(f"- **Updated:** {graph.get('updated', '')}")
    lines += ["", "## Idea graph", "", "```mermaid", "flowchart LR"]
    for nid, n in graph["nodes"].items():
        lines.append(f'  {ids[nid]}["{mermaid_label(n["type"])}: {mermaid_label(n["label"])}"]:::{n["type"]}')
    for e in graph["edges"]:
        lines.append(f"  {ids[e['from']]} -->|{e['type']}| {ids[e['to']]}")
    palette = {
        "idea": "#f6c343", "purpose": "#e8a87c", "stakeholder": "#85c1e9",
        "goal": "#82e0aa", "vision": "#c39bd3", "feature": "#76d7c4",
        "constraint": "#d5d8dc", "risk": "#f1948a", "milestone": "#f8c471",
        "measure": "#aed6f1", "assumption": "#fadbd8",
    }
    for t, colour in palette.items():
        lines.append(f"  classDef {t} fill:{colour},stroke:#333,color:#111")
    lines += ["```", ""]

    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    for e in graph["edges"]:
        outgoing[e["from"]].append(e)
        incoming[e["to"]].append(e)

    titles = {
        "idea": "Idea", "purpose": "Purpose", "stakeholder": "Stakeholders",
        "goal": "Goals", "vision": "Product vision", "feature": "Features",
        "constraint": "Constraints", "risk": "Risks", "milestone": "Roadmap",
        "measure": "Success measures", "assumption": "Assumptions",
    }
    for t in NODE_TYPES:
        members = [(nid, n) for nid, n in graph["nodes"].items() if n["type"] == t]
        if not members:
            continue
        lines += [f"## {titles[t]}", ""]
        for nid, n in members:
            parked = " *(parked: out of scope for now)*" if n.get("status") == "parked" else ""
            lines.append(f"### {n['label']}{parked}")
            if n.get("detail"):
                lines += ["", n["detail"]]
            links = [f"{e['type']} → {graph['nodes'][e['to']]['label']}" for e in outgoing[nid]]
            links += [f"← {e['type']} {graph['nodes'][e['from']]['label']}" for e in incoming[nid]]
            if links:
                lines += ["", "Links: " + "; ".join(links)]
            for q in n.get("open_questions", []):
                lines.append(f"- Open question: {q}")
            lines.append("")

    if graph.get("log"):
        lines += ["## Question log", ""]
        for i, entry in enumerate(graph["log"], 1):
            lines.append(f"{i}. **Q:** {entry['question']}  ")
            lines.append(f"   **A:** {entry['answer']}")
        lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


# ------------------------------------------------------------------------ cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--graph", default=DEFAULT_GRAPH,
                   help=f"Path to graph.json (default: {DEFAULT_GRAPH})")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Start a graph with the seed idea")
    s.add_argument("--title", required=True)
    s.add_argument("--idea", required=True, help="The idea in the owner's words")
    s.add_argument("--horizon", choices=HORIZONS, default="unknown")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("add-node", help="Add an idea to the graph")
    s.add_argument("--id", help="Short kebab-case id (generated if omitted)")
    s.add_argument("--type", required=True, choices=sorted(NODE_TYPES))
    s.add_argument("--label", required=True)
    s.add_argument("--detail")
    s.add_argument("--question", action="append", help="Open question (repeatable)")
    s.add_argument("--parked", action="store_true", help="Out of scope for now")
    s.set_defaults(func=cmd_add_node)

    s = sub.add_parser("update-node", help="Change a node's fields")
    s.add_argument("--id", required=True)
    s.add_argument("--type", choices=sorted(NODE_TYPES))
    s.add_argument("--label")
    s.add_argument("--detail")
    s.add_argument("--parked", type=lambda v: v.lower() in ("1", "true", "yes"),
                   help="true or false")
    s.set_defaults(func=cmd_update_node)

    s = sub.add_parser("remove-node", help="Delete a node and its edges")
    s.add_argument("--id", required=True)
    s.set_defaults(func=cmd_remove_node)

    s = sub.add_parser("add-question", help="Add an open question to a node")
    s.add_argument("--id", required=True)
    s.add_argument("--question", required=True)
    s.set_defaults(func=cmd_add_question)

    s = sub.add_parser("close-question", help="Mark a node's open question answered")
    s.add_argument("--id", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--index", type=int, help="1-based, as listed by check")
    g.add_argument("--all", action="store_true")
    s.set_defaults(func=cmd_close_question)

    s = sub.add_parser("add-edge", help="Link two nodes (directed)")
    s.add_argument("--from", dest="source", required=True)
    s.add_argument("--to", dest="target", required=True)
    s.add_argument("--type", required=True, choices=sorted(EDGE_TYPES))
    s.add_argument("--note")
    s.set_defaults(func=cmd_add_edge)

    s = sub.add_parser("remove-edge", help="Delete edges between two nodes")
    s.add_argument("--from", dest="source", required=True)
    s.add_argument("--to", dest="target", required=True)
    s.add_argument("--type", choices=sorted(EDGE_TYPES))
    s.set_defaults(func=cmd_remove_edge)

    s = sub.add_parser("set", help="Change graph settings")
    s.add_argument("--horizon", choices=HORIZONS)
    s.add_argument("--title")
    s.set_defaults(func=cmd_set)

    s = sub.add_parser("record", help="Log a question and the owner's answer")
    s.add_argument("--question", required=True)
    s.add_argument("--answer", required=True)
    s.add_argument("--node", action="append", help="Node id the answer touched (repeatable)")
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("show", help="Print every node and edge")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("check", help="Test the definition of done (exit 0 when done)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("render", help="Write BRAINSTORM.md with a Mermaid diagram")
    s.add_argument("--out", help="Output path (default: BRAINSTORM.md next to the graph)")
    s.set_defaults(func=cmd_render)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
