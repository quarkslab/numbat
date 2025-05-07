# -*- coding: utf-8 -*-

#  Copyright 2023-2025 Quarkslab
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


"""Manipulation of Sqlite DB used by Numbat."""

import sqlite3

from .exceptions import DBException, NumbatException
from .types import (
    ComponentAccess,
    ComponentAccessType,
    Edge,
    EdgeType,
    Element,
    ElementComponent,
    ElementComponentType,
    Error,
    File,
    FileContent,
    LocalSymbol,
    Node,
    NodeDisplay,
    NodeFile,
    NodeType,
    Occurrence,
    SourceLocation,
    SourceLocationType,
    Symbol,
    SymbolType,
)

# ------------------------------------------------------------------------ #
# Data Access Object (DAO) for Sourcetrail database                        #
# ------------------------------------------------------------------------ #


class SqliteHelper(object):
    """Helper class for sqlite operation."""

    @staticmethod
    def connect(path: str) -> sqlite3.Connection:
        """Connect method to avoid relying directly on sqlite module method.

        :param path: The path to the database, if the path doesn't point
        to an existing file, a new database file will be created
        :return: A connection handle that can be used for future
        operation on the database
        """
        try:
            res = sqlite3.connect(path)
        except sqlite3.Error as e:
            raise DBException(f"Error while connecting to DB: {e}") from e
        return res

    @staticmethod
    def exec(
        database: sqlite3.Connection, request: str, parameters: tuple = ()
    ) -> int | None:
        """Execute the sqlite request without returning the result.

        :param database: A database handle
        :param request: The SQL request to execute
        :param parameters: A tuple containing values for the bind
        parameters of the SQL request (if any)
        :return: The id of the last modified row (useful in case insertion)
        """
        if not database:
            raise DBException("Invalid database handle")

        try:
            cur = database.cursor()
            cur.execute(request, parameters)
            cur.close()
        except sqlite3.Error as e:
            raise DBException(f"Error while excuting request to DB: {e}") from e
        return cur.lastrowid

    @staticmethod
    def fetch(
        database: sqlite3.Connection, request: str, parameters: tuple = ()
    ) -> list:
        """Return the result of the sqlite request as list.

        :param database: A database handle
        :param request: The SQL request to execute
        :param parameters: A tuple containing values for the bind
        parameters of the SQL request (if any)
        :return: A list containing the results of the SQL request
        """
        if not database:
            raise Exception("Invalid database handle")

        try:
            cur = database.cursor()
            cur.execute(request, parameters)
            result = cur.fetchall()
            cur.close()
        except sqlite3.Error as e:
            raise DBException(
                f"Error while excuting a request to DB and fetching result: {e}"
            ) from e

        return result


class ElementDAO(object):
    """To manipulate Element objects, insert and remove them from a sqlite database."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the element table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE IF NOT EXISTS element(
                id INTEGER,                         
                PRIMARY KEY(id));""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the element table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.element;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: Element) -> int:
        """Insert a new Element inside the element table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted element
        """
        # The 'obj' parameter is not used because we need to create a identifier
        # that does not already exists in the database. So instead, we insert
        # NULL and the database does the rest.
        # The 'obj' parameter is present to add some consistency with the
        # rest of the API and also for futur proof consideration.
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO element(id) VALUES (NULL);""",
        )

        if res is None:
            raise NumbatException("New element creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: Element) -> None:
        """Delete an Element from the element table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM element WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Elements from the element table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM element;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> Element:
        """Return an element from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the element to retrieve
        :return: A Element object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM element WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            return Element(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: Element) -> None:
        """Update an Element inside the element table.

        :param database: A database handle
        :param obj: The Element object to update
        :return: None
        """
        # Since the Element object does only contain a primary key
        # it can't be updated
        pass

    @staticmethod
    def list(database: sqlite3.Connection) -> list[Element]:
        """Return the list of all the elements from the element table.

        :param database: A database handle
        :return: The list of Elements
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM element;""",
        )

        result = list()
        for row in rows:
            result.append(Element(*row))

        return result


class ElementComponentDAO(object):
    """To manipulate ElementComponent, insert and remove them from a sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the element_component table of the database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE IF NOT EXISTS element_component(
                id INTEGER, 
                element_id INTEGER, 
                type INTEGER, 
                data TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the element_component table of the Sourcetrail database if it exists.

        :param database: A database handle
        :return: Nonedatabase only if it exists.

        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.element_component;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: ElementComponent) -> int:
        """Insert a new ElementComponent inside the element_component table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted element
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO element_component(
                id, element_id, type, data
            ) VALUES(NULL, ?, ?, ?);""",
            (obj.elem_id, obj.type.value, obj.data),
        )
        if res is None:
            raise NumbatException("New element component creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: ElementComponent) -> None:
        """Delete an ElementComponent from the element_component table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM element_component WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all ElementComponents from the element_component table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM element_component;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> ElementComponent:
        """Return a ElementComponent from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the element_component to retrieve
        :return: A ElementComponent object that reflect the content inside the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM element_component WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            id_, element_id, type_, data = out[0]
            return ElementComponent(id_, element_id, ElementComponentType(type_), data)
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: ElementComponent) -> None:
        """Update an ElementComponent inside the element_component table.

        :param database: A database handle
        :param obj: The Element object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE element_component SET
                element_id = ?, 
                type = ?, 
                data = ?
            WHERE
                id = ?;""",
            (obj.elem_id, obj.type.value, obj.data, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[ElementComponent]:
        """Return the list of all the elements from the element_component table.

        :param database: A database handle
        :return: The list of ElementComponents
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM element_component;""",
        )

        result = list()
        for row in rows:
            id_, element_id, type_, data = row
            result.append(
                ElementComponent(id_, element_id, ElementComponentType(type_), data)
            )

        return result


class EdgeDAO(object):
    """To manipulate Edge  objects, insert and remove them from a sqlite database."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the edge table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE IF NOT EXISTS edge(
                id INTEGER NOT NULL, 
                type INTEGER NOT NULL, 
                source_node_id INTEGER NOT NULL, 
                target_node_id INTEGER NOT NULL, 
                color TEXT, 
                hover_display TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE, 
                FOREIGN KEY(source_node_id) REFERENCES node(id) ON DELETE CASCADE, 
                FOREIGN KEY(target_node_id) REFERENCES node(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the edge table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.edge;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: Edge) -> int:
        """Insert a new Edge inside the edge table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted element
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO edge(
                id, type, source_node_id, target_node_id, hover_display
            ) VALUES(?, ?, ?, ?, ?);""",
            (obj.id, obj.type.value, obj.src, obj.dst, obj.hover_display),
        )
        if res is None:
            raise NumbatException("New edge creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: Edge) -> None:
        """Delete an Edge from the edge table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM edge WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Edges from the edge table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM edge;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> Edge:
        """Return an Edge from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the element to retrieve
        :return: A Edge object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
SELECT id, type, source_node_id, target_node_id, hover_display FROM edge WHERE id = ?;\
""",
            (elem_id,),
        )

        if len(out) == 1:
            id_, type_, src, dst, hover_display = out[0]
            return Edge(id_, EdgeType(type_), src, dst, hover_display)
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: Edge) -> None:
        """Update an Edge inside the element table.

        :param database: A database handle
        :param obj: The Edge object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE edge SET
                type = ?, 
                source_node_id = ?,
                target_node_id = ?
            WHERE
                id = ?;""",
            (obj.type.value, obj.src, obj.dst, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[Edge]:
        """Return the list of all the elements from the edge table.

        :param database: A database handle
        :return: The list of Edges
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM edge;""",
        )

        result = list()
        for row in rows:
            id_, type_, src, dst = row
            result.append(Edge(id_, EdgeType(type_), src, dst))

        return result

    @staticmethod
    def set_color(database: sqlite3.Connection, id: int, new_color: str) -> None:
        """Set the color of an edge.

        :param database: A database handle
        :param id: Id of the edge to change
        :param new_color: RGB hex code or name of the edge's new color
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE edge SET
                color=?
            WHERE
                id=?;""",
            (new_color, id),
        )


class NodeDAO(object):
    """To manipulate Node  objects, insert and remove them from a sqlite database."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the node table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE IF NOT EXISTS node(
                id INTEGER NOT NULL, 
                type INTEGER NOT NULL, 
                serialized_name TEXT, 
                color TEXT, 
                hover_display TEXT, 
                custom_command TEXT, 
                custom_command_desc TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the node table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.node;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: Node) -> int:
        """Insert a new Node inside the node table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted element
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO node(
                id, type, serialized_name, hover_display 
            ) VALUES(?, ?, ?, ?);""",
            (obj.id, obj.type.value, obj.name, obj.hover_display),
        )
        if res is None:
            raise NumbatException("New node creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: Node) -> None:
        """Delete a Node from the node table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM node WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Nodes from the node table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM node;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> Node:
        """Return a Node from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the element to retrieve
        :return: A Node object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT id, type, serialized_name, hover_display FROM node WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            id_, type_, serialized_name, hover_display = out[0]
            return Node(id_, NodeType(type_), serialized_name, hover_display)
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def get_by_name(database: sqlite3.Connection, name: str) -> Node:
        """Return a Node from the database with the matching serialized_name.

        :param database: A database handle
        :param name: The serialized_name of the element to retrieve
        :return: A Node object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM node WHERE serialized_name = ? LIMIT 1;""",
            (name,),
        )

        if len(out) == 1:
            id_, type_, serialized_name = out[0]
            return Node(id_, NodeType(type_), serialized_name)
        elif len(out) == 0:
            raise KeyError(f"{name} doest not correspond to a registered object")
        else:
            raise LookupError(f"Several objects match name '{name}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: Node) -> None:
        """Update a Node inside the node table.

        :param database: A database handle
        :param obj: The Node object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE node SET
                type = ?, 
                serialized_name = ?
            WHERE
                id = ?;""",
            (obj.type.value, obj.name, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[Node]:
        """Return the list of all the elements from the node table.

        :param database: A database handle
        :return: The list of Nodes
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM node;""",
        )

        result = list()
        for row in rows:
            id_, type_, serialized_name = row
            result.append(Node(id_, NodeType(type_), serialized_name))

        return result

    @staticmethod
    def set_color(database: sqlite3.Connection, id: int, new_color: str) -> None:
        """Set the color of a node.

        :param database: A database handle
        :param id: Id of the node to modify
        :param new_color: RGB hex code or name of the node's new color
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE node SET
                color=?
            WHERE
                id=?;""",
            (new_color, id),
        )

    @staticmethod
    def set_custom_command(
        database: sqlite3.Connection, id: int, custom_command: tuple
    ) -> None:
        """Set a custom command for a node in its context menu.

        :param database: A database handle
        :param id: Id of the node to modify
        :param custom_command: The command to execute (with args) and its description
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE node SET
                custom_command=?,
                custom_command_desc=?
            WHERE
                id=?;""",
            (custom_command[0], custom_command[1], id),
        )


class NodeTypeDAO(object):
    """Handle Sourcetrail's internal node types."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the node type table if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            CREATE TABLE IF NOT EXISTS node_type(
                id INTEGER NOT NULL, 
                graph_display TEXT, 
                hover_display TEXT, 
                PRIMARY KEY(id)
            );""",
        )
        NodeTypeDAO.init(database)

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.node_type;""",
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all entries from the node_type table, reset them to default values.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM node_type;""",
        )
        NodeTypeDAO.init(database)

    @staticmethod
    def init(database: sqlite3.Connection) -> None:
        """Load the default values for each node type.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """INSERT OR IGNORE INTO node_type(id,graph_display,hover_display) VALUES
            (1, 'Symbols', 'symbol'),
            (2, 'Types', 'type'),
            (4, '', 'built-in type'),
            (8, 'Modules', 'module'),
            (16, 'Namespaces', 'namespace'),
            (32, 'Packages', 'package'),
            (64, 'Structs', 'struct'),
            (128, 'Classes', 'class'),
            (256, 'Interfaces', 'interface'),
            (512, 'Annotations', 'annotation'),
            (1024, 'Global variables', 'global variable'),
            (2048, '', 'field'),
            (4096, 'Functions', 'function'),
            (8192, '', 'method'),
            (16384, 'Enums', 'enum'),
            (32768, '', 'enum constant'),
            (65536, 'Typedefs', 'typedef'),
            (131072, 'Type parameters', 'type parameter'),
            (262144, 'Files', 'file'),
            (524288, 'Macros', 'macro'),
            (1048576, 'Unions', 'union');""",
        )

    @staticmethod
    def get_by_id(database: sqlite3.Connection, _id: NodeType) -> NodeDisplay:
        """Get an element from the database with the specified id.

        :param database: A database handle
        :param _id: the id of the object to return
        :return: The object with the specified id.
        """
        out = SqliteHelper.fetch(
            database,
            """
                           SELECT * FROM node_type WHERE id=? LIMIT 1;""",
            (_id.value,),
        )
        if len(out) == 1:
            id, graph_display, hover_display = out[0]
            return NodeDisplay(id, graph_display, hover_display)
        elif len(out) == 0:
            raise KeyError(f"{_id.value} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{_id.value}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: NodeDisplay) -> None:
        """Change the display text of an internal node type.

        :param database: A database handle
        :param obj: the type to change
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE node_type SET
                graph_display=?,
                hover_display=? 
            WHERE
                id=?;""",
            (obj.graph_display, obj.hover_display, obj.id.value),
        )


class SymbolDAO(object):
    """To manipulate Symbol  objects, insert and remove them from a sqlite database."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the symbol table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE symbol(
                id INTEGER NOT NULL, 
                definition_kind INTEGER NOT NULL, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the symbol table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.symbol;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: Symbol) -> int:
        """Insert a new Symbol inside the symbol table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted symbol
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO symbol(
                id, definition_kind 
            ) VALUES(?, ?);""",
            (obj.id, obj.definition_kind.value),
        )
        if res is None:
            raise NumbatException("New symbol creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: Symbol) -> None:
        """Delete a Symbol from the symbol table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM symbol WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Symbols from the symbol table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM symbol;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> Symbol:
        """Return a symbol from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the symbol to retrieve
        :return: A Symbol object that reflect the content inside the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM symbol WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            id_, type_ = out[0]
            return Symbol(id_, SymbolType(type_))
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: Symbol) -> None:
        """Update a Symbol inside the symbol table.

        :param database: A database handle
        :param obj: The Symbol object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE symbol SET
                definition_kind = ?
            WHERE
                id = ?;""",
            (obj.definition_kind.value, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[Symbol]:
        """Return the list of all the symbols from the symbol table.

        :param database: A database handle
        :return: The list of Symbols
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM symbol;""",
        )

        result = list()
        for row in rows:
            id_, type_ = row
            result.append(Symbol(id_, SymbolType(type_)))

        return result


class FileDAO(object):
    """To manipulate File  objects, insert and remove them from a sqlite database."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the file table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE file(
                id INTEGER NOT NULL, 
                path TEXT, 
                language TEXT, 
                modification_time TEXT, 
                indexed INTEGER, 
                complete INTEGER, 
                line_count INTEGER, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES node(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the file table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.file;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: File) -> int:
        """Insert a new File inside the file table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted file
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO file(
                id, path, language, modification_time, indexed, complete, line_count 
            ) VALUES(?, ?, ?, ?, ?, ?, ?);""",
            (
                obj.id,
                obj.path,
                obj.language,
                obj.modification_time,
                obj.indexed,
                obj.complete,
                obj.line_count,
            ),
        )
        if res is None:
            raise NumbatException("New file creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: File) -> None:
        """Delete a File from the file table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM file WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Files from the file table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM file;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> File:
        """Return a file from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the file to retrieve
        :return: A File object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM file WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            return File(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: File) -> None:
        """Update a File inside the file table.

        :param database: A database handle
        :param obj: The File object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE file SET
                path = ?,
                language = ?,
                modification_time = ?,
                indexed = ?,
                complete = ?,
                line_count = ? 
            WHERE
                id = ?;""",
            (
                obj.path,
                obj.language,
                obj.modification_time,
                obj.indexed,
                obj.complete,
                obj.line_count,
                obj.id,
            ),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[File]:
        """Return the list of all the files from the file table.

        :param database: A database handle
        :return: The list of Files
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM file;""",
        )

        result = list()
        for row in rows:
            result.append(File(*row))

        return result


class FileContentDAO(object):
    """To manipulate FileContent  objects, insert and remove them from a sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the filecontent table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE filecontent(
                id INTEGER, 
                content TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES file(id)ON DELETE CASCADE ON UPDATE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the filecontent table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.filecontent;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: FileContent) -> int:
        """Insert a new FileContent inside the filecontent table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted filecontent
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO filecontent(
                id, content 
            ) VALUES(?, ?);""",
            (obj.id, obj.content),
        )
        if res is None:
            raise NumbatException("New filecontent creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: FileContent) -> None:
        """Delete an FileContent from the filecontent table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM filecontent WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all FileContents from the filecontent table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM filecontent;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> FileContent:
        """Return a filecontent from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the filecontent to retrieve
        :return: A FileContent object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM filecontent WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            return FileContent(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: FileContent) -> None:
        """Update an FileContent inside the filecontent table.

        :param database: A database handle
        :param obj: The FileContent object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE filecontent SET
                content = ? 
            WHERE
                id = ?;""",
            (obj.content, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[FileContent]:
        """Return the list of all the filecontents from the filecontent table.

        :param database: A database handle
        :return: The list of FileContents
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM filecontent;""",
        )

        result = list()
        for row in rows:
            result.append(FileContent(*row))

        return result


class NodeFileDAO(object):
    """To manipulate NodeFile  objects, insert and remove them from a sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the node_file table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            CREATE TABLE node_file(
                file_id INTEGER NOT NULL,
                file_name TEXT,
                display_content INTEGER, 
                PRIMARY KEY(file_id),
                FOREIGN KEY(file_id) REFERENCES node(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the node_file table of the Sourcetrail database if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS node_file;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: NodeFile) -> int:
        """Insert a new NodeFile inside the node_file table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted node_file
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO node_file(
                file_id, file_name, display_content
            ) VALUES(?, ?, ?);""",
            (obj.id, obj.file_name, int(obj.display_content)),
        )
        if res is None:
            raise NumbatException("New node file creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: NodeFile) -> None:
        """Delete an NodeFile from the node_file table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM node_file WHERE file_id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all NodeFiles from the node_file table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM node_file;""",
        )


class LocalSymbolDAO(object):
    """To manipulate LocalSymbol  objects, insert and remove them from a sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the local_symbol table of the Sourcetrail db if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE local_symbol(
                id INTEGER NOT NULL, 
                name TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the local_symbol table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.local_symbol;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: LocalSymbol) -> int:
        """Insert a new LocalSymbol inside the local_symbol table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted local_symbol
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO local_symbol(
                id, name 
            ) VALUES(?, ?);""",
            (obj.id, obj.name),
        )
        if res is None:
            raise NumbatException("New local symbol creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: LocalSymbol) -> None:
        """Delete an LocalSymbol from the local_symbol table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM local_symbol WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all LocalSymbols from the local_symbol table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM local_symbol;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> LocalSymbol:
        """Return a local_symbol from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the local_symbol to retrieve
        :return: A LocalSymbol object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM local_symbol WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            return LocalSymbol(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def get_from_name(database: sqlite3.Connection, name: str) -> LocalSymbol:
        """Return a local_symbol from the database with the matching name.

        :param database: A database handle
        :param name: The name of the local_symbol to retrieve
        :return: A LocalSymbol object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM local_symbol WHERE name = ? LIMIT 1;""",
            (name,),
        )

        if len(out) == 1:
            return LocalSymbol(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{name} doest not correspond to a registered object")
        else:
            raise LookupError(f"Several objects match name '{name}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: LocalSymbol) -> None:
        """Update an LocalSymbol inside the local_symbol table.

        :param database: A database handle
        :param obj: The LocalSymbol object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE local_symbol SET
                name = ? 
            WHERE
                id = ?;""",
            (obj.name, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[LocalSymbol]:
        """Return the list of all the local_symbols from the local_symbol table.

        :param database: A database handle
        :return: The list of LocalSymbols
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM local_symbol;""",
        )

        result = list()
        for row in rows:
            result.append(LocalSymbol(*row))

        return result


class SourceLocationDAO(object):
    """To manipulate SourceLocation objects, insert and remove them from a sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the source_location table of the Sourcetrail db if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE source_location(
                id INTEGER NOT NULL, 
                file_node_id INTEGER, 
                start_line INTEGER, 
                start_column INTEGER, 
                end_line INTEGER, 
                end_column INTEGER, 
                type INTEGER, 
                PRIMARY KEY(id), 
                FOREIGN KEY(file_node_id) REFERENCES node(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the source_location table of the Sourcetrail db only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.source_location;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: SourceLocation) -> int:
        """Insert a new SourceLocation inside the source_location table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted source_location
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO source_location(
                id, file_node_id, start_line, start_column, end_line, end_column, type 
            ) VALUES(NULL, ?, ?, ?, ?, ?, ?);""",
            (
                obj.file_node_id,
                obj.start_line,
                obj.start_column,
                obj.end_line,
                obj.end_column,
                obj.type.value,
            ),
        )
        if res is None:
            raise NumbatException("New source location creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: SourceLocation) -> None:
        """Delete an SourceLocation from the source_location table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM source_location WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all SourceLocations from the source_location table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM source_location;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> SourceLocation:
        """Return a source_location from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the source_location to retrieve
        :return: A SourceLocation object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM source_location WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            id_, fid, sl, sc, el, ec, type_ = out[0]
            return SourceLocation(id_, fid, sl, sc, el, ec, SourceLocationType(type_))
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: SourceLocation) -> None:
        """Update an SourceLocation inside the source_location table.

        :param database: A database handle
        :param obj: The SourceLocation object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE source_location SET
                file_node_id = ?,
                start_line = ?,
                start_column = ?,
                end_line = ?,
                end_column = ?,
                type = ? 
            WHERE
                id = ?;""",
            (
                obj.file_node_id,
                obj.start_line,
                obj.start_column,
                obj.end_line,
                obj.end_column,
                obj.type.value,
                obj.id,
            ),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[SourceLocation]:
        """Return the list of all the source_locations from the source_location table.

        :param database: A database handle
        :return: The list of SourceLocations
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM source_location;""",
        )

        result = list()
        for row in rows:
            id_, fid, sl, sc, el, ec, type_ = row
            result.append(
                SourceLocation(id_, fid, sl, sc, el, ec, SourceLocationType(type_))
            )

        return result


class OccurrenceDAO(object):
    """To manipulate Occurrence  objects, insert and remove them from a sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the occurrence table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE occurrence(
                element_id INTEGER NOT NULL, 
                source_location_id INTEGER NOT NULL, 
                PRIMARY KEY(element_id, source_location_id), 
                FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE, 
                FOREIGN KEY(source_location_id) REFERENCES source_location(id) 
                    ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the occurrence table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.occurrence;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: Occurrence) -> int:
        """Insert a new Occurrence inside the occurrence table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted occurrence
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO occurrence(
                element_id, source_location_id 
            ) VALUES(?, ?);""",
            (obj.element_id, obj.source_location_id),
        )
        if res is None:
            raise NumbatException("New occurence creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: Occurrence) -> None:
        """Delete an Occurrence from the occurrence table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM occurrence WHERE element_id = ?;""",
            (obj.element_id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Occurrences from the occurrence table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM occurrence;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> Occurrence:
        """Return an occurrence from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the occurrence to retrieve
        :return: A Occurrence object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM occurrence WHERE element_id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            return Occurrence(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: Occurrence) -> None:
        """Update an Occurrence inside the occurrence table.

        :param database: A database handle
        :param obj: The Occurrence object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE occurrence SET
                source_location_id = ? 
            WHERE
                element_id = ?;""",
            (obj.source_location_id, obj.element_id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[Occurrence]:
        """Return the list of all the occurrences from the occurrence table.

        :param database: A database handle
        :return: The list of Occurrences
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM occurrence;""",
        )

        result = list()
        for row in rows:
            result.append(Occurrence(*row))

        return result


class ComponentAccessDAO(object):
    """To manipulate ComponentAccess objects, insert and remove them from  sqlite db."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the component_access table of the Sourcetrail db if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE component_access(
                node_id INTEGER NOT NULL, 
                type INTEGER NOT NULL, 
                PRIMARY KEY(node_id), 
                FOREIGN KEY(node_id) REFERENCES node(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the component_access table of the Sourcetrail db only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.component_access;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: ComponentAccess) -> int:
        """Insert a new ComponentAccess inside the component_access table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted component_access
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO component_access(
                node_id, type 
            ) VALUES(?, ?);""",
            (obj.node_id, obj.type.value),
        )
        if res is None:
            raise NumbatException("New component access creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: ComponentAccess) -> None:
        """Delete an ComponentAccess from the component_access table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM component_access WHERE node_id = ?;""",
            (obj.node_id,),
        )

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all ComponentAccess from the component_access table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM component_access;""",
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> ComponentAccess:
        """Return a component_access from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the component_access to retrieve
        :return: A ComponentAccess object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM component_access WHERE node_id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            node_id, type_ = out[0]
            return ComponentAccess(node_id, ComponentAccessType(type_))
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def update(database: sqlite3.Connection, obj: ComponentAccess) -> None:
        """Update an ComponentAccess inside the component_access table.

        :param database: A database handle
        :param obj: The ComponentAccess object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE component_access SET
                type = ? 
            WHERE
                node_id = ?;""",
            (obj.type.value, obj.node_id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[ComponentAccess]:
        """Return the list of all the component_access from the component_access table.

        :param database: A database handle
        :return: The list of ComponentAccess
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM component_access;""",
        )

        result = list()
        for row in rows:
            node_id, type_ = row
            result.append(ComponentAccess(node_id, ComponentAccessType(type_)))

        return result


class ErrorDAO(object):
    """To manipulate Error  objects, insert and remove them from a sqlite database."""

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the error table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE error(
                id INTEGER NOT NULL, 
                message TEXT, 
                fatal INTEGER NOT NULL, 
                indexed INTEGER NOT NULL, 
                translation_unit TEXT, 
                PRIMARY KEY(id), 
                FOREIGN KEY(id) REFERENCES element(id) ON DELETE CASCADE
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the error table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.error;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, obj: Error) -> int:
        """Insert a new Error inside the error table.

        :param database: A database handle
        :param obj: The object to insert
        :return: The id of the inserted error
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO error(
                id, message, fatal, indexed, translation_unit 
            ) VALUES(?, ?, ?, ?, ?);""",
            (obj.id, obj.message, obj.fatal, obj.indexed, obj.translation_unit),
        )
        if res is None:
            raise NumbatException("New error creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, obj: Error) -> None:
        """Delete an Error from the error table.

        :param database: A database handle
        :param obj: The object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM error WHERE id = ?;""",
            (obj.id,),
        )

    @staticmethod
    def get(database: sqlite3.Connection, elem_id: int) -> Error:
        """Return an error from the database with the matching id.

        :param database: A database handle
        :param elem_id: The id of the error to retrieve
        :return: A Error object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM error WHERE id = ?;""",
            (elem_id,),
        )

        if len(out) == 1:
            return Error(*out[0])
        elif len(out) == 0:
            raise KeyError(f"{elem_id} doest not correspond to a registered id")
        else:
            raise LookupError(f"Several objects match id '{elem_id}")

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Errors from the error table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM error;""",
        )

    @staticmethod
    def update(database: sqlite3.Connection, obj: Error) -> None:
        """Update an Error inside the error table.

        :param database: A database handle
        :param obj: The Error object to update
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE error SET
                message = ?,
                fatal = ?,
                indexed = ?,
                translation_unit = ?
            WHERE
                id = ?;""",
            (obj.message, obj.fatal, obj.indexed, obj.translation_unit, obj.id),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[Error]:
        """Return the list of all the errors from the error table.

        :param database: A database handle
        :return: The list of Errors
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM error;""",
        )

        result = list()
        for row in rows:
            result.append(Error(*row))

        return result


class MetaDAO(object):
    """To manipulate Meta information, insert and remove them from a sqlite database.

    There is no Meta object but a simple key, value pair can be used.
    """

    @staticmethod
    def create_table(database: sqlite3.Connection) -> None:
        """Create the meta table of the Sourcetrail database if it doesn't exist.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """    
            CREATE TABLE meta(
                id INTEGER, 
                key TEXT, 
                value TEXT, 
                PRIMARY KEY(id)
            );""",
        )

    @staticmethod
    def delete_table(database: sqlite3.Connection) -> None:
        """Delete the meta table of the Sourcetrail database only if it exists.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DROP TABLE IF EXISTS main.meta;""",
        )

    @staticmethod
    def new(database: sqlite3.Connection, key: str, value: str) -> int:
        """Insert a new Meta inside the meta table.

        :param database: A database handle
        :param key: The key to insert
        :param value: The value to insert
        :return: The id of the inserted meta
        """
        res = SqliteHelper.exec(
            database,
            """
            INSERT INTO meta(
                id, key, value  
            ) VALUES(NULL, ?, ?);""",
            (key, value),
        )
        if res is None:
            raise NumbatException("New meta creation failed.")
        else:
            return res

    @staticmethod
    def delete(database: sqlite3.Connection, id_: int) -> None:
        """Delete a Meta from the meta table.

        :param database: A database handle
        :param id_: The identifier of the object to delete
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM meta WHERE id = ?;""",
            (id_,),
        )

    @staticmethod
    def get(database: sqlite3.Connection, id_: int) -> tuple[int, str, str]:
        """Return a meta from the database with the matching id.

        :param database: A database handle
        :param id_: The id of the meta to retrieve
        :return: A Meta object that reflect the content inside
        the database
        """
        out = SqliteHelper.fetch(
            database,
            """
            SELECT id, key, value FROM meta WHERE id = ?;""",
            (id_,),
        )
        return tuple(out[0])

    @staticmethod
    def clear(database: sqlite3.Connection) -> None:
        """Delete all Metas from the meta table.

        :param database: A database handle
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            DELETE FROM meta;""",
        )

    @staticmethod
    def update(database: sqlite3.Connection, id_: int, key: str, value: str) -> None:
        """Update a Meta inside the meta table.

        :param database: A database handle
        :param id_: The id of the meta to update
        :param key: The key to update
        :param value: The value to insert
        :return: None
        """
        SqliteHelper.exec(
            database,
            """
            UPDATE meta SET
                key = ?,
                value = ?
            WHERE
                id = ?;""",
            (key, value, id_),
        )

    @staticmethod
    def list(database: sqlite3.Connection) -> list[tuple[int, str, str]]:
        """Return the list of all the metas from the meta table.

        :param database: A database handle
        :return: The list of Metas
        """
        rows = SqliteHelper.fetch(
            database,
            """
            SELECT * FROM meta;""",
        )

        result = list()
        for row in rows:
            result.append(tuple(row))

        return result
