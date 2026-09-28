import json
import sqlite3
from pathlib import Path

import pytest

from numbat import SourcetrailDB
from numbat.cli import main
from numbat.db import EdgeDAO, NodeDAO
from numbat.loader import load_graph, validate
from numbat.model import SCHEMA_URL, Graph, GraphValidationError, json_schema
from numbat.types import EdgeType, NodeType

EXAMPLE = Path(__file__).parents[2] / "examples" / "graph.json"


def issues_of(data: dict) -> list[str]:
    """Return all the issues (structural and semantic) of a graph document."""
    try:
        graph = Graph.from_dict(data)
    except GraphValidationError as e:
        return [str(i) for i in e.issues]
    return [str(i) for i in validate(graph)]


def query(db_path: Path, sql: str) -> list[tuple]:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(sql).fetchall()


# ------------------------------------------------------------------------ #
# Model                                                                    #
# ------------------------------------------------------------------------ #


def test_example_roundtrip():
    graph = Graph.load(EXAMPLE)
    assert Graph.from_dict(graph.to_dict()) == graph
    assert graph.nodes[0].kind == NodeType.NODE_CLASS
    assert graph.edges[0].kind == EdgeType.USAGE
    assert graph.node_types[NodeType.NODE_FILE].hover_display == "python file"


def test_schema_reference_is_accepted():
    assert issues_of({"$schema": SCHEMA_URL, "nodes": [{"name": "a"}]}) == []


def test_iter_nodes_parents_first():
    graph = Graph.from_dict(
        {"nodes": [{"name": "a", "children": [{"name": "b", "children": [{"name": "c"}]}]},
                   {"name": "d"}]}
    )
    assert [p for _, _, p in graph.iter_nodes()] == [
        "nodes[0]", "nodes[0].children[0]", "nodes[0].children[0].children[0]", "nodes[1]"
    ]


def test_structural_errors_are_all_reported():
    issues = issues_of(
        {
            "nodes": [{"name": "x", "kidn": "class", "kind": "klass",
                       "color": {"fill": "darkpurple"}, "children": [{"access": 1}]}],
            "edges": [{"source": "x"}],
            "delimiter": "->",
        }
    )
    assert issues == [
        "error: delimiter: invalid value '->', expected one of: /, ::, ., @",
        "error: nodes[0]: unknown field 'kidn' (did you mean 'kind'?)",
        "error: nodes[0].kind: invalid value 'klass' (did you mean 'class'?), expected "
        "one of: symbol, type, builtin_type, module, namespace, package, struct, class, "
        "interface, annotation, global_variable, field, function, method, enum, "
        "enum_constant, typedef, type_parameter, macro, union",
        "error: nodes[0].color.fill: invalid color 'darkpurple', expected '#RRGGBB' or "
        "an SVG color keyword",
        "error: nodes[0].children[0]: missing required field 'name'",
        "error: nodes[0].children[0].access: expected a string, got int",
        "error: edges[0]: missing required field 'kind'",
    ]


def test_file_kind_not_allowed_for_nodes():
    assert "invalid value 'file'" in issues_of({"nodes": [{"name": "a", "kind": "file"}]})[0]


def test_invalid_json():
    with pytest.raises(GraphValidationError, match="invalid JSON"):
        Graph.from_json("{")


def test_json_schema():
    schema = json_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == SCHEMA_URL
    assert "$schema" in schema["properties"]
    assert schema["required"] == []
    assert schema["additionalProperties"] is False
    node = schema["$defs"]["Node"]
    assert node["required"] == ["name"]
    assert "class" in node["properties"]["kind"]["enum"]
    assert "file" not in node["properties"]["kind"]["enum"]
    assert node["properties"]["children"]["items"] == {"$ref": "#/$defs/Node"}
    assert node["properties"]["kind"]["default"] == "symbol"
    assert "file" in schema["properties"]["node_types"]["propertyNames"]["enum"]
    json.dumps(schema)  # serializable


# ------------------------------------------------------------------------ #
# Semantic validation                                                      #
# ------------------------------------------------------------------------ #


def test_example_is_valid():
    assert validate(Graph.load(EXAMPLE), EXAMPLE.parent) == []


def test_semantic_errors():
    issues = issues_of(
        {
            "files": [{"id": "f", "name": "f.txt", "content": "a", "path": "nope.txt"},
                      {"id": "g"}],
            "nodes": [
                {"id": "a", "name": "A", "children": [
                    {"id": "b", "name": "B", "delimiter": "."},
                    {"name": "B"},
                ]},
                {"id": "a", "name": "C", "attached_file": {},
                 "locations": [{"file": "b", "start_line": 3, "start_column": 1,
                                "end_line": 2, "end_column": 1}]},
            ],
            "edges": [
                {"kind": "usage", "source": "a", "target": "bb"},
                {"kind": "usage", "source": "a"},
                {"kind": "call", "source": "a", "target": "b", "unsolved": True},
                {"kind": "member", "source": "a", "target": "b"},
            ],
        }
    )
    assert issues == [
        "error: files[0]: 'path' and 'content' are mutually exclusive",
        "error: files[0].path: file not found: nope.txt",
        "error: files[1]: 'name' is required when 'path' is not given",
        "error: nodes[0].children[0].delimiter: only allowed on top-level nodes, "
        "children use the delimiter of their top-level ancestor",
        "error: nodes[0].children[1]: same qualified name (delimiter, prefix, name, "
        "postfix of the node and its ancestors) as nodes[0].children[0], both would be "
        "merged into a single node",
        "error: nodes[1].id: duplicate id 'a' (already used by nodes[0])",
        "error: nodes[1].attached_file: exactly one of 'path' or 'content' is required",
        "error: nodes[1].locations[0].file: unknown file id 'b' (it is not a file id)",
        "error: nodes[1].locations[0]: the range ends before it starts",
        "error: edges[0].target: unknown id 'bb' (did you mean 'b'?)",
        "error: edges[1]: missing 'target' (or set 'unsolved' to true)",
        "error: edges[2].target: must be omitted when 'unsolved' is true",
        "error: edges[2].locations: unsolved edges require exactly one location",
        "warning: edges[3]: redundant member edge, nesting already creates it",
    ]


def test_same_name_different_postfix_is_valid():
    assert issues_of({"nodes": [{"name": "f", "postfix": "(int)"},
                                {"name": "f", "postfix": "(char)"}]}) == []


def test_same_name_different_delimiter_is_valid():
    assert issues_of({"nodes": [{"name": "f"}, {"name": "f", "delimiter": "."}]}) == []


# ------------------------------------------------------------------------ #
# Loading                                                                  #
# ------------------------------------------------------------------------ #


def test_load_example(tmp_path, monkeypatch):
    # Run from another directory than the database one (sideloaded files)
    monkeypatch.chdir(EXAMPLE.parent)
    db = SourcetrailDB.create(tmp_path / "db")
    ids = load_graph(Graph.load(EXAMPLE), db, EXAMPLE.parent)
    db.commit()
    db.close()
    path = tmp_path / "db.srctrldb"

    assert query(path, f"SELECT type, color FROM node WHERE id = {ids['MyType.my_method']}") == [
        (NodeType.NODE_METHOD.value, "lightgreen default default default default")
    ]
    assert query(path, f"SELECT id FROM symbol WHERE id = {ids['object']}") == []
    assert query(path, "SELECT graph_display, hover_display FROM node_type WHERE id = 128") == [
        ("Classes", "python class")
    ]
    edges = query(path, "SELECT type, source_node_id, target_node_id, color, hover_display FROM edge")
    assert (EdgeType.USAGE.value, ids["MyType.my_method"], ids["MyType.my_member"],
            "green", "reads the member") in edges
    assert (EdgeType.MEMBER.value, ids["MyType"], ids["MyType.my_member"], None, "") in edges
    assert len(query(path, "SELECT * FROM element_component")) == 1  # ambiguous
    assert len(query(path, "SELECT * FROM source_location WHERE type = 9")) == 1  # unsolved
    assert query(path, "SELECT name FROM local_symbol") == [("my_method.self",)]
    assert query(path, "SELECT message FROM error") == [("missing type annotations",)]
    assert query(path, "SELECT path, language, line_count FROM file") == [
        ("file.py", "python", 7)
    ]
    (file_name,) = query(path, "SELECT file_name FROM node_file")[0]
    assert (tmp_path / file_name).read_text() == "Documentation of MyType\n"


def test_load_invalid_graph_records_nothing(tmp_path):
    db = SourcetrailDB.create(tmp_path / "db")
    graph = Graph.from_dict({"nodes": [{"name": "a"}], "edges": [
        {"kind": "call", "source": "a", "target": "b"}]})
    with pytest.raises(GraphValidationError):
        load_graph(graph, db)
    assert NodeDAO.list(db.database) == []
    db.close()


def test_load_file_from_path(tmp_path):
    (tmp_path / "data.txt").write_text("line 1\nline 2\n")
    db = SourcetrailDB.create(tmp_path / "db")
    graph = Graph.from_dict({"files": [{"id": "d", "path": "data.txt"}],
                             "nodes": [{"name": "n", "attached_file": {"path": "data.txt"}}]})
    ids = load_graph(graph, db, tmp_path)
    db.commit()
    db.close()
    assert query(tmp_path / "db.srctrldb", f"SELECT path, line_count FROM file WHERE id = {ids['d']}") == [
        ("data.txt", 2)
    ]


# ------------------------------------------------------------------------ #
# CLI                                                                      #
# ------------------------------------------------------------------------ #


def test_cli_load(tmp_path, capsys):
    out = tmp_path / "out"
    assert main(["load", str(EXAMPLE), "-o", str(out)]) == 0
    assert (tmp_path / "out.srctrldb").exists()
    assert (tmp_path / "out.srctrlprj").exists()
    # Refuse to overwrite without --force
    assert main(["load", str(EXAMPLE), "-o", str(out)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert main(["load", str(EXAMPLE), "-o", str(out), "--force"]) == 0
    assert len(query(tmp_path / "out.srctrldb", "SELECT * FROM file")) == 1


def test_cli_validate_json(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"nodes": [{"name": "a", "kind": "klass"}]}))
    assert main(["validate", "--json", str(bad)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is False
    assert result["issues"][0]["path"] == "nodes[0].kind"
    assert main(["validate", str(EXAMPLE)]) == 0


def test_cli_load_invalid_creates_nothing(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}}")
    assert main(["load", str(bad), "-o", str(tmp_path / "out")]) == 1
    assert not (tmp_path / "out.srctrldb").exists()


def test_cli_schema_and_guide(tmp_path, capsys):
    assert main(["schema", "-o", str(tmp_path / "schema.json")]) == 0
    assert json.loads((tmp_path / "schema.json").read_text()) == json_schema()
    assert main(["guide"]) == 0
    assert "# Numbat graph format" in capsys.readouterr().out


# ------------------------------------------------------------------------ #
# API fixes                                                                #
# ------------------------------------------------------------------------ #


def test_node_and_edge_listing(tmp_path):
    db = SourcetrailDB.create(tmp_path / "db")
    a = db.record_class(name="A", hover_display="class A")
    b = db.record_field(name="b", parent_id=a)
    ref = db.record_ref_usage(b, a, hover_display="uses")
    node = NodeDAO.get(db.database, a)
    assert NodeDAO.get_by_name(db.database, node.name).hover_display == "class A"
    assert {n.id for n in NodeDAO.list(db.database)} == {a, b}
    assert [e.hover_display for e in EdgeDAO.list(db.database) if e.id == ref] == ["uses"]
    db.close()


def test_reopen_does_not_duplicate_nodes(tmp_path):
    db = SourcetrailDB.create(tmp_path / "db")
    a = db.record_class(name="A")
    db.commit()
    db.close()
    db = SourcetrailDB.open(tmp_path / "db")
    assert db.record_class(name="A") == a
    db.clear()
    # The cache is reset by clear: the node is really inserted again
    assert NodeDAO.get(db.database, db.record_class(name="A")).type == NodeType.NODE_CLASS
    db.close()


def test_set_node_type_empty_label(tmp_path):
    db = SourcetrailDB.create(tmp_path / "db")
    db.set_node_type("class", graph_display="")
    db.set_node_type(NodeType.NODE_FIELD, hover_display="port")
    rows = dict(query_db(db, "SELECT id, graph_display || '|' || hover_display FROM node_type"))
    assert rows[NodeType.NODE_CLASS.value] == "|class"
    assert rows[NodeType.NODE_FIELD.value] == "|port"
    db.close()


def query_db(db: SourcetrailDB, sql: str) -> list[tuple]:
    return db.database.execute(sql).fetchall()
