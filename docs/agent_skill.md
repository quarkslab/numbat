# Agent Skill

Numbat ships a `build-graph` agent skill in
[`skills/build-graph`](https://github.com/quarkslab/numbat/tree/main/skills/build-graph).
It teaches an AI agent how to turn any graph-shaped data into a NumbatUI database
using [graph files](graph_files.md): firmware images, network captures,
infrastructure, organizations, knowledge extracted from documents, and so on.

The format itself is documented by `numbat guide`, which the skill tells the agent to
read. The skill adds the *modelling* knowledge: how to map a domain onto Numbat's
nested nodes and edge kinds so that the result reads well in NumbatUI.

## What the agent does

1. Checks that the `numbat` command is available and reads `numbat guide`.
2. Profiles the data: entity kinds, containment, relations, attributes, text content.
3. Designs a mapping table (domain entity → node kind and label, domain relation →
   edge kind) and shows it to you when the domain is not obvious.
4. Writes the JSON directly when the agent itself is the source of the nodes
   (knowledge extracted from documents, curated views), or writes a script building
   the graph with `numbat.model` when the data is machine-readable (file trees,
   captures, API dumps, tool output). The script always saves the JSON.
5. Runs `numbat validate --json` and fixes every issue.
6. Runs `numbat load` and prints the path of the `.srctrlprj` file to open in
   NumbatUI.

Its main modelling rules:

- reuse the **code concept with the same meaning**: a person contacting a person is a
  function calling a function, a sub-kind is an inheritance;
- nest with `children`; a node has a single container, other affiliations are
  `member` (inclusion) or `usage` (general purpose) edges;
- model the relations you want to trace as `call` edges, NumbatUI path searches work
  on them;
- one node kind per domain category, relabeled with `node_types`;
- use [custom commands](customization.md#custom-commands) to open the real object
  behind a node, and [sideloaded content](customization.md#file-sideloading) to show
  text when a node is selected.

## Installation

The skill follows the open [Agent Skills](https://agentskills.io) format (a folder
with a `SKILL.md`), so any agent supporting it can use it. The repository is also a
Claude Code plugin (`.claude-plugin/plugin.json`).

```bash
git clone https://github.com/quarkslab/numbat.git
pip install numbat   # the skill drives the `numbat` command

# Claude Code: load the repository as a plugin for a session
claude --plugin-dir numbat
# or install the skill for all sessions
cp -r numbat/skills/build-graph ~/.claude/skills/

# Other agents: copy skills/build-graph into the agent's skills directory
```

## Usage

With Claude Code, invoke it explicitly with `/numbat:build-graph` (or `/build-graph`
when copied to `~/.claude/skills`), or simply ask for a visualization, the agent
picks the skill from its description:

```text
Map the Kubernetes manifests in ./deploy into a Numbat graph: services, their
endpoints and config, and which service calls which.
```

## Content

| File | Content |
|---|---|
| `SKILL.md` | Workflow and core modelling rules |
| `references/modeling.md` | Choosing containers, node kinds and edge kinds; naming; anti-patterns |
| `references/features.md` | Custom commands, sideloaded content, hover, colors, access groups, non-indexed nodes, files and locations, each with an example |
| `references/recipes.md` | Worked mappings: firmware, network capture, organization, microservices, knowledge graph |
| `templates/generate_graph.py` | Generator script skeleton |
