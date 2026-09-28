"""Generate the code reference pages and navigation."""

import json
from pathlib import Path

import mkdocs_gen_files

from numbat.model import json_schema

nav = mkdocs_gen_files.Nav()

excluded = ['__init__.py', 'exceptions.py']  # files from which doc will not be generated

for path in filter(lambda p: p.name not in excluded,
                   Path("src").rglob("*.py")):
    module_path = path.relative_to("src").with_suffix("")
    doc_path = path.relative_to("src").with_suffix(".md")
    full_doc_path = Path("intern_dev", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w+") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# Publish the JSON Schema of graph files (numbat.model.SCHEMA_URL)
with mkdocs_gen_files.open("graph.schema.json", "w") as fd:
    json.dump(json_schema(), fd, indent=2)
