#!/usr/bin/env python3
"""Skeleton of a script turning machine-readable data into a Numbat graph file.

Copy it next to the data, fill the three TODO sections, then:

    python generate_graph.py <input> -o graph.json
    numbat validate graph.json
    numbat load graph.json -o out

It builds the graph with the dataclasses of `numbat.model`, which mirror the JSON
format (`numbat guide`), and always saves the JSON so it can be reviewed and
validated. Fix issues reported by `numbat validate` here, not in the output.
"""

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from numbat.model import (  # noqa: F401  (some are only used once uncommented)
    AttachedFile,
    Command,
    Edge,
    Graph,
    Node,
    NodeColor,
    NodeTypeDisplay,
)
from numbat.types import ComponentAccessType, EdgeType, NodeType  # noqa: F401

# --------------------------------------------------------------------------- #
# TODO 1: the mapping table designed before writing code                      #
# --------------------------------------------------------------------------- #

# Qualified name separator: "::", ".", "/" or "@"
DELIMITER = "::"

# Labels of every node kind used (one kind per domain category)
NODE_TYPES: dict[NodeType, NodeTypeDisplay] = {
    # NodeType.NODE_NAMESPACE: NodeTypeDisplay(graph_display="...", hover_display="..."),
}

# Domain category -> node kind
KIND_OF: dict[str, NodeType] = {
    # "category": NodeType.NODE_CLASS,
}

# Domain relation -> edge kind
EDGE_OF: dict[str, EdgeType] = {
    # "relation": EdgeType.CALL,
}


# --------------------------------------------------------------------------- #
# Intermediate records: read_source() fills them from the input               #
# --------------------------------------------------------------------------- #


@dataclass
class Entity:
    key: str  # unique and stable, derived from the data; becomes the node id
    name: str  # displayed name; must be unique among the entity's siblings
    category: str  # key of KIND_OF
    parent: str | None = None  # key of the containing entity (one container at most)
    hover: str = ""  # metadata and volatile values (never in the name)
    extra: dict = field(default_factory=dict)  # anything make_node() needs


@dataclass
class Relation:
    source: str  # entity key
    target: str  # entity key
    type: str  # key of EDGE_OF
    hover: str = ""


# --------------------------------------------------------------------------- #
# TODO 2: parse the input                                                     #
# --------------------------------------------------------------------------- #


def read_source(path: Path) -> tuple[list[Entity], list[Relation]]:
    """Parse the input into entities and relations."""
    entities: list[Entity] = []
    relations: list[Relation] = []
    # TODO: fill entities and relations from `path`
    return entities, relations


# --------------------------------------------------------------------------- #
# TODO 3: per-node features                                                   #
# --------------------------------------------------------------------------- #


def make_node(entity: Entity) -> Node:
    """Create the node of an entity, with its interactive features."""
    return Node(
        id=entity.key,
        kind=KIND_OF.get(entity.category, NodeType.NODE_SYMBOL),
        name=entity.name,
        hover=entity.hover,
        # prefix="", postfix="",                 # decoration around the name
        # indexed=False,                         # referenced but not described
        # access=ComponentAccessType.PUBLIC,     # section inside class/struct boxes
        # color=NodeColor(fill="#RRGGBB"),       # encode one dimension consistently
        # command=Command(argv=["program", "/absolute/path"], description="..."),
        # attached_file=AttachedFile(content="..."),  # or path= relative to graph.json
    )


# --------------------------------------------------------------------------- #
# Generic assembly: usually no change needed below                            #
# --------------------------------------------------------------------------- #


def build_nodes(entities: list[Entity]) -> list[Node]:
    """Create the nodes and nest each one in its parent; return the top-level ones."""
    nodes = {e.key: make_node(e) for e in entities}
    roots: list[Node] = []
    for entity in entities:
        if entity.parent is None:
            roots.append(nodes[entity.key])
        elif entity.parent in nodes:
            nodes[entity.parent].children.append(nodes[entity.key])
        else:
            raise KeyError(f"entity {entity.key!r}: unknown parent {entity.parent!r}")
    for node in nodes.values():  # deterministic output
        node.children.sort(key=lambda n: n.name)
    return sorted(roots, key=lambda n: n.name)


def build_edges(relations: list[Relation]) -> list[Edge]:
    """Create one edge per (source, target, kind), aggregating repeated relations."""
    grouped: dict[tuple[str, str, EdgeType], list[Relation]] = {}
    for rel in relations:
        kind = EDGE_OF.get(rel.type, EdgeType.USAGE)
        grouped.setdefault((rel.source, rel.target, kind), []).append(rel)
    edges = []
    for (source, target, kind), rels in grouped.items():
        hovers = sorted({r.hover for r in rels if r.hover})
        hover = "; ".join(hovers)
        if len(rels) > 1:
            hover = f"{len(rels)} occurrences" + (f" - {hover}" if hover else "")
        edges.append(Edge(kind=kind, source=source, target=target, hover=hover))
    return edges


def build_graph(entities: list[Entity], relations: list[Relation]) -> Graph:
    return Graph(
        delimiter=DELIMITER,
        node_types=NODE_TYPES,
        nodes=build_nodes(entities),
        edges=build_edges(relations),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="source data")
    parser.add_argument("-o", "--output", type=Path, default=Path("graph.json"))
    args = parser.parse_args()

    graph = build_graph(*read_source(args.input))
    graph.save(args.output)
    print(f"wrote {args.output}, now run: numbat validate {args.output}")


if __name__ == "__main__":
    main()
