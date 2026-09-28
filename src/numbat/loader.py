# -*- coding: utf-8 -*-

#  Copyright 2026 Quarkslab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Validate a `Graph` document and load it into a Sourcetrail database."""

from pathlib import Path

from .api import SourcetrailDB
from .exceptions import NumbatException
from .model import (
    FORMAT_VERSION,
    Command,
    Graph,
    GraphValidationError,
    IndexerError,
    Location,
    NodeColor,
    ValidationIssue,
    _suggest,
)
from .types import (
    ComponentAccessType,
    EdgeType,
    NameElement,
    NameHierarchy,
    NodeType,
    SourceLocationType,
)

_NODE_RECORDERS = {
    NodeType.NODE_SYMBOL: SourcetrailDB.record_symbol_node,
    NodeType.NODE_TYPE: SourcetrailDB.record_type_node,
    NodeType.NODE_BUILTIN_TYPE: SourcetrailDB.record_buitin_type_node,
    NodeType.NODE_MODULE: SourcetrailDB.record_module,
    NodeType.NODE_NAMESPACE: SourcetrailDB.record_namespace,
    NodeType.NODE_PACKAGE: SourcetrailDB.record_package,
    NodeType.NODE_STRUCT: SourcetrailDB.record_struct,
    NodeType.NODE_CLASS: SourcetrailDB.record_class,
    NodeType.NODE_INTERFACE: SourcetrailDB.record_interface,
    NodeType.NODE_ANNOTATION: SourcetrailDB.record_annotation,
    NodeType.NODE_GLOBAL_VARIABLE: SourcetrailDB.record_global_variable,
    NodeType.NODE_FIELD: SourcetrailDB.record_field,
    NodeType.NODE_FUNCTION: SourcetrailDB.record_function,
    NodeType.NODE_METHOD: SourcetrailDB.record_method,
    NodeType.NODE_ENUM: SourcetrailDB.record_enum,
    NodeType.NODE_ENUM_CONSTANT: SourcetrailDB.record_enum_constant,
    NodeType.NODE_TYPEDEF: SourcetrailDB.record_typedef_node,
    NodeType.NODE_TYPE_PARAMETER: SourcetrailDB.record_type_parameter_node,
    NodeType.NODE_MACRO: SourcetrailDB.record_macro,
    NodeType.NODE_UNION: SourcetrailDB.record_union,
}

_EDGE_RECORDERS = {
    EdgeType.MEMBER: SourcetrailDB.record_ref_member,
    EdgeType.TYPE_USAGE: SourcetrailDB.record_ref_type_usage,
    EdgeType.USAGE: SourcetrailDB.record_ref_usage,
    EdgeType.CALL: SourcetrailDB.record_ref_call,
    EdgeType.INHERITANCE: SourcetrailDB.record_ref_inheritance,
    EdgeType.OVERRIDE: SourcetrailDB.record_ref_override,
    EdgeType.TYPE_ARGUMENT: SourcetrailDB.record_ref_type_argument,
    EdgeType.TEMPLATE_SPECIALIZATION: SourcetrailDB.record_ref_template_specialization,
    EdgeType.INCLUDE: SourcetrailDB.record_ref_include,
    EdgeType.IMPORT: SourcetrailDB.record_ref_import,
    EdgeType.MACRO_USAGE: SourcetrailDB.record_ref_macro_usage,
    EdgeType.ANNOTATION_USAGE: SourcetrailDB.record_ref_annotation_usage,
}

_ACCESS_RECORDERS = {
    ComponentAccessType.PUBLIC: SourcetrailDB.record_public_access,
    ComponentAccessType.PROTECTED: SourcetrailDB.record_protected_access,
    ComponentAccessType.PRIVATE: SourcetrailDB.record_private_access,
    ComponentAccessType.DEFAULT: SourcetrailDB.record_default_access,
    ComponentAccessType.TEMPLATE_PARAMETER: (
        SourcetrailDB.record_template_parameter_access
    ),
    ComponentAccessType.TYPE_PARAMETER: SourcetrailDB.record_type_parameter_access,
}

_LOCATION_RECORDERS = {
    SourceLocationType.TOKEN: SourcetrailDB.record_symbol_location,
    SourceLocationType.SCOPE: SourcetrailDB.record_symbol_scope_location,
    SourceLocationType.SIGNATURE: SourcetrailDB.record_symbol_signature_location,
    SourceLocationType.QUALIFIER: SourcetrailDB.record_qualifier_location,
    SourceLocationType.ATOMIC_RANGE: SourcetrailDB.record_atomic_source_range,
}


# ------------------------------------------------------------------------ #
# Semantic validation                                                      #
# ------------------------------------------------------------------------ #


def validate(graph: Graph, base_dir: Path | str | None = None) -> list[ValidationIssue]:
    """Check the consistency of a graph (references, uniqueness, files, ...).

    The structure itself (fields, types, enum values) is already checked when
    the graph is decoded with `Graph.from_dict`.

    :param graph: The graph to check
    :param base_dir: Directory against which relative paths are resolved
    :return: All the issues found (errors and warnings)
    """
    base = Path(base_dir) if base_dir is not None else Path(".")
    issues: list[ValidationIssue] = []
    ids: dict[str, str] = {}  # id -> path in the document
    file_ids: set[str] = set()
    qualified_names: dict[str, str] = {}  # serialized name -> path in the document

    def error(path: str, msg: str) -> None:
        issues.append(ValidationIssue(path, msg))

    def warning(path: str, msg: str) -> None:
        issues.append(ValidationIssue(path, msg, "warning"))

    def register_id(id_: str, path: str) -> None:
        if not id_:
            error(f"{path}.id", "must not be empty")
        elif id_ in ids:
            error(f"{path}.id", f"duplicate id '{id_}' (already used by {ids[id_]})")
        else:
            ids[id_] = path

    def register_name(hierarchy: NameHierarchy, path: str) -> None:
        name = hierarchy.serialize_name()
        if name in qualified_names:
            error(
                path,
                "same qualified name (delimiter, prefix, name, postfix of the node and "
                f"its ancestors) as {qualified_names[name]}, both would be merged "
                "into a single node",
            )
        else:
            qualified_names[name] = path

    def check_command(command: Command | None, path: str) -> None:
        if command is not None and not command.argv:
            error(f"{path}.argv", "must contain at least the program to run")

    def check_range(r: Location | IndexerError, path: str) -> None:
        if (r.end_line, r.end_column) < (r.start_line, r.start_column):
            error(path, "the range ends before it starts")

    def check_location(loc: Location, path: str) -> None:
        if loc.file not in file_ids:
            hint = (
                " (it is not a file id)"
                if loc.file in ids
                else _suggest(loc.file, file_ids)
            )
            error(f"{path}.file", f"unknown file id '{loc.file}'{hint}")
        check_range(loc, path)

    def check_reference(id_: str, path: str) -> None:
        if id_ not in ids:
            error(path, f"unknown id '{id_}'{_suggest(id_, ids)}")

    def check_existing_file(file: str, path: str) -> None:
        if not (base / file).is_file():
            error(path, f"file not found: {base / file}")

    if graph.format_version != FORMAT_VERSION:
        error("format_version", f"unsupported version, expected {FORMAT_VERSION}")

    # Files
    for i, file in enumerate(graph.files):
        path = f"files[{i}]"
        register_id(file.id, path)
        file_ids.add(file.id)
        if file.path is not None and file.content is not None:
            error(path, "'path' and 'content' are mutually exclusive")
        if file.path is not None:
            check_existing_file(file.path, f"{path}.path")
        name = file.name or file.path
        if not name:
            error(path, "'name' is required when 'path' is not given")
        else:
            register_name(
                NameHierarchy(
                    NameHierarchy.NAME_DELIMITER_FILE, [NameElement("", name, "")]
                ),
                path,
            )
        check_command(file.command, f"{path}.command")
        for j, err in enumerate(file.errors):
            check_range(err, f"{path}.errors[{j}]")

    # Nodes
    hierarchies: dict[int, tuple[str, list[NameElement]]] = {}  # id(node) -> hierarchy
    parent_ids: dict[str, str] = {}  # node id -> parent node id
    for node, parent, path in graph.iter_nodes():
        if node.id is not None:
            register_id(node.id, path)
        if not node.name:
            error(f"{path}.name", "must not be empty")
        element = NameElement(node.prefix, node.name, node.postfix)
        if parent is None:
            delimiter, elements = node.delimiter or graph.delimiter, [element]
        else:
            if node.delimiter is not None:
                error(
                    f"{path}.delimiter",
                    "only allowed on top-level nodes, children use the delimiter of "
                    "their top-level ancestor",
                )
            delimiter, parent_elements = hierarchies[id(parent)]
            elements = parent_elements + [element]
            if parent.id is not None and node.id is not None:
                parent_ids[node.id] = parent.id
        hierarchies[id(node)] = (delimiter, elements)
        register_name(NameHierarchy(delimiter, list(elements)), path)

        check_command(node.command, f"{path}.command")
        attached = node.attached_file
        if attached is not None:
            if (attached.path is None) == (attached.content is None):
                error(
                    f"{path}.attached_file",
                    "exactly one of 'path' or 'content' is required",
                )
            elif attached.path is not None:
                check_existing_file(attached.path, f"{path}.attached_file.path")

    # Locations are checked once all file ids are known
    for node, _, path in graph.iter_nodes():
        for j, sym_loc in enumerate(node.locations):
            check_location(sym_loc, f"{path}.locations[{j}]")

    # Edges
    for i, edge in enumerate(graph.edges):
        path = f"edges[{i}]"
        check_reference(edge.source, f"{path}.source")
        if edge.unsolved:
            if edge.target is not None:
                error(f"{path}.target", "must be omitted when 'unsolved' is true")
            if len(edge.locations) != 1:
                error(
                    f"{path}.locations", "unsolved edges require exactly one location"
                )
        elif edge.target is None:
            error(path, "missing 'target' (or set 'unsolved' to true)")
        else:
            check_reference(edge.target, f"{path}.target")
            if (
                edge.kind == EdgeType.MEMBER
                and parent_ids.get(edge.target) == edge.source
            ):
                warning(path, "redundant member edge, nesting already creates it")
        for j, loc in enumerate(edge.locations):
            check_location(loc, f"{path}.locations[{j}]")

    # Local symbols
    for i, local in enumerate(graph.local_symbols):
        path = f"local_symbols[{i}]"
        if not local.name:
            error(f"{path}.name", "must not be empty")
        if not local.locations:
            warning(
                f"{path}.locations", "a local symbol without location is not visible"
            )
        for j, loc in enumerate(local.locations):
            check_location(loc, f"{path}.locations[{j}]")

    return issues


# ------------------------------------------------------------------------ #
# Loading                                                                  #
# ------------------------------------------------------------------------ #


def _apply_color(db: SourcetrailDB, node_id: int, color: NodeColor | None) -> None:
    """Set the colors of a node, if any."""
    if color is not None:
        db.change_node_color(
            node_id,
            fill_color=color.fill or "default",
            border_color=color.border or "default",
            text_color=color.text or "default",
            icon_color=color.icon or "default",
            hatching_color=color.hatching or "default",
        )


def _apply_command(db: SourcetrailDB, node_id: int, command: Command | None) -> None:
    """Set the custom command of a node, if any."""
    if command is not None:
        db.set_custom_command(node_id, command.argv, command.description)


def load_graph(
    graph: Graph, db: SourcetrailDB, base_dir: Path | str | None = None
) -> dict[str, int]:
    """Record a whole graph into a Sourcetrail database.

    The graph is validated first and nothing is recorded if it contains errors.
    Changes are not committed, it is up to the caller to commit the database.

    :param graph: The graph to record
    :param db: The database in which the graph is recorded
    :param base_dir: Directory against which relative paths are resolved
    :return: Mapping between the ids of the graph and the database identifiers
    :raises GraphValidationError: if the graph is invalid
    """
    errors = [i for i in validate(graph, base_dir) if i.severity == "error"]
    if errors:
        raise GraphValidationError(errors)
    base = Path(base_dir) if base_dir is not None else Path(".")
    ids: dict[str, int] = {}

    for node_type, display in graph.node_types.items():
        db.set_node_type(node_type, display.graph_display, display.hover_display)

    for file in graph.files:
        name = file.name or file.path or ""
        if file.path is not None:
            file_id = db.record_file(base / file.path, name, file.indexed, file.hover)
        else:
            file_id = db.record_file_content(
                name, file.content or "", file.indexed, file.hover
            )
        if file.language:
            db.record_file_language(file_id, file.language)
        _apply_color(db, file_id, file.color)
        _apply_command(db, file_id, file.command)
        for err in file.errors:
            db.record_error(
                err.message,
                err.fatal,
                file_id,
                err.start_line,
                err.start_column,
                err.end_line,
                err.end_column,
            )
        ids[file.id] = file_id

    node_ids: dict[int, int] = {}  # id(node) -> database id
    for node, parent, path in graph.iter_nodes():
        node_id = _NODE_RECORDERS[node.kind](
            db,
            name=node.name,
            prefix=node.prefix,
            postfix=node.postfix,
            delimiter=node.delimiter or graph.delimiter,
            parent_id=node_ids[id(parent)] if parent is not None else None,
            is_indexed=node.indexed,
            hover_display=node.hover,
        )
        if node_id is None:
            raise NumbatException(f"{path}: node could not be recorded")
        node_ids[id(node)] = node_id
        if node.id is not None:
            ids[node.id] = node_id

        if node.access is not None:
            _ACCESS_RECORDERS[node.access](db, node_id)
        _apply_color(db, node_id, node.color)
        _apply_command(db, node_id, node.command)
        if node.attached_file is not None:
            attached = node.attached_file
            if attached.path is not None:
                db.associate_file_to_node(
                    node_id, base / attached.path, attached.display_content
                )
            else:
                db.associate_file_content_to_node(
                    node_id, attached.content or "", attached.display_content
                )

    # Record locations once all the files are known
    for node, _, _ in graph.iter_nodes():
        for sym_loc in node.locations:
            _LOCATION_RECORDERS[sym_loc.type](
                db,
                node_ids[id(node)],
                ids[sym_loc.file],
                sym_loc.start_line,
                sym_loc.start_column,
                sym_loc.end_line,
                sym_loc.end_column,
            )

    for edge in graph.edges:
        if edge.unsolved:
            loc = edge.locations[0]
            edge_id = db.record_reference_to_unsolved_symbol(
                ids[edge.source],
                edge.kind,
                ids[loc.file],
                loc.start_line,
                loc.start_column,
                loc.end_line,
                loc.end_column,
                edge.hover,
            )
        else:
            assert edge.target is not None  # checked by validate
            edge_id = _EDGE_RECORDERS[edge.kind](
                db, ids[edge.source], ids[edge.target], edge.hover
            )
            for loc in edge.locations:
                db.record_reference_location(
                    edge_id,
                    ids[loc.file],
                    loc.start_line,
                    loc.start_column,
                    loc.end_line,
                    loc.end_column,
                )
        if edge.color is not None:
            db.change_edge_color(edge_id, edge.color)
        if edge.ambiguous:
            db.record_reference_is_ambiguous(edge_id)

    for local in graph.local_symbols:
        local_id = db.record_local_symbol(local.name)
        for loc in local.locations:
            db.record_local_symbol_location(
                local_id,
                ids[loc.file],
                loc.start_line,
                loc.start_column,
                loc.end_line,
                loc.end_column,
            )

    return ids
