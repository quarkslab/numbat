# -*- coding: utf-8 -*-

#  Copyright 2023 Quarkslab
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

"""Public API of Numbat. Allow to create and manipulate Sourcetrail DB."""

import hashlib
import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from .db import (
    ComponentAccessDAO,
    EdgeDAO,
    ElementComponentDAO,
    ElementDAO,
    ErrorDAO,
    FileContentDAO,
    FileDAO,
    LocalSymbolDAO,
    MetaDAO,
    NodeDAO,
    NodeFileDAO,
    NodeTypeDAO,
    OccurrenceDAO,
    SourceLocationDAO,
    SqliteHelper,
    SymbolDAO,
)
from .exceptions import NoDatabaseOpen, NumbatException
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
    NameElement,
    NameHierarchy,
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


class SourcetrailDB:
    """Wrapper to Sourcetrail internal database.

    It is able to create, edit and delete the underlying sqlite3
    database used by Sourcetrail.
    """

    # Sourcetrail files extension
    SOURCETRAIL_PROJECT_EXT = ".srctrlprj"
    SOURCETRAIL_DB_EXT = ".srctrldb"
    # Project directory for sideloaded files
    SOURCETRAIL_PROJECT_DIR = "_files/"

    SOURCETRAIL_XML = "\n".join(
        [
            '<?xml version="1.0" encoding="utf-8" ?>',
            "<config>",
            "   <version>0</version>",
            "</config>",
        ]
    )

    def __init__(
        self,
        database: sqlite3.Connection,
        path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        self.database = database
        self.path = path
        self.project_dir = self.path.parent
        self.files_directory = Path(str(path.stem) + self.SOURCETRAIL_PROJECT_DIR)
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        self.name_cache: dict[str, int] = dict()

    # ------------------------------------------------------------------------ #
    # Database file management functions                                       #
    # ------------------------------------------------------------------------ #

    @classmethod
    def __uniformize_path(cls, path: Path | str) -> Path:
        """Check path type and suffix.

        Ensure that the provided path is of type pathlib.Path and has the
        correct suffix, if not add it or cast it.

        :param path: The path to the existing or future database
        :return: a path object
        """
        path = Path(path)
        if path.suffix != cls.SOURCETRAIL_DB_EXT:
            path = path.with_suffix(cls.SOURCETRAIL_DB_EXT)
        return path.resolve().absolute()

    @classmethod
    def exists(cls, path: Path | str) -> bool:
        """Check if there is a Sourcetrail db with the given path.

        If the provided path does not end with the sourcetrail db correct
        suffix. It will be added.

        :param path: The path to test
        :return: a bool
        """
        path = cls.__uniformize_path(path)
        return path.exists()

    @classmethod
    def open(cls, path: Path | str, clear: bool = False) -> "SourcetrailDB":
        """Open an existing sourcetrail database.

        :param path: The path to the existing database
        :param clear: If set to True the database is cleared (Optional)
        :return: the SourcetrailDB object corresponding to the given DB
        """
        path = cls.__uniformize_path(path)
        if not path.exists():
            if path.is_file() or not clear:
                raise FileNotFoundError("%s not found" % str(path))
            return cls.create(path)

        if clear:
            path.unlink(missing_ok=True)
            return cls.create(path)

        try:
            database = SqliteHelper.connect(str(path))
        except Exception as e:
            raise NumbatException(*e.args) from e

        obj = SourcetrailDB(database, path)

        return obj

    @classmethod
    def create(cls, path: Path | str) -> "SourcetrailDB":
        """Create a sourcetrail database.

        :param path: The path to the new database
        :return: the SourcetrailDB object corresponding to the given DB path
        """
        path = cls.__uniformize_path(path)
        if path.exists():
            raise FileExistsError("%s already exists" % str(path))

        try:
            database = SqliteHelper.connect(str(path))
        except Exception as e:
            raise NumbatException(*e.args) from e

        obj = SourcetrailDB(database, path)
        try:
            obj.__create_sql_tables()
            # add metadata in db
            MetaDAO.new(obj.database, "storage_version", "25")
            MetaDAO.new(obj.database, "project_settings", obj.SOURCETRAIL_XML)
            # Create Sourcetrail Project file
            project_file = obj.path.with_suffix(cls.SOURCETRAIL_PROJECT_EXT)
            project_file.write_text(cls.SOURCETRAIL_XML)
            # Create project directory
            obj.project_dir = obj.path.parent
            obj.files_directory = Path(str(obj.path.stem) + cls.SOURCETRAIL_PROJECT_DIR)
            Path(obj.project_dir, obj.files_directory).mkdir(mode=0o755, exist_ok=True)
            # Commit change to the database so we don't ended up with a half setup DB if
            # an exceptions is raised before the next commit
            obj.commit()
        except Exception as e:
            # They already exists, fail
            obj.close()
            raise NumbatException(*e.args) from e
        return obj

    def __create_sql_tables(self) -> None:
        """Create all the sql tables needed by sourcetrail.

        :return: None
        """
        ElementDAO.create_table(self.database)
        ElementComponentDAO.create_table(self.database)
        EdgeDAO.create_table(self.database)
        NodeDAO.create_table(self.database)
        NodeTypeDAO.create_table(self.database)
        SymbolDAO.create_table(self.database)
        FileDAO.create_table(self.database)
        FileContentDAO.create_table(self.database)
        NodeFileDAO.create_table(self.database)
        LocalSymbolDAO.create_table(self.database)
        SourceLocationDAO.create_table(self.database)
        OccurrenceDAO.create_table(self.database)
        ComponentAccessDAO.create_table(self.database)
        ErrorDAO.create_table(self.database)
        MetaDAO.create_table(self.database)

    def commit(self) -> None:
        """Commit changes made to a sourcetrail database.

        Any change made to the database using this API will be lost if not
        committed before closing the database.

        :return: None
        """
        if self.database:
            self.database.commit()
        else:
            raise NoDatabaseOpen()

    def clear(self) -> None:
        """
        Clear all elements present in the database.

        :return: None
        """
        if not self.database:
            raise NoDatabaseOpen()
        ElementDAO.clear(self.database)
        ElementComponentDAO.clear(self.database)
        EdgeDAO.clear(self.database)
        NodeDAO.clear(self.database)
        NodeTypeDAO.clear(self.database)
        SymbolDAO.clear(self.database)
        FileDAO.clear(self.database)
        FileContentDAO.clear(self.database)
        NodeFileDAO.clear(self.database)
        LocalSymbolDAO.clear(self.database)
        SourceLocationDAO.clear(self.database)
        OccurrenceDAO.clear(self.database)
        ComponentAccessDAO.clear(self.database)
        ErrorDAO.clear(self.database)

    def close(self) -> None:
        """Close a sourcetrail database.

        The database must be closed after use in order to liberate
        memory and resources allocated for it.

        :return: None
        """
        if self.database:
            self.database.close()
            del self
        else:
            raise NoDatabaseOpen()

    ####################################################################################
    #                        GENERAL SYMBOLS OPERATIONS                                #
    ####################################################################################

    def __add_if_not_existing(
        self, name: str, type_: NodeType, hover_display: str
    ) -> int:
        """Create a new node if it does not already exist.

        :warning: This is not the same behavior as SourcetrailDB
        We are not allowing nodes with same serialized_name

        :param name: The serialized_name of the node
        :param type_: The type of the node to insert
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new node or the identifier of
                 the existing one
        """
        if name not in self.name_cache:
            elem = Element()
            elem.id = ElementDAO.new(self.database, elem)

            NodeDAO.new(self.database, Node(elem.id, type_, name, hover_display))

            self.name_cache[name] = elem.id
            return elem.id
        else:
            return self.name_cache[name]

    def _record_symbol(self, hierarchy: NameHierarchy, hover_display: str) -> int:
        """Record a new Symbol in the database.

        :param hierarchy: The hierarchy of the symbol to insert
        :param hover_display: the display text when hovering over the node
        :return: An unique integer that identify the inserted element
        """
        ids = []

        # Add all the nodes needed
        for i in range(0, hierarchy.size()):
            ids.append(
                self.__add_if_not_existing(
                    hierarchy.serialize_range(0, i + 1),
                    NodeType.NODE_SYMBOL,
                    hover_display,
                )
            )

        # Add all the edges between nodes
        if len(ids) > 1:
            for i in range(1, len(ids)):
                parent, child = ids[i - 1], ids[i]
                elem = Element()
                elem.id = ElementDAO.new(self.database, elem)

                EdgeDAO.new(
                    self.database, Edge(elem.id, EdgeType.MEMBER, parent, child)
                )

                # Return the id of the last inserted elements
        return ids[-1]

    def _get_symbol(self, hierarchy: NameHierarchy) -> int | None:
        """Return the corresponding Symbol from the database.

        :param hierarchy: The hierarchy of the symbol to retrieve
        :return: The identifier of the existing symbol or None if the symbol
                 does not exist.
        """
        serialized_name = hierarchy.serialize_name()
        try:
            node = NodeDAO.get_by_name(self.database, serialized_name)
        except KeyError:
            return None
        if node:
            return node.id
        return None

    def _record_symbol_kind(self, id_: int, type_: NodeType) -> None:
        """Set the type of the symbol.

        It is equivalent to setting the type of the underlying node.

        :param id_: The identifier of the element
        :param type_: The new type for the symbol
        :return: None
        """
        try:
            node = NodeDAO.get(self.database, id_)
        except KeyError as e:
            raise KeyError(f"Node with id {id_} does not exist in DB") from e
        if node:
            node.type = type_
            NodeDAO.update(self.database, node)

    def _record_symbol_definition_kind(self, id_: int, kind: SymbolType) -> None:
        """Set the type of definition of the corresponding element.

        :param id_: The identifier of the element
        :param kind: The new type for the symbol
        :return: None
        """
        try:
            symb = SymbolDAO.get(self.database, id_)
        except KeyError:
            symb = None
        if symb:
            if symb.definition_kind != kind:
                symb.definition_kind = kind
                SymbolDAO.update(self.database, symb)
        else:
            symb = Symbol(id_, kind)
            SymbolDAO.new(self.database, symb)

    ####################################################################################
    #                                 NODES                                            #
    ####################################################################################

    def __full_record_node(
        self,
        name: str,
        prefix: str,
        postfix: str,
        delimiter: str,
        parent_id: int | None,
        is_indexed: bool,
        type_: NodeType,
        hover_display: str,
    ) -> int | None:
        """Implement a wrapper for all the record_XX methods where XX is a node type.

        It creates the appropriated structures (NameElement, NameHierarchy, etc.)
        and then insert them in the DB. It also handles the typing of the created node
        plus its definition type (explicit or implicit).

        This method also handle the case where the node is the child of an already
        existing node. It automatically creates the hierarchy and so on.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :param type_: type of the node to add
        :return: The identifier of the new class or None if it could not be inserted
        """
        name_element = NameElement(prefix, name, postfix)
        if parent_id:
            try:
                node = NodeDAO.get(self.database, parent_id)
            except KeyError:
                node = None
            if not node:
                return None
            hierarchy = NameHierarchy.deserialize_name(node.name)
            hierarchy.extend(name_element)
            obj_id = self._record_symbol(hierarchy, hover_display)
        else:
            obj_id = self._record_symbol(
                NameHierarchy(delimiter, [name_element]), hover_display
            )

        if obj_id:
            self._record_symbol_kind(obj_id, type_)
            if is_indexed:
                self._record_symbol_definition_kind(obj_id, SymbolType.EXPLICIT)
            return obj_id
        return None

    def record_symbol_node(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a "SYMBOL" symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_SYMBOL,
            hover_display,
        )

    def record_type_node(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a TYPE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_TYPE,
            hover_display,
        )

    def record_buitin_type_node(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a BUILTIN_TYPE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_BUILTIN_TYPE,
            hover_display,
        )

    def record_module(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a MODULE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_MODULE,
            hover_display,
        )

    def record_namespace(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a NAMESPACE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_NAMESPACE,
            hover_display,
        )

    def record_package(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a PACKAGE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_PACKAGE,
            hover_display,
        )

    def record_struct(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a STRUCT symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_STRUCT,
            hover_display,
        )

    def record_class(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a CLASS symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_CLASS,
            hover_display,
        )

    def record_interface(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a INTERFACE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_INTERFACE,
            hover_display,
        )

    def record_annotation(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a ANNOTATION symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_ANNOTATION,
            hover_display,
        )

    def record_global_variable(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a GLOBAL_VARIABLE symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_GLOBAL_VARIABLE,
            hover_display,
        )

    def record_field(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a FIELD symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_FIELD,
            hover_display,
        )

    def record_function(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a FUNCTION symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_FUNCTION,
            hover_display,
        )

    def record_method(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a METHOD symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_METHOD,
            hover_display,
        )

    def record_enum(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a ENUM symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_ENUM,
            hover_display,
        )

    def record_enum_constant(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a ENUM_CONSTANT symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_ENUM_CONSTANT,
            hover_display,
        )

    def record_typedef_node(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a TYPEDEF symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_TYPEDEF,
            hover_display,
        )

    def record_type_parameter_node(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a TYPE_PARAMETER symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_TYPE_PARAMETER,
            hover_display,
        )

    def record_macro(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a MACRO symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_MACRO,
            hover_display,
        )

    def record_union(
        self,
        name: str = "",
        prefix: str = "",
        postfix: str = "",
        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
        parent_id: int | None = None,
        is_indexed: bool = True,
        hover_display: str = "",
    ) -> int | None:
        """Record a UNION symbol into the DB.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param hover_display: the display text when hovering over the node
        :return: The identifier of the new class or None if it could not be inserted
        """
        return self.__full_record_node(
            name,
            prefix,
            postfix,
            delimiter,
            parent_id,
            is_indexed,
            NodeType.NODE_UNION,
            hover_display,
        )

    def _record_access_specifier(
        self, symbol_id: int, access: ComponentAccessType
    ) -> None:
        """Record an access specifier for a symbol.

        For example, if the symbol is a public one in the class.

        :param symbol_id: The identifier of the symbol to update
        :param access: The access specifier to set (cf. ComponentAccessType)
        :return: None
        """
        ComponentAccessDAO.new(
            self.database, ComponentAccess(symbol_id, ComponentAccessType(access))
        )

    def record_public_access(self, symbol_id: int) -> None:
        """Record the `public` access specifier for a symbol.

        :param symbol_id: The identifier of the symbol to update
        :return: None
        """
        self._record_access_specifier(symbol_id, ComponentAccessType.PUBLIC)

    def record_private_access(self, symbol_id: int) -> None:
        """Record the `private` access specifier for a symbol.

        :param symbol_id: The identifier of the symbol to update
        :return: None
        """
        self._record_access_specifier(symbol_id, ComponentAccessType.PRIVATE)

    def record_protected_access(self, symbol_id: int) -> None:
        """Record the `protected` access specifier for a symbol.

        :param symbol_id: The identifier of the symbol to update
        :return: None
        """
        self._record_access_specifier(symbol_id, ComponentAccessType.PROTECTED)

    def record_default_access(self, symbol_id: int) -> None:
        """Record the `default` access specifier for a symbol.

        :param symbol_id: The identifier of the symbol to update
        :return: None
        """
        self._record_access_specifier(symbol_id, ComponentAccessType.DEFAULT)

    def record_template_parameter_access(self, symbol_id: int) -> None:
        """Record the `template parameter` access specifier for a symbol.

        :param symbol_id: The identifier of the symbol to update
        :return: None
        """
        self._record_access_specifier(symbol_id, ComponentAccessType.TEMPLATE_PARAMETER)

    def record_type_parameter_access(self, symbol_id: int) -> None:
        """Record the `type parameter` access specifier for a symbol.

        :param symbol_id: The identifier of the symbol to update
        :return: None
        """
        self._record_access_specifier(symbol_id, ComponentAccessType.TYPE_PARAMETER)

    @staticmethod
    def __str_to_node_type(s: str) -> NodeType:
        """Convert a string to its corresponding element in the NodeType enum.

        :param s: The string to convert
        :return: The corresponding enum value
        """
        match s:
            case "symbol":
                return NodeType.NODE_SYMBOL
            case "type":
                return NodeType.NODE_TYPE
            case "built-in type":
                return NodeType.NODE_BUILTIN_TYPE
            case "module":
                return NodeType.NODE_MODULE
            case "namespace":
                return NodeType.NODE_NAMESPACE
            case "package":
                return NodeType.NODE_PACKAGE
            case "struct":
                return NodeType.NODE_STRUCT
            case "class":
                return NodeType.NODE_CLASS
            case "interface":
                return NodeType.NODE_INTERFACE
            case "annotation":
                return NodeType.NODE_ANNOTATION
            case "global variable":
                return NodeType.NODE_GLOBAL_VARIABLE
            case "field":
                return NodeType.NODE_FIELD
            case "function":
                return NodeType.NODE_FUNCTION
            case "method":
                return NodeType.NODE_METHOD
            case "enum":
                return NodeType.NODE_ENUM
            case "enum constant":
                return NodeType.NODE_ENUM_CONSTANT
            case "typedef":
                return NodeType.NODE_TYPEDEF
            case "type parameter":
                return NodeType.NODE_TYPE_PARAMETER
            case "file":
                return NodeType.NODE_FILE
            case "macro":
                return NodeType.NODE_MACRO
            case "union":
                return NodeType.NODE_UNION
        raise KeyError(f"{s} is not a Node Type")

    def set_node_type(
        self, type_to_change: str, graph_display: str = "", hover_display: str = ""
    ) -> None:
        """Change the display text of a node type.

        Allowed values for node types: `annotation` `built-in type` `class` `enum`
        `enum constant` `field` `file` `function` `global variable`
        `interface` `macro` `method` `module` `namespace` `package` `struct` `symbol`
        `type` `type parameter` `typedef` `union`
        :param type_to_change: The node type to update
        :param graph_display: The display text in the Sourcetrail graph
        :param hover_display: The display text when hovering over a node
        """
        node_type = self.__str_to_node_type(type_to_change)
        if node_type != "":
            if graph_display == "":
                graph_display = NodeTypeDAO.get_by_id(
                    self.database, node_type
                ).graph_display
            if hover_display == "":
                hover_display = NodeTypeDAO.get_by_id(
                    self.database, node_type
                ).hover_display
            NodeTypeDAO.update(
                self.database, NodeDisplay(node_type, graph_display, hover_display)
            )

    def change_node_color(
        self,
        node_id: int,
        fill_color: str = "default",
        border_color: str = "default",
        text_color: str = "default",
        icon_color: str = "default",
        hatching_color: str = "default",
    ) -> None:
        """Change the color of a node.

        Supported values for colors: RGB hex code (e.g. #AABBCC), [SVG color keyword](https://www.w3.org/TR/SVG11/types.html#ColorKeywords)
        :param node_id: Id of the node to change
        :param fill_color: Color of the node body
        :param border_color: Color of the border
        :param text_color: Color of the node text
        :param icon_color: Color of the node icon (if applicable)
        :param hatching_color: Color of the node hatching (if applicable)
        :return: None
        """
        NodeDAO.set_color(
            self.database,
            node_id,
            " ".join(
                [fill_color, border_color, text_color, icon_color, hatching_color]
            ),
        )

    def change_edge_color(self, edge_id: int, color: str) -> None:
        """Change the color of an edge.

        Supported values for colors: RGB hex code (e.g. #AABBCC), [SVG color keyword](https://www.w3.org/TR/SVG11/types.html#ColorKeywords)
        :param edge_id: Id of the edge to change
        :param color: RGB hex code or name of the edge's new color
        :return: None
        """
        EdgeDAO.set_color(self.database, edge_id, color)

    def set_custom_command(self, node_id: int, command: list, description: str) -> None:
        """Add a custom command to a node's context menu.

        :param node_id: Id of the node to add the custom command to
        :param command: List containing the command to execute and its arguments
        :param description: Description of the command
        :return: None
        """
        if not isinstance(command, list):
            raise TypeError(
                "Custom command must be a list containing its argument vector"
            )
        NodeDAO.set_custom_command(
            self.database, node_id, ("\t".join(command), description)
        )

    def associate_file_to_node(
        self, node_id: int, file: Path, display_content: bool
    ) -> None:
        """Copy a file to the project directory and link it to a node.

        :param node_id: Id of the node to link
        :param file: Path to the file to link
        :param display_content: Whether the file content should be displayed or not
        :return: None
        """
        # use file hash as destination file name
        sha256 = hashlib.sha256()

        with open(file, "rb") as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                sha256.update(data)
        hash = sha256.hexdigest()
        file_path = f"{self.files_directory}/{hash}"
        dest = f"{self.project_dir}/{file_path}"

        # copy file if not exists
        if not Path(dest).exists():
            shutil.copy2(file, dest)
        # associate node and file
        NodeFileDAO.new(self.database, NodeFile(node_id, file_path, display_content))

    ####################################################################################
    #                               REFERENCES                                         #
    ####################################################################################

    # Add new references

    def _record_reference(
        self, source_id: int, dest_id: int, type_: EdgeType, hover_display: str
    ) -> int:
        """Add a new reference (an edge) between two elements.

        :param source_id: The source identifier of the reference
        :param dest_id: The destination identifier of the reference
        :param type_: The type of reference to add
        :return: None
        """
        elem = Element()
        elem.id = ElementDAO.new(self.database, elem)

        EdgeDAO.new(
            self.database, Edge(elem.id, type_, source_id, dest_id, hover_display)
        )

        return elem.id

    def record_ref_member(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a member reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.MEMBER, hover_display
        )

    def record_ref_type_usage(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a TYPE_USAGE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.TYPE_USAGE, hover_display
        )

    def record_ref_usage(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a USAGE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, EdgeType.USAGE, hover_display)

    def record_ref_call(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a CALL reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, EdgeType.CALL, hover_display)

    def record_ref_inheritance(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add an INHERITANCE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.INHERITANCE, hover_display
        )

    def record_ref_override(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add an OVERRIDE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.OVERRIDE, hover_display
        )

    def record_ref_type_argument(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a TYPE_ARGUMENT reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.TYPE_ARGUMENT, hover_display
        )

    def record_ref_template_specialization(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a TEMPLATE_SPECIALIZATION reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.TEMPLATE_SPECIALIZATION, hover_display
        )

    def record_ref_include(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add an INCLUDE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.INCLUDE, hover_display
        )

    def record_ref_import(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add an import reference (aka an edge) between two elements.

        :param source_id: The source identifier (who imports)
        :param dest_id: The destination identifier (who is imported)
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.IMPORT, hover_display
        )

    def record_ref_bundled_edges(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a BUNDLED_EDGES reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.BUNDLED_EDGES, hover_display
        )

    def record_ref_macro_usage(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add a MACRO_USAGE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.MACRO_USAGE, hover_display
        )

    def record_ref_annotation_usage(
        self, source_id: int, dest_id: int, hover_display: str = ""
    ) -> int:
        """Add an ANNOTATION_USAGE reference (aka an edge) between two elements.

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :param hover_display: The display text when hovering over the edge
        :return: the reference id
        """
        return self._record_reference(
            source_id, dest_id, EdgeType.ANNOTATION_USAGE, hover_display
        )

    def record_reference_to_unsolved_symbol(
        self,
        symbol_id: int,
        reference_type: EdgeType,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        hover_display: str = "",
    ) -> int:
        """Record a reference to an unsolved symbol.

        :param symbol_id: The identifier of the symbol
        :param reference_type: The type of reference
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :param hover_display: the display text when hovering over the edge
        :return: The identifier of the new reference
        """
        # Don't blame me, it's done like this in sourcetrail source code
        hierarchy = NameHierarchy(
            NameHierarchy.NAME_DELIMITER_UNKNOWN,
            [NameElement("", "unsolved symbol", "")],
        )

        # Insert the new node
        unsolved_symbol_id = self._record_symbol(hierarchy, "")

        # Add a new edge
        elem = Element()
        elem.id = ElementDAO.new(self.database, elem)

        reference_id = EdgeDAO.new(
            self.database,
            Edge(elem.id, reference_type, symbol_id, unsolved_symbol_id, hover_display),
        )

        # Add the new source location
        self.__record_source_location(
            reference_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.UNSOLVED,
        )

        # Return edge id
        return reference_id

    # Modify existing references
    def record_reference_is_ambiguous(self, reference_id: int) -> None:
        """Add an indication in the database to tell that the reference is ambiguous.

        :param reference_id: the identifier of the reference
        :return: None
        """
        ElementComponentDAO.new(
            self.database,
            ElementComponent(0, reference_id, ElementComponentType.IS_AMBIGUOUS, ""),
        )

    ####################################################################################
    #                           SOURCE CODE MANIPULATION                               #
    ####################################################################################

    def record_file(
        self, path: Path, indexed: bool = True, hover_display: str = ""
    ) -> int:
        """Record a source file in the database.

        :param path: The path to the existing source file
        :param indexed: A boolean that indicates if the source file
                        was indexed by the parser
        :param hover_display: The display text when hovering over the node
        :return: The identifier of the inserted file
        """
        if not path.exists() or not path.is_file():
            raise FileNotFoundError()

        # Create a new name hierarchy
        hierarchy = NameHierarchy(
            NameHierarchy.NAME_DELIMITER_FILE,
            [NameElement("", str(path.absolute()), "")],
        )

        # Retrieve the modification date in the correct format
        modification_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Read the file
        lines = []
        if indexed:
            lines = open(path, "r").readlines()

        # Insert a new node
        elem_id = self.__add_if_not_existing(
            hierarchy.serialize_name(), NodeType.NODE_FILE, hover_display
        )

        # Insert a new file
        FileDAO.new(
            self.database,
            File(
                elem_id,
                str(path.absolute()),
                "",  # Empty language identifier for now
                modification_time,
                indexed,
                True,
                len(lines),
            ),
        )

        if indexed:
            # Insert a new filecontent
            FileContentDAO.new(self.database, FileContent(elem_id, "".join(lines)))

        # Return the newly created element id
        return elem_id

    def record_file_language(self, id_: int, language: str) -> None:
        """Set the language of an existing file inside the database.

        :param id_: The identifier of the file
        :param language: A string that indicate the programming language of the file
        :return: None
        """
        try:
            file = FileDAO.get(self.database, id_)
        except KeyError as e:
            raise KeyError(f"File with id {id_} does not exist in DB") from e
        if file:
            file.language = language
            FileDAO.update(self.database, file)

    def __record_source_location(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        type_: SourceLocationType,
    ) -> int:
        """Record a location. Wrapper for all the record_*_location.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :param type_: The type of the source location.
        :return: None
        """
        # First add a new source location entry
        loc_id = SourceLocationDAO.new(
            self.database,
            SourceLocation(
                0, file_id, start_line, start_column, end_line, end_column, type_
            ),
        )

        # Now add an occurrence that refer to this location
        OccurrenceDAO.new(self.database, Occurrence(symbol_id, loc_id))
        return loc_id

    def record_symbol_location(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new source location of type TOKEN.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.TOKEN,
        )

    def record_symbol_scope_location(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new source location of type SCOPE.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.SCOPE,
        )

    def record_symbol_signature_location(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new source location of type SCOPE.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.SIGNATURE,
        )

    def record_reference_location(
        self,
        reference_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new reference location of type TOKEN.

        :param reference_id: The reference identifier
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            reference_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.TOKEN,
        )

    def record_qualifier_location(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new source location of type QUALIFIER.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.QUALIFIER,
        )

    def record_local_symbol(self, name: str) -> int:
        """Record a new local symbol.

        :param name: The name of the new local symbol
        :return: The identifier of the new local symbol
        """
        # Check that the symbol does not already exist
        try:
            local = LocalSymbolDAO.get_from_name(self.database, name)
        except KeyError:
            local = None
        if not local:
            # Insert a new local symbol
            elem = Element()
            elem.id = ElementDAO.new(self.database, elem)
            local = LocalSymbol(elem.id, name)
            LocalSymbolDAO.new(self.database, local)

        return local.id

    def record_local_symbol_location(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new source location of type LOCAL_SYMBOL.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.LOCAL_SYMBOL,
        )

    def record_atomic_source_range(
        self,
        symbol_id: int,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> int:
        """Record a new source location of type ATOMIC_RANGE.

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        return self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.ATOMIC_RANGE,
        )

    def record_error(
        self,
        msg: str,
        fatal: bool,
        file_id: int,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
    ) -> None:
        """Record a new indexer error in the database.

        :param msg: The description of the error
        :param fatal: A boolean indicating if the error stop the execution of the parser
        :param file_id: The identifier of the source file being parsed
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """
        # Add a new error
        elem = Element()
        elem.id = ElementDAO.new(self.database, elem)

        error_id = ErrorDAO.new(self.database, Error(elem.id, msg, fatal, True, ""))
        self.__record_source_location(
            error_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.INDEXER_ERROR,
        )
