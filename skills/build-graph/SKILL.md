---
name: build-graph
description: Build a NumbatUI (Sourcetrail) database from any graph-shaped data with Numbat - nested entities (boxes inside boxes) linked by relationships. Use when asked to visualize, map or explore relationships and containment in data such as code, binaries, firmware, file systems, network captures, infrastructure, organizations, or knowledge extracted from documents, or when asked to produce a Numbat graph JSON file, a .srctrldb / .srctrlprj database, or something to open in NumbatUI.
---

# Build a Numbat graph

Numbat turns a JSON description of a graph into a database that
[NumbatUI](https://github.com/quarkslab/NumbatUI) displays. Unlike standard graph or
knowledge-graph tools, **nodes can be nested**: a node is drawn inside its container
(machine ⊃ ports, directory ⊃ files, team ⊃ people) while edges still link any two
nodes, whatever their depth. Good results come from exploiting both.

This skill is about *modelling* data so it reads well in NumbatUI. The field-by-field
reference of the format is printed by `numbat guide`: always read it, it is the
reference for the installed version.

## Workflow

### 0. Check the tooling

```sh
numbat --version            # needs numbat >= 0.3.0
pip install -U numbat       # if missing or older
```

### 1. Read the format reference

```sh
numbat guide                # fields, kinds, rules (Markdown)
numbat schema               # JSON Schema, if you need exact field definitions
```

### 2. Profile the data

List, from the source data:

- the **entity kinds** (machines, people, binaries, functions...);
- the **containment** relation: which entity lives inside which. Every node has
  **at most one container**, so pick the hierarchy users will browse by;
- the other **relation kinds** (talks to, depends on, is a, tagged with...);
- **attributes** (metadata, status, counts) and any **text content** (logs, configs,
  source, documentation) worth showing.

### 3. Design the mapping before writing JSON

Write a short mapping table and, unless the domain is trivial, show it to the user
before generating anything:

| Domain | Numbat | Label (`node_types`) / styling |
|---|---|---|
| Machine | `class` | "Machines" / "machine" |
| Port | `field` (child of machine) | hover "port" |
| Connection | `call` edge port → port | hover = packet count |

Choose kinds and edges with [references/modeling.md](references/modeling.md). The
core rule: **reuse the code concept with the same meaning** - a person contacting a
person is a function calling a function, a data item being read is a field being
used, a sub-kind is an inheritance.

Then decide which interactive features carry the attributes and content
([references/features.md](references/features.md)): custom commands, sideloaded
content, hover text, colors, access groups, non-indexed nodes.

Worked mappings for common domains: [references/recipes.md](references/recipes.md).

### 4. Produce the JSON

Choose by **who produces the nodes**, not by the size of the graph:

- **You are the source**: the nodes come from your reading and judgment (knowledge
  extracted from documents, a curated architecture view, a summary of a
  discussion). Write the JSON directly.
- **The data is machine-readable** (a file tree, a capture, an API dump, a CSV, a
  database, tool output): write a script that reads it and builds the graph with
  `numbat.model`, starting from [templates/generate_graph.py](templates/generate_graph.py).
  Re-typing machine-readable data node by node is slow, bounded by your output
  length, error-prone (omitted, drifting or invented items) and not reproducible;
  a script is exact and can be re-run when the data changes. The script always
  saves the JSON, which is then validated and loaded like a hand-written one.

Both can be combined: script the bulk of the graph, and put the curated parts
(labels, colors, commands) in the script's mapping rather than editing the output.

### 5. Validate until clean

```sh
numbat validate graph.json --json
```

Every issue carries its path in the document (e.g. `nodes[0].children[2].kind`) and
often a suggestion. Fix them all and re-run: structural errors (unknown fields, bad
enum values) are reported before semantic ones (unknown ids, merged nodes), so it
can take a few rounds. If the JSON comes from a script, fix the script, not the
output.

### 6. Load and hand over

```sh
numbat load graph.json -o out        # add -f to overwrite an existing database
```

This creates `out.srctrldb`, `out.srctrlprj` and, if files are sideloaded, an
`out_files/` directory - keep them together. Print the absolute path of
`out.srctrlprj`: the user opens it with NumbatUI. Do not try to launch NumbatUI.

## Core rules

1. **Nesting is expressed with `children` only.** Never add `member` edges to
   express the container of a node; they are created automatically.
2. **One container per node.** If an entity belongs to several groups, nest it in
   the main one and link the others with a `member` edge (inclusion) or a `usage`
   edge (looser relation).
3. **Model the relations to trace as `call` edges.** NumbatUI's call graph and path
   search between two nodes work on them, which makes "how does A reach B?" a single
   click.
4. **One `kind` per domain category.** `node_types` relabels a kind *globally*
   (every `class` becomes a "Machine"), so two unrelated categories must not share a
   kind. There are 20 kinds available.
5. **Names are identities.** Two siblings with the same `prefix` + `name` +
   `postfix` would be merged into one node (validation reports it). Keep names stable
   and readable; put changing values (counts, dates, sizes) in `hover`, not in names.
6. **Only referenced nodes need an `id`.** Use readable, path-like ids
   (`"fw/bin/busybox"`, `"10.0.0.1:80"`).
7. **Show text with `attached_file`,** not with fake source files. Use `files` +
   `locations` only when the nodes really come from ranges of a text (code, logs,
   configs).
