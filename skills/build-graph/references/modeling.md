# Modelling a domain for NumbatUI

NumbatUI was built to explore source code, and its vocabulary (classes, functions,
calls, inheritance...) comes from there. Any graph fits in it as long as each domain
concept is mapped to the **code concept with the same meaning**. A reader who knows
code then understands the graph without a legend, and NumbatUI features built for
code (call graphs, path search, member lists) work on the domain.

## 1. Containment: choose the hierarchy

Nesting is Numbat's distinctive feature: children are drawn inside their parent and
edges between deeply nested nodes are still shown (and bundled between their
containers when collapsed).

- **Each node has at most one container.** When an entity has several candidate
  containers (a library shipped in several firmware images, a person in two teams),
  nest it under the one users will browse by, and express the others with edges:
  - `member` edge: a real inclusion ("Alice is also a member of Team B");
  - `usage` edge: a looser, general-purpose relation ("Team B relies on Alice").
- **Prefer depth that carries meaning.** `datacenter ⊃ rack ⊃ host ⊃ process` is
  good; an extra level with a single child everywhere is noise.
- **Do not flatten.** Encoding the hierarchy in names (`"rack1/host3/nginx"` as a
  top-level node) loses the boxes-in-boxes view.
- Choose the `delimiter` of qualified names (shown in search and tooltips) to match
  the domain: `/` for paths, `.` for dotted names, `::` (default), or `@`.

## 2. Node kinds

`kind` drives the icon, the default color, how children are drawn and how nodes are
grouped in the overview. Pick by **role**, then rename with `node_types`.

| Role in the domain | Kinds | How it renders |
|---|---|---|
| Pure grouping / scope (organization, directory, network segment, layer) | `namespace`, `package`, `module` | Box containing its children |
| Entity with members (machine, binary, person, service, document) | `class`, `struct`, `interface`, `union` | Box listing its members, split by `access` (public / protected / private); by default only members with edges are shown, the others behind an expand arrow |
| Active element: acts, triggers, sends (function, endpoint, process, actor, handler) | `function` (top-level), `method` (inside an entity) | Yellow; source and target of `call` edges |
| Passive element: data, attribute, resource (port, config key, variable, field) | `global_variable` (top-level), `field` (inside an entity) | Blue; target of `usage` edges |
| A closed set of categories and its values (severity, state, protocol) | `enum` ⊃ `enum_constant` | Enum box with its constants |
| Abstract or external thing, alias (symlink, external library, data type) | `type`, `typedef`, `builtin_type` | Gray |
| Tag / label applied to many nodes | `annotation` | Target of `annotation_usage` edges |
| Generic / anything else | `symbol` (default), `macro`, `type_parameter` | Neutral |

Guidelines:

- **One kind per domain category**: `node_types` relabels a kind globally.
- Give every kind you use a `node_types` label: `graph_display` (plural, shown in the
  overview, e.g. "Machines") and `hover_display` (singular, shown in tooltips, e.g.
  "machine"). An empty `graph_display` hides the kind from the overview.
- Relabeling `file` is also possible when you record `files`.
- Use `indexed: false` for entities that are referenced but not described in the data
  (an external IP, an imported library you do not have): they are drawn hatched.

## 3. Edge kinds

Edges are directed, `source` → `target`. They cannot be renamed: pick by meaning and
distinguish relations sharing a kind with `hover` and `color`.

| Relation in the domain | Edge kind | Why |
|---|---|---|
| Active interaction: contacts, sends to, invokes, triggers, connects to | `call` | Powers NumbatUI's call graph and path search: use it for every relation you want to trace transitively ("how does A reach B?") |
| Reads, accesses, refers to, uses a resource (general purpose) | `usage` | The default when nothing more specific fits |
| Is typed by, depends on the definition of, is an instance of | `type_usage` | |
| Includes, embeds, loads (a file, a library) | `include` | Include-tree trail |
| Imports, depends on (at build / install time) | `import` | |
| Is a, derives from, is a fork / variant of | `inheritance` | Inheritance-chain trail |
| Replaces, overrides, supersedes | `override` | |
| Is tagged with | `annotation_usage` | Target is an `annotation` node |
| Is included in (a group other than its container) | `member` | Never for the node's own container |
| Is parameterized by / is a specialization of | `type_argument`, `template_specialization` | Rarely needed |
| Macro expansion | `macro_usage` | Rarely needed |

Guidelines:

- Edges can link nodes at any depth and files: link the **most precise** nodes (port
  to port rather than machine to machine); NumbatUI aggregates them visually when
  containers are collapsed.
- Numbat does not deduplicate edges: aggregate repeated relations yourself (one edge
  with `"hover": "42 packets"` rather than 42 edges).
- `ambiguous: true` marks an uncertain relation (inferred, heuristic).

## 4. Names and identity

- A node is identified by its qualified name: the `prefix`, `name` and `postfix` of
  the node and of all its ancestors. Siblings with identical triples are merged, and
  the validator reports it.
- `name` is the stable, readable identity (`10.0.0.1`, `busybox`, `Alice Martin`).
- `prefix` / `postfix` are decoration displayed around it: a role (`"prefix":
  "Machine"`), a signature (`"postfix": "(80/tcp)"`), a version. Use `postfix` to
  disambiguate siblings that share a name (two `README` in the same container: use
  different postfixes or better, a more precise name).
- Volatile values (counts, sizes, timestamps, scores) go in `hover`, never in names.
- `id`s are only needed for nodes referenced by edges. Make them readable and derived
  from the data (`"fw/bin/busybox"`, `"10.0.0.1:80/tcp"`) so scripts can compute
  them without lookup tables.

## 5. Anti-patterns

| Don't | Do |
|---|---|
| Add `member` edges from a node to its children | Use `children` |
| One top-level node per leaf with the hierarchy in the name | Nest |
| The same kind for unrelated categories | One kind per category, relabeled |
| `usage` for everything | `call` for interactions to trace, specific kinds when they fit |
| Counts / dates in names | `hover` |
| A fake source file to show a text | `attached_file` |
| Hundreds of duplicate edges | One edge with an aggregated `hover` |
| Re-typing machine-readable data node by node | A generator script |
