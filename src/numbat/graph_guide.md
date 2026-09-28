# Numbat graph format

A Numbat graph file is a JSON document describing a graph that is turned into a
[NumbatUI](https://github.com/quarkslab/NumbatUI) / Sourcetrail database with:

```sh
numbat validate graph.json          # check the file, prints every issue with its path
numbat load graph.json -o my_graph  # creates my_graph.srctrldb + my_graph.srctrlprj
```

The complete reference of every field is given by `numbat schema` (JSON Schema).

## Mental model

- **Nodes can be nested.** A node's `children` are displayed *inside* it, like
  boxes in boxes (a class containing its fields, a machine containing its ports, a
  directory containing files...). Nesting is the main way to express containment:
  never add `member` edges for it, they are created automatically.
- **Edges** are directed relationships between two nodes (or files), referenced by
  their `id`. Only nodes that are referenced need an `id`.
- **Kinds are labels you can rename.** Nodes have a `kind` among a fixed list
  (`class`, `field`, `function`, ...) which drives their icon and how they are grouped
  in the UI. For non-code data, pick the kinds that fit the structure best and rename
  them with `node_types` (e.g. `class` shown as "Machines" / "machine").
- **Files** (optional) hold text that can be displayed. Nodes and edges can point at
  ranges of these files with `locations`, which highlights them in the code view.

## Example

```json
{
  "format_version": 1,
  "delimiter": ".",
  "node_types": {
    "class": {"graph_display": "Machines", "hover_display": "machine"},
    "field": {"hover_display": "port"}
  },
  "files": [
    {"id": "log", "name": "capture.log", "language": "text",
     "content": "10.0.0.7:5555 -> 10.0.0.1:80 TCP\n"}
  ],
  "nodes": [
    {"id": "gw", "kind": "class", "name": "10.0.0.1", "hover": "Gateway",
     "color": {"fill": "#DEB887", "border": "brown"},
     "children": [
       {"id": "gw.80", "kind": "field", "name": "80 TCP", "access": "public",
        "locations": [{"file": "log", "start_line": 1, "start_column": 27,
                       "end_line": 1, "end_column": 32}]}
     ]},
    {"id": "pc", "kind": "class", "name": "10.0.0.7",
     "children": [{"id": "pc.5555", "kind": "field", "name": "5555 TCP"}]}
  ],
  "edges": [
    {"kind": "usage", "source": "pc.5555", "target": "gw.80",
     "hover": "42 packets", "color": "green"}
  ]
}
```

## Top-level fields

| Field | Content |
|---|---|
| `$schema` | Optional: `https://quarkslab.github.io/numbat/graph.schema.json`. |
| `format_version` | Always `1`. |
| `delimiter` | Separator of qualified names: `::` (default), `.`, `/` or `@`. |
| `node_types` | Map from a node kind (or `file`) to `{graph_display, hover_display}`. |
| `files` | Text files: `{id, name, content}` or `{id, path}` (relative to the JSON file). |
| `nodes` | Top-level nodes, with nested `children`. |
| `edges` | `{kind, source, target}` relationships. |
| `local_symbols` | Symbols only visible in the code view: `{name, locations}`. |

## Nodes

`{id, kind, name, prefix, postfix, delimiter, indexed, hover, access, color, command,
attached_file, locations, children}`. Only `name` is required.

- `kind`: `symbol` (default), `type`, `builtin_type`, `module`, `namespace`,
  `package`, `struct`, `class`, `interface`, `annotation`, `global_variable`, `field`,
  `function`, `method`, `enum`, `enum_constant`, `typedef`, `type_parameter`, `macro`,
  `union`.
- `prefix` / `postfix`: text around the name (e.g. `"prefix": "int"`,
  `"postfix": "(char *s)"`).
- `indexed: false`: the node is known but not defined in the data (hatched in the UI).
- `hover`: tooltip text.
- `access`: `public`, `protected`, `private`, `default`, `template_parameter`,
  `type_parameter`.
- `color`: `{fill, border, text, icon, hatching}`, each `"#RRGGBB"` or an SVG color
  keyword (`red`, `steelblue`...).
- `command`: `{argv: ["program", "arg"], description}`, added to the context menu.
- `attached_file`: `{content}` or `{path}`, displayed when the node is selected.
- `locations`: `[{file, start_line, start_column, end_line, end_column, type}]`, `type`
  being `token` (default: the name itself), `scope` (the whole body), `signature`,
  `qualifier` or `atomic_range`.

## Edges

`{kind, source, target, unsolved, hover, color, ambiguous, locations}`.

- `kind`: `usage`, `call`, `type_usage`, `inheritance`, `override`, `type_argument`,
  `template_specialization`, `include`, `import`, `macro_usage`, `annotation_usage`,
  `member`.
- `unsolved: true`: the target is unknown; omit `target` and give exactly one location.
- `locations`: ranges (without `type`) where the relationship appears.

## Rules

1. `id`s are unique across all nodes **and** files.
2. Every `source`, `target` and location `file` must reference an existing `id`.
3. Two sibling nodes cannot have the same `prefix` + `name` + `postfix`: they would be
   merged. Make names distinct (or use `postfix` to disambiguate).
4. `delimiter` is only allowed on top-level nodes.
5. Lines and columns are 1-based and inclusive; a range cannot end before it starts.
6. A file has either `content` or `path`, not both; `name` is required with `content`.
7. Unknown fields are errors: check spelling against this guide.

## Workflow

Write the JSON, run `numbat validate graph.json` and fix every reported issue (each
one is prefixed by its path in the document, e.g. `nodes[0].children[2].kind`), then
run `numbat load graph.json -o output`. Open `output.srctrlprj` with NumbatUI.
