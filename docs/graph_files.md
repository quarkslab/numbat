# Graph Files

Instead of calling the API, a whole graph can be described in a JSON file and turned
into a database with the `numbat` command, installed with the package. The format is
designed to be easy to write for humans, scripts and LLMs:

- `numbat guide` prints the page below, meant to be given to an LLM as instructions;
- `numbat schema` prints the [JSON Schema](graph.schema.json) of the format, which
  can be used as a structured output / tool input schema. It is also published at
  `https://quarkslab.github.io/numbat/graph.schema.json`;
- `numbat validate graph.json [--json]` reports every issue with its path in the
  document, so that the file can be fixed in a single iteration.

The same model is available in Python (`numbat.model`) to build graph files from a
script, and `numbat.loader.load_graph` loads a `Graph` into an open `SourcetrailDB`:

```python
from numbat import SourcetrailDB
from numbat.loader import load_graph
from numbat.model import Edge, Graph, Node
from numbat.types import EdgeType, NodeType

graph = Graph(
    nodes=[
        Node(id="A", kind=NodeType.NODE_CLASS, name="A",
             children=[Node(id="A.f", kind=NodeType.NODE_METHOD, name="f")]),
        Node(id="g", kind=NodeType.NODE_FUNCTION, name="g"),
    ],
    edges=[Edge(kind=EdgeType.CALL, source="g", target="A.f")],
)
graph.save("graph.json")  # or load it directly:

db = SourcetrailDB.open("my_database", clear=True)
load_graph(graph, db)
db.commit()
db.close()
```

Editors supporting JSON Schema (e.g. VS Code) validate and auto-complete a graph
file that references the schema:

```json
{
  "$schema": "https://quarkslab.github.io/numbat/graph.schema.json",
  "nodes": [{"name": "A"}]
}
```

A complete example using every feature is available in
[`examples/graph.json`](https://github.com/quarkslab/numbat/blob/main/examples/graph.json).

---

--8<-- "src/numbat/graph_guide.md"
