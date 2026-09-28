# Interactive features

Beyond nodes and edges, NumbatUI offers features that turn a static picture into a
workbench. Decide for each attribute and piece of content of the data which feature
carries it. Every example below is a complete graph file that passes
`numbat validate`.

## Custom commands

A node (or file) can carry one **command** added to its context menu (right click).
It runs an arbitrary program on the viewer's machine: open the real object behind a
node in the right tool. This is what makes the graph an entry point rather than a
dead end.

`argv` is the program followed by its arguments (no shell parsing), `description` is
the menu label.

```json
{
  "nodes": [
    {"id": "busybox", "kind": "class", "name": "busybox",
     "command": {"argv": ["ghidraRun", "/data/fw/extracted/bin/busybox"],
                 "description": "Open in Ghidra"}},
    {"id": "alice", "kind": "class", "name": "Alice Martin",
     "command": {"argv": ["open", "https://intranet.example.com/people/alice"],
                 "description": "Open profile"}},
    {"id": "handler", "kind": "function", "name": "parse_request",
     "command": {"argv": ["code", "--goto", "/src/server/http.c:128"],
                 "description": "Open in VS Code"}},
    {"id": "gw", "kind": "class", "name": "10.0.0.1",
     "command": {"argv": ["wireshark", "-r", "/data/capture.pcap", "-Y", "ip.addr==10.0.0.1"],
                 "description": "Show packets in Wireshark"}}
  ]
}
```

Tips:

- Use **absolute paths**: the command runs wherever NumbatUI runs, not where the JSON
  was written.
- Typical uses: open the file, binary, URL, ticket or dashboard behind the node; run
  a script that extracts more details about it.
- A wrapper script can go further (e.g. `["python3", "/tools/triage.py", "busybox"]`).

## Sideloaded content

A node can be associated with a text shown in NumbatUI **when the node is selected**
(`attached_file`). The content is not stored in the database nor recorded as a node:
it is stored in the `<db>_files/` directory next to the database and read by
NumbatUI only when needed. Use it for anything worth reading in context: a
decompiled function, a `strings` dump, a config, a README, a log excerpt, notes.

Two forms:

- `{"content": "..."}`: inline text, convenient when the text is generated;
- `{"path": "relative/to/graph.json"}`: an existing file on disk, copied at load time
  (it must exist when running `numbat validate` / `numbat load`).

```json
{
  "nodes": [
    {"id": "sshd_config", "kind": "field", "name": "sshd_config",
     "attached_file": {"content": "Port 22\nPermitRootLogin no\nPasswordAuthentication no\n"}},
    {"id": "report", "kind": "class", "name": "CVE-2024-1234",
     "hover": "CVSS 9.8",
     "attached_file": {"content": "# CVE-2024-1234\n\nHeap overflow in parse_request().\nFixed in 1.2.3.\n"}}
  ]
}
```

For large texts, prefer writing them to files next to the JSON and using `path`,
rather than inlining megabytes into the JSON.

## Hover text

`hover` sets the tooltip of a node, file or edge. It replaces the default tooltip, so
it is the place for metadata that should not be part of the name: sizes, counts,
versions, dates, scores, descriptions.

```json
{
  "nodes": [
    {"id": "a", "kind": "class", "name": "10.0.0.7", "hover": "workstation - 1.2 GB exchanged"},
    {"id": "b", "kind": "class", "name": "10.0.0.1", "hover": "gateway"}
  ],
  "edges": [
    {"kind": "call", "source": "a", "target": "b", "hover": "TCP/443 - 1203 packets"}
  ]
}
```

## Colors

Nodes have five color slots (`fill`, `border`, `text`, `icon`, `hatching`), edges one
`color`. Values are `#RRGGBB` or SVG color keywords (`red`, `steelblue`...). Use color
to encode **one** dimension consistently (status, severity, owner, trust) and keep
the default colors elsewhere.

```json
{
  "nodes": [
    {"id": "vuln", "kind": "class", "name": "libssl.so.1.0.0",
     "color": {"fill": "#FFCCCC", "border": "red"}, "hover": "outdated, 12 known CVEs"},
    {"id": "ok", "kind": "class", "name": "libssl.so.3", "color": {"fill": "#CCFFCC"}}
  ],
  "edges": [
    {"kind": "import", "source": "ok", "target": "vuln", "color": "red", "hover": "suspicious dependency"}
  ]
}
```

## Access groups

Inside `class` / `struct` boxes, members are split into **public**, **protected** and
**private** sections. Beyond code, this is a free three-way sub-grouping of an
entity's members: exposed / internal / hidden ports, exported / internal / local
symbols, owners / members / guests.

```json
{
  "node_types": {"class": {"graph_display": "Hosts", "hover_display": "host"},
                 "field": {"hover_display": "port"}},
  "nodes": [
    {"kind": "class", "name": "web-01", "children": [
      {"kind": "field", "name": "443/tcp", "access": "public", "hover": "exposed to internet"},
      {"kind": "field", "name": "9100/tcp", "access": "protected", "hover": "monitoring VLAN only"},
      {"kind": "field", "name": "5432/tcp", "access": "private", "hover": "localhost only"}
    ]}
  ]
}
```

## Non-indexed nodes

`indexed: false` marks an entity that is referenced but not described by the data
(an external host, a missing library, a person outside the organization). It is drawn
**hatched**, making the boundary of the dataset visible.

```json
{
  "nodes": [
    {"id": "app", "kind": "class", "name": "app"},
    {"id": "libfoo", "kind": "class", "name": "libfoo.so", "indexed": false,
     "hover": "imported but not found in the image"}
  ],
  "edges": [{"kind": "import", "source": "app", "target": "libfoo"}]
}
```

## Files and locations

When nodes really come **from a text** (source code, a log, a config, a document),
record the text in `files` and point nodes and edges at ranges of it with
`locations`. Selecting a node then highlights where it appears; clicking an edge
shows where the relation appears. Lines and columns are 1-based and inclusive.

```json
{
  "files": [
    {"id": "log", "name": "auth.log", "language": "text",
     "content": "alice logged in from 10.0.0.7\nbob logged in from 10.0.0.9\n"}
  ],
  "nodes": [
    {"id": "alice", "kind": "class", "name": "alice",
     "locations": [{"file": "log", "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 5}]},
    {"id": "h7", "kind": "class", "name": "10.0.0.7",
     "locations": [{"file": "log", "start_line": 1, "start_column": 22, "end_line": 1, "end_column": 29}]}
  ],
  "edges": [
    {"kind": "call", "source": "alice", "target": "h7",
     "locations": [{"file": "log", "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 29}]}
  ]
}
```

Location `type`: `token` (default: the name itself), `scope` (the whole body),
`signature`, `qualifier`, `atomic_range`. Files can also carry `errors` (shown as
indexer errors) and nodes can reference files in edges.

If the text only illustrates a node and no range matters, use `attached_file`
instead.

## Uncertain relations

- `ambiguous: true` on an edge: the relation is inferred or uncertain.
- `unsolved: true` on an edge: the target is unknown (omit `target`, give exactly one
  location), e.g. a call to a function that could not be resolved.
