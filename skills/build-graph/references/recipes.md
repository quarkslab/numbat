# Recipes

Worked mappings for common domains. Each one gives the mapping table and a small
complete graph (valid for `numbat validate`) to adapt. When the source data is
machine-readable, implement the mapping in a generator script
([../templates/generate_graph.py](../templates/generate_graph.py)) rather than
writing the JSON by hand.

## Firmware / file system

Explore what a firmware image contains and how its binaries depend on each other
(the approach of [Pyrrha](https://quarkslab.github.io/pyrrha/)).

| Domain | Numbat | Notes |
|---|---|---|
| Directory | `namespace` "Directories" | Nesting = the file tree, `delimiter: "/"` |
| Executable | `class` "Binaries" | Command: open in a disassembler; attached: `strings` output |
| Shared library | `struct` "Libraries" | |
| Exported function | `method`, `access: public` | Child of its binary / library |
| Symlink | `typedef` "Symlinks" | `type_usage` edge to its target |
| Binary imports library | `import` edge | |
| Function imported and called | `call` edge binary function → library function | Enables call paths across binaries |
| Library not found in the image | `indexed: false` | Hatched |

```json
{
  "delimiter": "/",
  "node_types": {
    "namespace": {"graph_display": "Directories", "hover_display": "directory"},
    "class": {"graph_display": "Binaries", "hover_display": "executable"},
    "struct": {"graph_display": "Libraries", "hover_display": "shared library"},
    "method": {"graph_display": "Functions", "hover_display": "function"},
    "typedef": {"graph_display": "Symlinks", "hover_display": "symlink"}
  },
  "nodes": [
    {"kind": "namespace", "name": "bin", "children": [
      {"id": "bin/busybox", "kind": "class", "name": "busybox", "hover": "ELF ARM, 812 KB",
       "command": {"argv": ["ghidraRun", "/data/fw/extracted/bin/busybox"], "description": "Open in Ghidra"},
       "attached_file": {"content": "BusyBox v1.36.1\nUsage: busybox [function [arguments]...]\n"},
       "children": [{"id": "bin/busybox/main", "kind": "method", "name": "main", "access": "public"}]},
      {"id": "bin/sh", "kind": "typedef", "name": "sh", "hover": "-> busybox"}
    ]},
    {"kind": "namespace", "name": "lib", "children": [
      {"id": "lib/libc.so.6", "kind": "struct", "name": "libc.so.6", "children": [
        {"id": "lib/libc.so.6/system", "kind": "method", "name": "system", "access": "public"}
      ]},
      {"id": "lib/libcrypto.so.1.1", "kind": "struct", "name": "libcrypto.so.1.1", "indexed": false,
       "hover": "needed but missing from the image"}
    ]}
  ],
  "edges": [
    {"kind": "type_usage", "source": "bin/sh", "target": "bin/busybox", "hover": "symlink target"},
    {"kind": "import", "source": "bin/busybox", "target": "lib/libc.so.6"},
    {"kind": "import", "source": "bin/busybox", "target": "lib/libcrypto.so.1.1"},
    {"kind": "call", "source": "bin/busybox/main", "target": "lib/libc.so.6/system"}
  ]
}
```

## Network capture

Hosts, their ports, and who talks to whom (a declarative version of
[examples/map_pcap.py](https://github.com/quarkslab/numbat/blob/main/examples/map_pcap.py)).

| Domain | Numbat | Notes |
|---|---|---|
| Subnet | `namespace` "Subnets" | Optional grouping |
| Host | `class` "Hosts" | Command: filter the capture on this host |
| Port | `field`, child of its host | `access` public = listening, private = ephemeral |
| Connection | `call` edge port → port | Aggregated: one edge per pair, packet count in `hover`; `call` enables path search across hops |
| Host outside the capture scope | `indexed: false` | |

```json
{
  "delimiter": ".",
  "node_types": {
    "namespace": {"graph_display": "Subnets", "hover_display": "subnet"},
    "class": {"graph_display": "Hosts", "hover_display": "host"},
    "field": {"graph_display": "Ports", "hover_display": "port"}
  },
  "nodes": [
    {"kind": "namespace", "name": "10.0.0.0/24", "children": [
      {"kind": "class", "name": "10.0.0.7", "hover": "workstation",
       "command": {"argv": ["wireshark", "-r", "/data/capture.pcap", "-Y", "ip.addr==10.0.0.7"],
                   "description": "Show packets in Wireshark"},
       "children": [{"id": "10.0.0.7:51234/tcp", "kind": "field", "name": "51234/tcp", "access": "private"}]},
      {"kind": "class", "name": "10.0.0.1", "hover": "gateway / proxy", "children": [
        {"id": "10.0.0.1:3128/tcp", "kind": "field", "name": "3128/tcp", "access": "public"},
        {"id": "10.0.0.1:40001/tcp", "kind": "field", "name": "40001/tcp", "access": "private"}
      ]}
    ]},
    {"kind": "class", "name": "93.184.216.34", "indexed": false, "hover": "external", "children": [
      {"id": "93.184.216.34:443/tcp", "kind": "field", "name": "443/tcp", "access": "public"}
    ]}
  ],
  "edges": [
    {"kind": "call", "source": "10.0.0.7:51234/tcp", "target": "10.0.0.1:3128/tcp", "hover": "HTTP CONNECT - 212 packets"},
    {"kind": "call", "source": "10.0.0.1:3128/tcp", "target": "10.0.0.1:40001/tcp", "hover": "proxied"},
    {"kind": "call", "source": "10.0.0.1:40001/tcp", "target": "93.184.216.34:443/tcp", "hover": "TLS - 198 packets"}
  ]
}
```

## Organization / social graph

People, teams and who works with whom.

| Domain | Numbat | Notes |
|---|---|---|
| Department | `namespace` "Departments" | |
| Team | `class` "Teams" | Box listing its people |
| Person | `method` "People", child of their main team | People *act*, so `call` edges between them read naturally; `access` public = lead |
| Contact / collaboration | `call` edge person → person | Path search answers "who can introduce me to X?" |
| Also member of another team | `member` edge team → person | One container only: the main team nests the person |
| Reports to | `usage` edge, `hover: "reports to"` | |
| External contact | `indexed: false` | |

```json
{
  "delimiter": ".",
  "node_types": {
    "namespace": {"graph_display": "Departments", "hover_display": "department"},
    "class": {"graph_display": "Teams", "hover_display": "team"},
    "method": {"graph_display": "People", "hover_display": "person"}
  },
  "nodes": [
    {"kind": "namespace", "name": "R&D", "children": [
      {"id": "security", "kind": "class", "name": "Security", "children": [
        {"id": "alice", "kind": "method", "name": "Alice Martin", "access": "public", "hover": "team lead",
         "command": {"argv": ["open", "https://intranet.example.com/people/alice"], "description": "Open profile"}},
        {"id": "bob", "kind": "method", "name": "Bob Chen"}
      ]},
      {"id": "compilers", "kind": "class", "name": "Compilers", "children": [
        {"id": "carol", "kind": "method", "name": "Carol Diaz", "access": "public"}
      ]}
    ]},
    {"kind": "class", "name": "Partners", "children": [
      {"id": "dan", "kind": "method", "name": "Dan Okafor", "indexed": false, "hover": "external consultant"}
    ]}
  ],
  "edges": [
    {"kind": "call", "source": "bob", "target": "carol", "hover": "weekly sync"},
    {"kind": "call", "source": "carol", "target": "dan", "hover": "contract"},
    {"kind": "member", "source": "compilers", "target": "bob", "hover": "50% allocation"},
    {"kind": "usage", "source": "bob", "target": "alice", "hover": "reports to"}
  ]
}
```

## Microservices / Kubernetes

Services, their endpoints and configuration, and the calls between them.

| Domain | Numbat | Notes |
|---|---|---|
| Cluster namespace | `namespace` "Namespaces" | |
| Service / deployment | `class` "Services" | Command: `kubectl describe`; attached: manifest |
| Endpoint / RPC | `method` "Endpoints" | `access` public = exposed via ingress |
| Config value, secret, volume | `field` "Config" | `usage` edges from the code that reads them |
| Service calls another | `call` edge endpoint → endpoint | Traces request paths |
| Container image | `type` "Images", `indexed: false` | `type_usage` edge service → image |

```json
{
  "delimiter": "/",
  "node_types": {
    "namespace": {"graph_display": "Namespaces", "hover_display": "k8s namespace"},
    "class": {"graph_display": "Services", "hover_display": "service"},
    "method": {"graph_display": "Endpoints", "hover_display": "endpoint"},
    "field": {"graph_display": "Config", "hover_display": "config value"},
    "type": {"graph_display": "Images", "hover_display": "container image"}
  },
  "nodes": [
    {"kind": "namespace", "name": "shop", "children": [
      {"id": "frontend", "kind": "class", "name": "frontend",
       "command": {"argv": ["kubectl", "-n", "shop", "describe", "deployment", "frontend"], "description": "kubectl describe"},
       "attached_file": {"content": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: frontend\n"},
       "children": [{"id": "frontend/GET /checkout", "kind": "method", "name": "GET /checkout", "access": "public"}]},
      {"id": "payments", "kind": "class", "name": "payments", "children": [
        {"id": "payments/Charge", "kind": "method", "name": "Charge", "postfix": "(CardRequest)"},
        {"id": "payments/STRIPE_KEY", "kind": "field", "name": "STRIPE_KEY", "access": "private", "hover": "secret"}
      ]}
    ]},
    {"id": "img/payments", "kind": "type", "name": "registry.example.com/payments:1.4.2", "indexed": false}
  ],
  "edges": [
    {"kind": "call", "source": "frontend/GET /checkout", "target": "payments/Charge", "hover": "gRPC, p99 120 ms"},
    {"kind": "usage", "source": "payments/Charge", "target": "payments/STRIPE_KEY"},
    {"kind": "type_usage", "source": "payments", "target": "img/payments"}
  ]
}
```

## Knowledge graph from a document

Entities and relations extracted from a text, linked back to where they are
mentioned.

| Domain | Numbat | Notes |
|---|---|---|
| Source document | `files` entry with the text | Nodes and edges get `locations` in it |
| Category of entities (Organizations, People, Places) | `namespace` | |
| Entity with attributes | `class` | Attributes as `field` children, value in `hover` |
| Event / action | `function` | `call` edges actor → event → affected entity |
| Is a / subtype of | `inheritance` edge | |
| Topic / tag | `annotation` | `annotation_usage` edge entity → tag |
| Uncertain extraction | `ambiguous: true` | |

```json
{
  "delimiter": ".",
  "node_types": {
    "namespace": {"graph_display": "Categories", "hover_display": "category"},
    "class": {"graph_display": "Entities", "hover_display": "entity"},
    "field": {"graph_display": "Attributes", "hover_display": "attribute"},
    "function": {"graph_display": "Events", "hover_display": "event"},
    "annotation": {"graph_display": "Topics", "hover_display": "topic"}
  },
  "files": [
    {"id": "doc", "name": "article.txt", "language": "text",
     "content": "Acme Corp acquired Beta Labs in 2023.\nBeta Labs builds fuzzers.\n"}
  ],
  "nodes": [
    {"kind": "namespace", "name": "Organizations", "children": [
      {"id": "acme", "kind": "class", "name": "Acme Corp",
       "locations": [{"file": "doc", "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 9}]},
      {"id": "beta", "kind": "class", "name": "Beta Labs",
       "locations": [{"file": "doc", "start_line": 1, "start_column": 20, "end_line": 1, "end_column": 28}],
       "children": [{"kind": "field", "name": "activity", "hover": "builds fuzzers"}]}
    ]},
    {"id": "acquisition", "kind": "function", "name": "acquisition", "postfix": "(2023)",
     "locations": [{"file": "doc", "start_line": 1, "start_column": 11, "end_line": 1, "end_column": 18}]},
    {"id": "security", "kind": "annotation", "name": "security tooling"}
  ],
  "edges": [
    {"kind": "call", "source": "acme", "target": "acquisition", "hover": "acquirer"},
    {"kind": "call", "source": "acquisition", "target": "beta", "hover": "acquired"},
    {"kind": "annotation_usage", "source": "beta", "target": "security", "ambiguous": true}
  ]
}
```
