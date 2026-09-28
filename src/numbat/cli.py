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

"""Command line interface of Numbat: create databases from graph files."""

import argparse
import json
import sys
from importlib import resources
from pathlib import Path

from . import __version__
from .api import SourcetrailDB
from .loader import load_graph, validate
from .model import Graph, GraphValidationError, ValidationIssue, json_schema


def _read_graph(source: str) -> tuple[Graph | None, list[ValidationIssue], Path]:
    """Read, decode and validate a graph file.

    :param source: Path of the graph file, or '-' for stdin
    :return: The graph (None if it could not be decoded), all the issues found
    and the directory against which relative paths are resolved
    """
    if source == "-":
        text, base_dir = sys.stdin.read(), Path.cwd()
    else:
        path = Path(source)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            return (
                None,
                [ValidationIssue("", f"cannot read {source}: {e.strerror}")],
                path,
            )
        base_dir = path.parent
    try:
        graph = Graph.from_json(text)
    except GraphValidationError as e:
        return None, e.issues, base_dir
    return graph, validate(graph, base_dir), base_dir


def _print_issues(issues: list[ValidationIssue]) -> None:
    """Print issues on stderr."""
    for issue in issues:
        print(issue, file=sys.stderr)


def _cmd_validate(args: argparse.Namespace) -> int:
    graph, issues, _ = _read_graph(args.graph)
    valid = graph is not None and not any(i.severity == "error" for i in issues)
    if args.json:
        print(
            json.dumps(
                {
                    "valid": valid,
                    "issues": [
                        {"severity": i.severity, "path": i.path, "message": i.message}
                        for i in issues
                    ],
                },
                indent=2,
            )
        )
    else:
        _print_issues(issues)
        if valid:
            print(f"{args.graph} is valid")
    return 0 if valid else 1


def _cmd_load(args: argparse.Namespace) -> int:
    graph, issues, base_dir = _read_graph(args.graph)
    _print_issues(issues)
    if graph is None or any(i.severity == "error" for i in issues):
        print("error: the graph is invalid, nothing was created", file=sys.stderr)
        return 1

    if SourcetrailDB.exists(args.output) and not args.force:
        print(
            f"error: {args.output} already exists (use --force to overwrite it)",
            file=sys.stderr,
        )
        return 1

    db = SourcetrailDB.open(args.output, clear=True)
    try:
        load_graph(graph, db, base_dir)
        db.commit()
    except Exception as e:
        # Do not leave a half-filled database behind
        db.close()
        db.path.unlink(missing_ok=True)
        db.path.with_suffix(SourcetrailDB.SOURCETRAIL_PROJECT_EXT).unlink(
            missing_ok=True
        )
        print(f"error: {e}", file=sys.stderr)
        return 1
    db.close()

    nb_nodes = sum(1 for _ in graph.iter_nodes())
    print(
        f"Created {db.path} ({len(graph.files)} files, {nb_nodes} nodes, "
        f"{len(graph.edges)} edges)"
    )
    print(
        f"Open {db.path.with_suffix(SourcetrailDB.SOURCETRAIL_PROJECT_EXT)} "
        "with NumbatUI"
    )
    return 0


def _cmd_schema(args: argparse.Namespace) -> int:
    schema = json.dumps(json_schema(), indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(schema, encoding="utf-8")
    else:
        sys.stdout.write(schema)
    return 0


def _cmd_guide(args: argparse.Namespace) -> int:
    sys.stdout.write(
        resources.files("numbat").joinpath("graph_guide.md").read_text("utf-8")
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point of the `numbat` command.

    :param argv: Command line arguments (defaults to sys.argv)
    :return: The exit code
    """
    parser = argparse.ArgumentParser(
        prog="numbat",
        description="Create Sourcetrail/NumbatUI databases from JSON graph files.",
    )
    parser.add_argument("--version", action="version", version=f"numbat {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("load", help="create a database from a graph file")
    p.add_argument("graph", help="graph JSON file ('-' to read stdin)")
    p.add_argument(
        "-o", "--output", required=True, help="database to create (.srctrldb is added)"
    )
    p.add_argument(
        "-f", "--force", action="store_true", help="overwrite the database if it exists"
    )
    p.set_defaults(func=_cmd_load)

    p = subparsers.add_parser("validate", help="check a graph file")
    p.add_argument("graph", help="graph JSON file ('-' to read stdin)")
    p.add_argument("--json", action="store_true", help="print the result as JSON")
    p.set_defaults(func=_cmd_validate)

    p = subparsers.add_parser("schema", help="print the JSON Schema of graph files")
    p.add_argument("-o", "--output", help="write the schema in this file")
    p.set_defaults(func=_cmd_schema)

    p = subparsers.add_parser(
        "guide", help="print the graph format guide (e.g. to give to an LLM)"
    )
    p.set_defaults(func=_cmd_guide)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
