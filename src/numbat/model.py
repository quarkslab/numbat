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

"""Declarative data model describing a whole Numbat graph.

A `Graph` can be written as a JSON file (by hand, by a script or by an LLM)
and then loaded into a Sourcetrail/NumbatUI database with `numbat.loader`
or the `numbat load` command.

The enumerations of `numbat.types` (NodeType, EdgeType, ...) are reused, they
are serialized as lowercase strings derived from their member names
(e.g. `NodeType.NODE_CLASS` <-> `"class"`, `EdgeType.TYPE_USAGE` <-> `"type_usage"`).
"""

import dataclasses
import difflib
import enum
import json
import re
import types
import typing
from dataclasses import MISSING, dataclass, field
from pathlib import Path
from typing import Any

from .exceptions import NumbatException
from .types import (
    ComponentAccessType,
    EdgeType,
    NameHierarchy,
    NodeType,
    SourceLocationType,
)

FORMAT_VERSION = 1

# Where the JSON Schema is published (generated with the documentation)
SCHEMA_URL = "https://quarkslab.github.io/numbat/graph.schema.json"

# ------------------------------------------------------------------------ #
# Enumerations serialization                                               #
# ------------------------------------------------------------------------ #


def enum_to_str(member: enum.Enum) -> str:
    """Return the serialized name of an enum member (e.g. NODE_CLASS -> "class").

    :param member: The enum member to serialize
    :return: Its lowercase name, without the `NODE_` prefix for node types
    """
    return member.name.removeprefix("NODE_").lower()


def str_to_enum(enum_cls: type[enum.Enum], value: str) -> enum.Enum:
    """Return the enum member corresponding to a serialized name.

    :param enum_cls: The enum class
    :param value: The serialized name (cf. `enum_to_str`)
    :return: The corresponding member
    """
    for member in enum_cls:
        if enum_to_str(member) == value:
            return member
    raise KeyError(f"{value} is not a valid {enum_cls.__name__}")


# Subsets of the enumerations that can be used in a graph file
NODE_KINDS = tuple(t for t in NodeType if t != NodeType.NODE_FILE)
EDGE_KINDS = tuple(
    t for t in EdgeType if t not in (EdgeType.UNDEFINED, EdgeType.BUNDLED_EDGES)
)
ACCESS_TYPES = tuple(t for t in ComponentAccessType if t != ComponentAccessType.NONE)
SYMBOL_LOCATION_TYPES = (
    SourceLocationType.TOKEN,
    SourceLocationType.SCOPE,
    SourceLocationType.SIGNATURE,
    SourceLocationType.QUALIFIER,
    SourceLocationType.ATOMIC_RANGE,
)

# ------------------------------------------------------------------------ #
# Colors                                                                   #
# ------------------------------------------------------------------------ #

HEX_COLOR_PATTERN = r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"

# https://www.w3.org/TR/SVG11/types.html#ColorKeywords (+ "transparent")
SVG_COLOR_KEYWORDS = frozenset(
    """aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond
    blue blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue
    cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey
    darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon
    darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet
    deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen
    fuchsia gainsboro ghostwhite gold goldenrod gray grey green greenyellow honeydew
    hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon
    lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
    lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey
    lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine
    mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue
    mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose
    moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid
    palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink
    plum powderblue purple red rosybrown royalblue saddlebrown salmon sandybrown
    seagreen seashell sienna silver skyblue slateblue slategray slategrey snow
    springgreen steelblue tan teal thistle tomato turquoise violet wheat white
    whitesmoke yellow yellowgreen transparent""".split()
)


def is_valid_color(value: str) -> bool:
    """Check that a color is a hex code (#RGB, #RRGGBB, #AARRGGBB) or an SVG keyword.

    :param value: The color to check
    :return: True if the color is supported
    """
    return (
        bool(re.match(HEX_COLOR_PATTERN, value)) or value.lower() in SVG_COLOR_KEYWORDS
    )


# ------------------------------------------------------------------------ #
# Data model                                                               #
# ------------------------------------------------------------------------ #


def _field(description: str, default: Any = MISSING, **metadata: Any) -> Any:
    """Declare a dataclass field with its description (used for the JSON schema).

    Lists and dicts defaults are handled with a default_factory.

    :param description: Description of the field
    :param default: Default value, if the field is optional
    :param metadata: Additional constraints (`values`, `choices`, `color`, `minimum`)
    :return: A dataclass field
    """
    metadata["description"] = description
    if isinstance(default, (list, dict)):
        return field(default_factory=type(default), metadata=metadata)
    return field(default=default, metadata=metadata)


_RANGE_DOC = "Lines and columns are 1-based and inclusive."


@dataclass(kw_only=True)
class Location:
    """A range of text inside one of the graph files."""

    file: str = _field("Id of the file (from `files`) containing the range.")
    start_line: int = _field("Line where the range starts. " + _RANGE_DOC, minimum=1)
    start_column: int = _field(
        "Column where the range starts. " + _RANGE_DOC, minimum=1
    )
    end_line: int = _field("Line where the range ends. " + _RANGE_DOC, minimum=1)
    end_column: int = _field("Column where the range ends. " + _RANGE_DOC, minimum=1)


@dataclass(kw_only=True)
class SymbolLocation(Location):
    """A range of text inside one of the graph files, associated to a node."""

    type: SourceLocationType = _field(
        "What the range represents: `token` the name of the node itself, `scope` its "
        "whole body (e.g. a full function), `signature` its declaration, `qualifier` a "
        "qualifier of its name, `atomic_range` a range that cannot be split.",
        SourceLocationType.TOKEN,
        values=SYMBOL_LOCATION_TYPES,
    )


@dataclass(kw_only=True)
class NodeColor:
    """Colors of a node. Each color is '#RRGGBB' or an SVG color keyword."""

    fill: str | None = _field("Color of the node body.", None, color=True)
    border: str | None = _field("Color of the node border.", None, color=True)
    text: str | None = _field("Color of the node text.", None, color=True)
    icon: str | None = _field("Color of the node icon (if any).", None, color=True)
    hatching: str | None = _field(
        "Color of the node hatching (non-indexed nodes).", None, color=True
    )


@dataclass(kw_only=True)
class Command:
    """A custom command available in the context menu of a node (NumbatUI)."""

    argv: list[str] = _field("Program to run followed by its arguments.")
    description: str = _field("Label of the command in the context menu.", "")


@dataclass(kw_only=True)
class AttachedFile:
    """A file displayed when the node is selected, without creating a file node.

    Exactly one of `path` or `content` must be given.
    """

    path: str | None = _field(
        "Path of an existing file (relative to the graph file directory).", None
    )
    content: str | None = _field("Inline content of the file.", None)
    display_content: bool = _field("Whether the content is displayed.", True)


@dataclass(kw_only=True)
class Node:
    """A node of the graph. Nodes can be nested using `children`."""

    id: str | None = _field(
        "Unique identifier used to reference this node from `edges`. Only required if "
        "the node is referenced. Must be unique among all nodes and files.",
        None,
    )
    kind: NodeType = _field(
        "Kind of the node. It drives the icon and the grouping in the UI. Kinds can be "
        "relabeled with the top-level `node_types`, so pick the ones that fit best and "
        "rename them (e.g. `class` displayed as 'Machine').",
        NodeType.NODE_SYMBOL,
        values=NODE_KINDS,
    )
    name: str = _field("Name of the node, displayed in the graph.")
    prefix: str = _field("Text displayed before the name (e.g. a return type).", "")
    postfix: str = _field("Text displayed after the name (e.g. '(int a)').", "")
    delimiter: str | None = _field(
        "Separator between a node and its children in qualified names. Only allowed on "
        "top-level nodes: children always use the delimiter of their top-level "
        "ancestor. Defaults to the graph `delimiter`.",
        None,
        choices=NameHierarchy.NAME_DELIMITERS,
    )
    indexed: bool = _field(
        "False marks the node as known but not defined in the data (hatched in the "
        "UI).",
        True,
    )
    hover: str = _field(
        "Text displayed in the tooltip when hovering over the node.", ""
    )
    access: ComponentAccessType | None = _field(
        "Access specifier of the node, shown as an icon inside its parent.",
        None,
        values=ACCESS_TYPES,
    )
    color: NodeColor | None = _field("Colors of the node.", None)
    command: Command | None = _field("Custom command of the node context menu.", None)
    attached_file: AttachedFile | None = _field(
        "File displayed when the node is selected.", None
    )
    locations: list[SymbolLocation] = _field(
        "Ranges of the graph files where this node appears.", []
    )
    children: list["Node"] = _field(
        "Nested nodes. Nesting means containment (the child is a member of this node) "
        "and is displayed as boxes inside boxes. Do not add `member` edges for it.",
        [],
    )


@dataclass(kw_only=True)
class Edge:
    """A directed relationship between two nodes (or files)."""

    kind: EdgeType = _field(
        "Kind of the relationship. It drives the look of the edge in the UI.",
        values=EDGE_KINDS,
    )
    source: str = _field("Id of the source node or file.")
    target: str | None = _field(
        "Id of the target node or file. Must be omitted when `unsolved` is true.", None
    )
    unsolved: bool = _field(
        "True if the target could not be resolved. The edge then points to a special "
        "'unsolved symbol' node and requires exactly one location.",
        False,
    )
    hover: str = _field(
        "Text displayed in the tooltip when hovering over the edge.", ""
    )
    color: str | None = _field(
        "Color of the edge ('#RRGGBB' or SVG color keyword).", None, color=True
    )
    ambiguous: bool = _field("Mark the edge as ambiguous.", False)
    locations: list[Location] = _field(
        "Ranges of the graph files where this relationship appears.", []
    )


@dataclass(kw_only=True)
class IndexerError:
    """An error message attached to a range of a file."""

    message: str = _field("Description of the error.")
    fatal: bool = _field("Whether the error is fatal.", False)
    start_line: int = _field("Line where the range starts. " + _RANGE_DOC, 1, minimum=1)
    start_column: int = _field(
        "Column where the range starts. " + _RANGE_DOC, 1, minimum=1
    )
    end_line: int = _field("Line where the range ends. " + _RANGE_DOC, 1, minimum=1)
    end_column: int = _field("Column where the range ends. " + _RANGE_DOC, 1, minimum=1)


@dataclass(kw_only=True)
class File:
    """A text file whose content can be displayed, and referenced by locations.

    Its content is either read from `path` or given inline in `content`.
    """

    id: str = _field(
        "Unique identifier of the file, used by locations and edges. Must be unique "
        "among all nodes and files."
    )
    name: str | None = _field(
        "Name (usually a path) displayed in the UI. Defaults to `path`.", None
    )
    path: str | None = _field(
        "Path of an existing file to read (relative to the graph file directory).", None
    )
    content: str | None = _field("Inline content of the file.", None)
    language: str = _field("Language of the file, used for syntax highlighting.", "")
    indexed: bool = _field(
        "False records the file without its content (it cannot be displayed).", True
    )
    hover: str = _field(
        "Text displayed in the tooltip when hovering over the file.", ""
    )
    color: NodeColor | None = _field("Colors of the file node.", None)
    command: Command | None = _field("Custom command of the file context menu.", None)
    errors: list[IndexerError] = _field("Errors to display in this file.", [])


@dataclass(kw_only=True)
class NodeTypeDisplay:
    """How a node kind is labeled in the UI."""

    graph_display: str | None = _field(
        "Label of the kind in the overview (plural, e.g. 'Machines'). An empty string "
        "hides the kind from the overview.",
        None,
    )
    hover_display: str | None = _field(
        "Label of the kind in tooltips (singular, e.g. 'machine').", None
    )


@dataclass(kw_only=True)
class LocalSymbol:
    """A symbol local to a scope (e.g. a variable), only shown in the file view."""

    name: str = _field("Name of the local symbol.")
    locations: list[Location] = _field("Ranges where the local symbol appears.")


@dataclass(kw_only=True)
class Graph:
    """A whole graph, loadable into a Sourcetrail/NumbatUI database."""

    format_version: int = _field("Version of this file format.", FORMAT_VERSION)
    delimiter: str = _field(
        "Default separator between a node and its children in qualified names.",
        NameHierarchy.NAME_DELIMITER_CXX,
        choices=NameHierarchy.NAME_DELIMITERS,
    )
    node_types: dict[NodeType, NodeTypeDisplay] = _field(
        "Relabel node kinds (keys are node kinds, or `file`) to fit the data domain.",
        {},
    )
    files: list[File] = _field("Text files of the graph.", [])
    nodes: list[Node] = _field("Top-level nodes of the graph.", [])
    edges: list[Edge] = _field("Relationships between nodes and/or files.", [])
    local_symbols: list[LocalSymbol] = _field("Symbols local to a scope.", [])

    @classmethod
    def from_dict(cls, data: Any) -> "Graph":
        """Build a Graph from its dict representation (e.g. parsed JSON).

        :param data: The dict to decode
        :return: The corresponding Graph
        :raises GraphValidationError: if the data does not follow the model
        """
        issues: list[ValidationIssue] = []
        if isinstance(data, dict):
            # Reference to the JSON Schema (e.g. for editors), not part of the model
            data = {k: v for k, v in data.items() if k != "$schema"}
        graph = _decode(cls, data, "", {}, issues)
        if issues:
            raise GraphValidationError(issues)
        return graph

    @classmethod
    def from_json(cls, text: str) -> "Graph":
        """Build a Graph from a JSON string.

        :param text: The JSON document
        :return: The corresponding Graph
        :raises GraphValidationError: if the JSON is invalid or does not follow the
        model
        """
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise GraphValidationError(
                [ValidationIssue("", f"invalid JSON: {e}")]
            ) from e
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: Path | str) -> "Graph":
        """Read a Graph from a JSON file.

        :param path: The path of the JSON file
        :return: The corresponding Graph
        """
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def to_dict(self) -> dict:
        """Return the dict representation of the graph, omitting default values.

        :return: A JSON serializable dict
        """
        return _encode(self)

    def to_json(self, indent: int | None = 2) -> str:
        """Return the JSON representation of the graph.

        :param indent: JSON indentation
        :return: The JSON document
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: Path | str) -> None:
        """Write the graph in a JSON file.

        :param path: The path of the JSON file
        :return: None
        """
        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    def iter_nodes(self) -> typing.Iterator[tuple[Node, Node | None, str]]:
        """Iterate over all the nodes, parents before children.

        :return: An iterator of (node, parent node or None, path in the document)
        """
        stack: list[tuple[Node, Node | None, str]] = [
            (node, None, f"nodes[{i}]") for i, node in enumerate(self.nodes)
        ]
        stack.reverse()
        while stack:
            node, parent, path = stack.pop()
            yield node, parent, path
            stack.extend(
                (child, node, f"{path}.children[{i}]")
                for i, child in reversed(list(enumerate(node.children)))
            )


# ------------------------------------------------------------------------ #
# Validation issues                                                        #
# ------------------------------------------------------------------------ #


@dataclass
class ValidationIssue:
    """A problem found in a graph document."""

    path: str
    message: str
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        """Return a human (and LLM) readable description of the issue."""
        location = f"{self.path}: " if self.path else ""
        return f"{self.severity}: {location}{self.message}"


class GraphValidationError(NumbatException):
    """Raised when a graph document is invalid, holds all the issues found."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__("\n".join(str(i) for i in issues))


# ------------------------------------------------------------------------ #
# Generic (de)serialization based on type hints                            #
# ------------------------------------------------------------------------ #

_INVALID = object()


def _join(path: str, key: str | int) -> str:
    """Return the path of a key/index inside a document path."""
    if isinstance(key, int):
        return f"{path}[{key}]"
    return f"{path}.{key}" if path else key


def _suggest(value: str, candidates: typing.Iterable[str]) -> str:
    """Return a ' (did you mean ...?)' hint, or an empty string."""
    matches = difflib.get_close_matches(value, list(candidates), n=1)
    return f" (did you mean '{matches[0]}'?)" if matches else ""


def _optional_inner(tp: Any) -> Any | None:
    """Return X for `X | None`, else None."""
    if isinstance(tp, types.UnionType) or typing.get_origin(tp) is typing.Union:
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return None


def _decode(tp: Any, value: Any, path: str, meta: typing.Mapping, issues: list) -> Any:
    """Decode a JSON value according to a type hint, collecting issues.

    :param tp: The expected type
    :param value: The JSON value
    :param path: The path of the value in the document (for error messages)
    :param meta: The metadata of the field holding the value
    :param issues: The list where to append issues
    :return: The decoded value (or _INVALID)
    """
    inner = _optional_inner(tp)
    if inner is not None:
        return None if value is None else _decode(inner, value, path, meta, issues)

    def error(msg: str) -> Any:
        issues.append(ValidationIssue(path, msg))
        return _INVALID

    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        if not isinstance(value, dict):
            return error(f"expected an object, got {type(value).__name__}")
        fields = {f.name: f for f in dataclasses.fields(tp)}
        hints = typing.get_type_hints(tp)
        kwargs = {}
        for key in value:
            if key not in fields:
                error(f"unknown field '{key}'{_suggest(key, fields)}")
        for name, f in fields.items():
            if name not in value:
                if f.default is MISSING and f.default_factory is MISSING:
                    issues.append(
                        ValidationIssue(path, f"missing required field '{name}'")
                    )
                continue
            decoded = _decode(
                hints[name], value[name], _join(path, name), f.metadata, issues
            )
            if decoded is not _INVALID:
                kwargs[name] = decoded
        try:
            return tp(**kwargs)
        except TypeError:  # missing required fields, already reported
            return _INVALID

    origin = typing.get_origin(tp)
    if origin is list:
        if not isinstance(value, list):
            return error(f"expected an array, got {type(value).__name__}")
        (item_tp,) = typing.get_args(tp)
        items = [
            _decode(item_tp, v, _join(path, i), {}, issues) for i, v in enumerate(value)
        ]
        return [v for v in items if v is not _INVALID]

    if origin is dict:
        if not isinstance(value, dict):
            return error(f"expected an object, got {type(value).__name__}")
        key_tp, value_tp = typing.get_args(tp)
        result = {}
        for k, v in value.items():
            key = _decode(key_tp, k, _join(path, k), {}, issues)
            val = _decode(value_tp, v, _join(path, k), {}, issues)
            if key is not _INVALID and val is not _INVALID:
                result[key] = val
        return result

    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        allowed = {enum_to_str(m): m for m in meta.get("values", tuple(tp))}
        if not isinstance(value, str):
            return error(f"expected a string, got {type(value).__name__}")
        if value not in allowed:
            return error(
                f"invalid value '{value}'{_suggest(value, allowed)}, "
                f"expected one of: {', '.join(allowed)}"
            )
        return allowed[value]

    if tp is bool:
        if not isinstance(value, bool):
            return error(f"expected a boolean, got {type(value).__name__}")
        return value

    if tp is int:
        if not isinstance(value, int) or isinstance(value, bool):
            return error(f"expected an integer, got {type(value).__name__}")
        if "minimum" in meta and value < meta["minimum"]:
            return error(f"must be >= {meta['minimum']}, got {value}")
        return value

    if tp is str:
        if not isinstance(value, str):
            return error(f"expected a string, got {type(value).__name__}")
        if "choices" in meta and value not in meta["choices"]:
            return error(
                f"invalid value '{value}', "
                f"expected one of: {', '.join(meta['choices'])}"
            )
        if meta.get("color") and not is_valid_color(value):
            return error(
                f"invalid color '{value}', expected '#RRGGBB' or an SVG color keyword"
            )
        return value

    raise TypeError(f"Unsupported type in model: {tp}")  # pragma: no cover


def _encode(value: Any) -> Any:
    """Encode a model value to JSON compatible types, omitting default values.

    :param value: The value to encode
    :return: The encoded value
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        result = {}
        for f in dataclasses.fields(value):
            v = getattr(value, f.name)
            if f.default is not MISSING and v == f.default:
                continue
            if f.default_factory is not MISSING and v == f.default_factory():
                continue
            result[f.name] = _encode(v)
        return result
    if isinstance(value, enum.Enum):
        return enum_to_str(value)
    if isinstance(value, list):
        return [_encode(v) for v in value]
    if isinstance(value, dict):
        return {_encode(k): _encode(v) for k, v in value.items()}
    return value


# ------------------------------------------------------------------------ #
# JSON Schema                                                              #
# ------------------------------------------------------------------------ #


def _schema(tp: Any, meta: typing.Mapping, defs: dict) -> dict:
    """Return the JSON schema of a type hint, registering dataclasses in defs.

    :param tp: The type hint
    :param meta: The metadata of the field holding the value
    :param defs: The `$defs` of the schema being built
    :return: The JSON schema
    """
    inner = _optional_inner(tp)
    if inner is not None:
        return _schema(inner, meta, defs)

    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        name = tp.__name__
        if name not in defs:
            defs[name] = {}  # placeholder, handles recursive types
            hints = typing.get_type_hints(tp)
            properties, required = {}, []
            for f in dataclasses.fields(tp):
                prop = _schema(hints[f.name], f.metadata, defs)
                if "$ref" in prop:  # description cannot be a sibling of $ref everywhere
                    prop = {"allOf": [prop]}
                prop["description"] = f.metadata["description"]
                if f.default is MISSING and f.default_factory is MISSING:
                    required.append(f.name)
                elif f.default is not MISSING and f.default is not None:
                    prop["default"] = _encode(f.default)
                properties[f.name] = prop
            defs[name] = {
                "type": "object",
                "description": " ".join((tp.__doc__ or "").split()),
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            }
        return {"$ref": f"#/$defs/{name}"}

    origin = typing.get_origin(tp)
    if origin is list:
        (item_tp,) = typing.get_args(tp)
        return {"type": "array", "items": _schema(item_tp, {}, defs)}
    if origin is dict:
        key_tp, value_tp = typing.get_args(tp)
        return {
            "type": "object",
            "propertyNames": _schema(key_tp, {}, defs),
            "additionalProperties": _schema(value_tp, {}, defs),
        }
    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        return {
            "type": "string",
            "enum": [enum_to_str(m) for m in meta.get("values", tuple(tp))],
        }
    if tp is bool:
        return {"type": "boolean"}
    if tp is int:
        schema: dict = {"type": "integer"}
        if "minimum" in meta:
            schema["minimum"] = meta["minimum"]
        return schema
    if tp is str:
        if "choices" in meta:
            return {"type": "string", "enum": list(meta["choices"])}
        if meta.get("color"):
            defs.setdefault(
                "Color",
                {
                    "description": "'#RRGGBB' hex code or SVG color keyword.",
                    "anyOf": [
                        {"type": "string", "pattern": HEX_COLOR_PATTERN},
                        {"type": "string", "enum": sorted(SVG_COLOR_KEYWORDS)},
                    ],
                },
            )
            return {"$ref": "#/$defs/Color"}
        return {"type": "string"}
    raise TypeError(f"Unsupported type in model: {tp}")  # pragma: no cover


def json_schema() -> dict:
    """Return the JSON Schema (draft 2020-12) of a graph document.

    It can be given to an LLM (e.g. as a structured output or tool input schema)
    so that it produces a valid graph file.

    :return: The JSON Schema as a dict
    """
    defs: dict = {}
    root = _schema(Graph, {}, defs)
    graph_schema = defs.pop(root["$ref"].split("/")[-1])
    graph_schema["properties"] = {
        "$schema": {
            "type": "string",
            "description": f"Optional reference to this schema: {SCHEMA_URL}",
        },
        **graph_schema["properties"],
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_URL,
        "title": "Numbat graph",
        **graph_schema,
        "$defs": defs,
    }
