import importlib.util
import json
import re
from pathlib import Path

import pytest

import numbat
from numbat.loader import validate
from numbat.model import Graph

ROOT = Path(__file__).parents[2]
SKILL = ROOT / "skills" / "build-graph"


def json_examples() -> list:
    """Return every complete graph given as a JSON example in the skill."""
    examples = []
    for md in sorted(SKILL.rglob("*.md")):
        blocks = re.findall(r"```json\n(.*?)```", md.read_text(), re.S)
        for i, block in enumerate(blocks):
            examples.append(pytest.param(block, id=f"{md.stem}-{i}"))
    return examples


def test_plugin_version_matches_package() -> None:
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["version"] == numbat.__version__


def test_skill_frontmatter() -> None:
    text = (SKILL / "SKILL.md").read_text()
    match = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
    assert match, "SKILL.md must start with a name/description frontmatter"
    name, description = match.groups()
    assert name == SKILL.name  # Agent Skills: name must match the directory
    assert len(description) <= 1024


@pytest.mark.parametrize("block", json_examples())
def test_skill_examples_are_valid(block: str) -> None:
    graph = Graph.from_json(block)
    assert [str(i) for i in validate(graph)] == []


def load_template():
    spec = importlib.util.spec_from_file_location(
        "generate_graph", SKILL / "templates" / "generate_graph.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_builds_valid_graph(tmp_path: Path) -> None:
    tpl = load_template()
    entities = [
        tpl.Entity(key="a", name="A", category="c"),
        tpl.Entity(key="a/x", name="x", category="c", parent="a"),
        tpl.Entity(key="b", name="B", category="c"),
    ]
    relations = [
        tpl.Relation(source="a/x", target="b", type="r", hover="h"),
        tpl.Relation(source="a/x", target="b", type="r", hover="h"),
    ]
    graph = tpl.build_graph(entities, relations)
    assert [n.name for n in graph.nodes] == ["A", "B"]
    assert [n.name for n in graph.nodes[0].children] == ["x"]
    assert len(graph.edges) == 1 and graph.edges[0].hover == "2 occurrences - h"

    out = tmp_path / "graph.json"
    graph.save(out)
    assert validate(Graph.load(out)) == []


def test_template_rejects_unknown_parent() -> None:
    tpl = load_template()
    with pytest.raises(KeyError):
        tpl.build_nodes([tpl.Entity(key="x", name="x", category="c", parent="nope")])
