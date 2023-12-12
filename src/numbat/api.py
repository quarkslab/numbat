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

"""Public API of Numbat. Allow to create and manipulate Sourcetrail DB"""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from .types import Element, ElementComponent, ElementComponentType, Edge, \
    EdgeType, Node, NodeType, Symbol, SymbolType, File, FileContent, \
    LocalSymbol, SourceLocation, SourceLocationType, Occurrence, Error, \
    NameElement, NameHierarchy

from .db import ComponentAccessDAO, EdgeDAO, ElementComponentDAO, FileDAO, \
    ElementDAO, ErrorDAO, FileContentDAO, LocalSymbolDAO, MetaDAO, \
    NodeDAO, OccurrenceDAO, SourceLocationDAO, SqliteHelper, SymbolDAO

from .exceptions import NoDatabaseOpen, NumbatException


class SourcetrailDB():
    """
    This class implement a wrapper to Sourcetrail internal database,
    it is able to create, edit and delete the underlying sqlite3
    database used by Sourcetrail.
    """

    # Sourcetrail files extension
    SOURCETRAIL_PROJECT_EXT = '.srctrlprj'
    SOURCETRAIL_DB_EXT = '.srctrldb'

    SOURCETRAIL_XML = '\n'.join([
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<config>',
        '   <version>0</version>',
        '</config>'
    ])

    def __init__(self, database: sqlite3.Connection, path: Path, logger: logging.Logger = None) -> None:
        self.database = database
        self.path = path
        if logger is None:
            self.logger = logging.getLogger()
        else:
            self.logger = logger
        self.name_cache = dict()

    # ------------------------------------------------------------------------ #
    # Database file management functions                                       #
    # ------------------------------------------------------------------------ #


    @classmethod
    def __uniformize_path(cls, path: Path | str) -> Path:
        """
        Ensure that the provided path is of type pathlib.Path and has the
        correct suffix, if not add it or cast it.

        :param path: The path to the existing or future database
        :return: a path object
        """
        if type(path) == str:
            path = Path(path)
        if path.suffix != cls.SOURCETRAIL_DB_EXT:
            path = path.with_suffix(cls.SOURCETRAIL_DB_EXT)
        return path.absolute()

    @classmethod
    def exists(cls, path: Path | str) -> bool:
        """
        This method check if there is a Sourcetrail db with the given path.
        If the provided path does not end with the sourcetrail db correct
        suffix. It will be added.

        :param path: The path to test
        :return: a bool
        """
        path = cls.__uniformize_path(path)
        return path.exists()

    @classmethod
    def open(cls, path: Path | str, clear: bool = False) -> 'SourcetrailDB':
        """
        This method allow to open an existing sourcetrail database

        :param path: The path to the existing database
        :param clear: If set to True the database is cleared (Optional)
        :return: the SourcetrailDB object corresponding to the given DB
        """
        path = cls.__uniformize_path(path)
        if not path.exists():
            if path.is_file() or not clear:
                raise FileNotFoundError('%s not found' % str(path))
            return cls.create(path)

        try:
            database = SqliteHelper.connect(str(path))
        except Exception as e:
            raise NumbatException(*e.args)

        obj = SourcetrailDB(database, path)

        if clear:
            # Clear the database if the user ask to
            obj.clear()

        return obj

    @classmethod
    def create(cls, path: Path | str) -> 'SourcetrailDB':
        """
        This method allow to create a sourcetrail database

        :param path: The path to the new database
        :return: the SourcetrailDB object corresponding to the given DB path
        """
        path = cls.__uniformize_path(path)
        if path.exists():
            raise FileExistsError('%s already exists' % str(path))

        try:
            database = SqliteHelper.connect(str(path))
        except Exception as e:
            raise NumbatException(*e.args)

        obj = SourcetrailDB(database, path)
        try:
            obj.__create_sql_tables()
            # add metadata in db
            MetaDAO.new(obj.database, 'storage_version', '25')
            MetaDAO.new(obj.database, 'project_settings', obj.SOURCETRAIL_XML)
            # Create Sourcetrail Project file
            project_file = obj.path.with_suffix(cls.SOURCETRAIL_PROJECT_EXT)
            project_file.write_text(cls.SOURCETRAIL_XML)
            # Commit change to the database so we don't ended up with a half setup DB if an
            # exceptions is raised before the next commit
            obj.commit()
        except Exception as e:
            # They already exists, fail
            obj.close()
            raise NumbatException(*e.args)
        return obj

    def __create_sql_tables(self) -> None:
        """
        This method allow to create all the sql tables needed
        by sourcetrail

        :return: None
        """
        ElementDAO.create_table(self.database)
        ElementComponentDAO.create_table(self.database)
        EdgeDAO.create_table(self.database)
        NodeDAO.create_table(self.database)
        SymbolDAO.create_table(self.database)
        FileDAO.create_table(self.database)
        FileContentDAO.create_table(self.database)
        LocalSymbolDAO.create_table(self.database)
        SourceLocationDAO.create_table(self.database)
        OccurrenceDAO.create_table(self.database)
        ComponentAccessDAO.create_table(self.database)
        ErrorDAO.create_table(self.database)
        MetaDAO.create_table(self.database)

    def commit(self) -> None:
        """
        This method allow to commit changes made to a sourcetrail database.
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
        SymbolDAO.clear(self.database)
        FileDAO.clear(self.database)
        FileContentDAO.clear(self.database)
        LocalSymbolDAO.clear(self.database)
        SourceLocationDAO.clear(self.database)
        OccurrenceDAO.clear(self.database)
        ComponentAccessDAO.clear(self.database)
        ErrorDAO.clear(self.database)

    def close(self) -> None:
        """
        This method allow to close a sourcetrail database.
        The database must be closed after use in order to liberate
        memory and resources allocated for it.

        :return: None
        """
        if self.database:
            self.database.close()
            self.database = None
        else:
            raise NoDatabaseOpen()

    ####################################################################################
    #                        GENERAL SYMBOLS OPERATIONS                                #
    ####################################################################################

    def __add_if_not_existing(self, name: str, type_: NodeType) -> int:
        """
        Create a new node if it does not already exist

        @Warning: This is not the same behavior as SourcetrailDB
        We are not allowing nodes with same serialized_name

        :param name: The serialized_name of the node
        :param type_: The type of the node to insert
        :return: The identifier of the new node or the identifier of
                 the existing one
        """

        if name not in self.name_cache:
            elem = Element()
            elem.id = ElementDAO.new(self.database, elem)

            NodeDAO.new(self.database, Node(
                elem.id,
                type_,
                name
            ))

            self.name_cache[name] = elem.id
            return elem.id
        else:
            return self.name_cache[name]

    def _record_symbol(self, hierarchy: NameHierarchy) -> int:
        """
        Record a new Symbol in the database

        :param hierarchy: The hierarchy of the symbol to insert
        :return: An unique integer that identify the inserted element
        """

        ids = []

        # Add all the nodes needed
        for i in range(0, hierarchy.size()):
            ids.append(self.__add_if_not_existing(
                hierarchy.serialize_range(0, i + 1),
                NodeType.NODE_SYMBOL
            ))

        # Add all the edges between nodes
        if len(ids) > 1:
            parent, children = ids[0], ids[1:]
            for child in children:
                elem = Element()
                elem.id = ElementDAO.new(self.database, elem)

                EdgeDAO.new(self.database, Edge(
                    elem.id,
                    EdgeType.MEMBER,
                    parent,
                    child
                ))

                # Return the id of the last inserted elements
        return ids[-1]

    def _get_symbol(self, hierarchy: NameHierarchy) -> int | None:
        """
        Return the corresponding Symbol from the database

        :param hierarchy: The hierarchy of the symbol to retrieve
        :return: The identifier of the existing symbol or None if the symbol
                 does not exist.
        """

        serialized_name = hierarchy.serialize_name()
        node = NodeDAO.get_by_name(self.database, serialized_name)
        if node:
            return node.id

    def _record_symbol_kind(self, id_: int, type_: NodeType) -> None:
        """
        Set the type of the symbol which is equivalent to setting the
        type of the underlying node.

        :param id_: The identifier of the element
        :param type_: The new type for the symbol
        :return: None
        """

        node = NodeDAO.get(self.database, id_)
        if node:
            node.type = type_
            NodeDAO.update(self.database, node)

    def _record_symbol_definition_kind(self, id_: int, kind: SymbolType) -> None:
        """
        Set the type of definition of the corresponding element

        :param id_: The identifier of the element
        :param kind: The new type for the symbol
        :return: None
        """

        symb = SymbolDAO.get(self.database, id_)
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

    def __full_record_node(self,
                           name: str,
                           prefix: str,
                           postfix: str,
                           delimiter: str,
                           parent_id: int | None,
                           is_indexed: bool,
                           type_: NodeType) -> int | None:
        """
        Internal function which will be wrapped by all the record_XX methods
        where XX is a node type (class, method, field, etc.). It creates the
        appropriated structures (NameElement, NameHierarchy, etc.) and then insert
        them in the DB. It also handles the typing of the created node plus its
        definition type (explicit or implicit).

        This method also handle the case where the node is the child of an already
        existing node. It automatically creates the hierarchy and so on.

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :param type_: type of the node to add
        :return: The identifier of the new class or None if it could not be inserted
        """
        name_element = NameElement(prefix, name, postfix)
        if parent_id:
            node = NodeDAO.get(self.database, parent_id)
            if not node:
                return
            hierarchy = NameHierarchy.deserialize_name(node.name)
            hierarchy.extend(name_element)
            obj_id = self._record_symbol(hierarchy)
        else:
            obj_id = self._record_symbol(NameHierarchy(delimiter, [name_element]))

        if obj_id:
            self._record_symbol_kind(obj_id, type_)
            if is_indexed:
                self._record_symbol_definition_kind(obj_id, SymbolType.EXPLICIT)
            return obj_id

    def record_symbol_node(self,
                           name: str = '',
                           prefix: str = '',
                           postfix: str = '',
                           delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                           parent_id: int = None,
                           is_indexed: bool = True) -> int | None:
        """
        Record a "SYMBOL" symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_SYMBOL)

    def record_type_node(self,
                         name: str = '',
                         prefix: str = '',
                         postfix: str = '',
                         delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                         parent_id: int = None,
                         is_indexed: bool = True) -> int | None:
        """
        Record a TYPE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_TYPE)

    def record_buitin_type_node(self,
                                name: str = '',
                                prefix: str = '',
                                postfix: str = '',
                                delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                                parent_id: int = None,
                                is_indexed: bool = True) -> int | None:
        """
        Record a BUILTIN_TYPE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_BUILTIN_TYPE)

    def record_module(self,
                      name: str = '',
                      prefix: str = '',
                      postfix: str = '',
                      delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                      parent_id: int = None,
                      is_indexed: bool = True) -> int | None:
        """
        Record a MODULE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_MODULE)

    def record_namespace(self,
                         name: str = '',
                         prefix: str = '',
                         postfix: str = '',
                         delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                         parent_id: int = None,
                         is_indexed: bool = True) -> int | None:
        """
        Record a NAMESPACE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_NAMESPACE)

    def record_package(self,
                       name: str = '',
                       prefix: str = '',
                       postfix: str = '',
                       delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                       parent_id: int = None,
                       is_indexed: bool = True) -> int | None:
        """
        Record a PACKAGE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_PACKAGE)

    def record_struct(self,
                      name: str = '',
                      prefix: str = '',
                      postfix: str = '',
                      delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                      parent_id: int = None,
                      is_indexed: bool = True) -> int | None:
        """
        Record a STRUCT symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_STRUCT)

    def record_class(self,
                     name: str = '',
                     prefix: str = '',
                     postfix: str = '',
                     delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                     parent_id: int = None,
                     is_indexed: bool = True) -> int | None:
        """
        Record a CLASS symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_CLASS)

    def record_interface(self,
                         name: str = '',
                         prefix: str = '',
                         postfix: str = '',
                         delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                         parent_id: int = None,
                         is_indexed: bool = True) -> int | None:
        """
        Record a INTERFACE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_INTERFACE)

    def record_annotation(self,
                          name: str = '',
                          prefix: str = '',
                          postfix: str = '',
                          delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                          parent_id: int = None,
                          is_indexed: bool = True) -> int | None:
        """
        Record a ANNOTATION symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_ANNOTATION)

    def record_global_variable(self,
                               name: str = '',
                               prefix: str = '',
                               postfix: str = '',
                               delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                               parent_id: int = None,
                               is_indexed: bool = True) -> int | None:
        """
        Record a GLOBAL_VARIABLE symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_GLOBAL_VARIABLE)

    def record_field(self,
                     name: str = '',
                     prefix: str = '',
                     postfix: str = '',
                     delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                     parent_id: int = None,
                     is_indexed: bool = True) -> int | None:
        """
        Record a FIELD symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_FIELD)

    def record_function(self,
                        name: str = '',
                        prefix: str = '',
                        postfix: str = '',
                        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                        parent_id: int = None,
                        is_indexed: bool = True) -> int | None:
        """
        Record a FUNCTION symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_FUNCTION)

    def record_method(self,
                      name: str = '',
                      prefix: str = '',
                      postfix: str = '',
                      delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                      parent_id: int = None,
                      is_indexed: bool = True) -> int | None:
        """
        Record a METHOD symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_METHOD)

    def record_enum(self,
                    name: str = '',
                    prefix: str = '',
                    postfix: str = '',
                    delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                    parent_id: int = None,
                    is_indexed: bool = True) -> int | None:
        """
        Record a ENUM symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_ENUM)

    def record_enum_constant(self,
                             name: str = '',
                             prefix: str = '',
                             postfix: str = '',
                             delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                             parent_id: int = None,
                             is_indexed: bool = True) -> int | None:
        """
        Record a ENUM_CONSTANT symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_ENUM_CONSTANT)

    def record_typedef_node(self,
                            name: str = '',
                            prefix: str = '',
                            postfix: str = '',
                            delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                            parent_id: int = None,
                            is_indexed: bool = True) -> int | None:
        """
        Record a TYPEDEF symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_TYPEDEF)

    def record_type_parameter_node(self,
                                   name: str = '',
                                   prefix: str = '',
                                   postfix: str = '',
                                   delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                                   parent_id: int = None,
                                   is_indexed: bool = True) -> int | None:
        """
        Record a TYPE_PARAMETER symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_TYPE_PARAMETER)

    def record_macro(self,
                     name: str = '',
                     prefix: str = '',
                     postfix: str = '',
                     delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                     parent_id: int = None,
                     is_indexed: bool = True) -> int | None:
        """
        Record a MACRO symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_MACRO)

    def record_union(self,
                     name: str = '',
                     prefix: str = '',
                     postfix: str = '',
                     delimiter: str = NameHierarchy.NAME_DELIMITER_CXX,
                     parent_id: int = None,
                     is_indexed: bool = True) -> int | None:
        """
        Record a UNION symbol into the DB

        :param name: The name of the element to insert
        :param prefix: The prefix of the element to insert
        :param postfix: The postfix of the element to insert
        :param delimiter: The delimiter of the element, if the element has a parent,
        it will not be taken into account as the parent delimiter will be used
        :param parent_id: The identifier of the class in which the method is defined.
        :param is_indexed: if the element is explicit or non-indexed
        :return: The identifier of the new class or None if it could not be inserted
        """

        return self.__full_record_node(name, prefix, postfix, delimiter,
                                       parent_id, is_indexed, NodeType.NODE_UNION)

    ####################################################################################
    #                               REFERENCES                                         #
    ####################################################################################

    # Add new references

    def _record_reference(self, source_id: int, dest_id: int, type_: EdgeType) -> int:
        """
        Add a new reference (an edge) between two elements

        :param source_id: The source identifier of the reference
        :param dest_id: The destination identifier of the reference
        :param type_: The type of reference to add
        :return: None
        """

        elem = Element()
        elem.id = ElementDAO.new(self.database, elem)

        EdgeDAO.new(self.database, Edge(elem.id, type_, source_id, dest_id))

        return elem.id

    def record_ref_member(self, source_id: int, dest_id: int) -> int:
        """
        Add a member reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.MEMBER)

    def record_ref_type_usage(self, source_id: int, dest_id: int) -> int:
        """
        Add a TYPE_USAGE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.TYPE_USAGE)

    def record_ref_usage(self, source_id: int, dest_id: int) -> int:
        """
        Add a USAGE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.USAGE)

    def record_ref_call(self, source_id: int, dest_id: int) -> int:
        """
        Add a CALL reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.CALL)

    def record_ref_inheritance(self, source_id: int, dest_id: int) -> int:
        """
        Add an INHERITANCE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.INHERITANCE)

    def record_ref_override(self, source_id: int, dest_id: int) -> int:
        """
        Add an OVERRIDE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.OVERRIDE)

    def record_ref_type_argument(self, source_id: int, dest_id: int) -> int:
        """
        Add a TYPE_ARGUMENT reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.TYPE_ARGUMENT)

    def record_ref_template_specialization(self, source_id: int, dest_id: int) -> int:
        """
        Add a TEMPLATE_SPECIALIZATION reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.TEMPLATE_SPECIALIZATION)

    def record_ref_include(self, source_id: int, dest_id: int) -> int:
        """
        Add an INCLUDE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.INCLUDE)

    def record_ref_import(self, source_id: int, dest_id: int) -> int:
        """
        Add an import reference (aka an edge) between two elements

        :param source_id: The source identifier (who imports)
        :param dest_id: The destination identifier (who is imported)
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.IMPORT)

    def record_ref_bundled_edges(self, source_id: int, dest_id: int) -> int:
        """
        Add a BUNDLED_EDGES reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.BUNDLED_EDGES)

    def record_ref_macro_usage(self, source_id: int, dest_id: int) -> int:
        """
        Add a MACRO_USAGE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.MACRO_USAGE)

    def record_ref_annotation_usage(self, source_id: int, dest_id: int) -> int:
        """
        Add an ANNOTATION_USAGE reference (aka an edge) between two elements

        :param source_id: The source identifier
        :param dest_id: The destination identifier
        :return: the reference id
        """
        return self._record_reference(source_id, dest_id, type_=EdgeType.ANNOTATION_USAGE)

    def record_reference_to_unsolved_symbol(self, symbol_id: int, reference_type: EdgeType,
                                            file_id: int, start_line: int, start_column: int, end_line: int,
                                            end_column: int) -> int:
        """
        Record a reference to an unsolved symbol.

        :param symbol_id: The identifier of the symbol
        :param reference_type: The type of reference
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: The identifier of the new reference
        """

        # Don't blame me, it's done like this in sourcetrail source code
        hierarchy = NameHierarchy(
            NameHierarchy.NAME_DELIMITER_UNKNOWN,
            [NameElement(
                '',
                'unsolved symbol',
                ''
            )]
        )

        # Insert the new node
        unsolved_symbol_id = self._record_symbol(hierarchy)

        # Add a new edge
        elem = Element()
        elem.id = ElementDAO.new(self.database, elem)

        reference_id = EdgeDAO.new(self.database, Edge(
            elem.id,
            reference_type,
            symbol_id,
            unsolved_symbol_id
        ))

        # Add the new source location
        self.__record_source_location(
            reference_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.UNSOLVED
        )

        # Return edge id
        return reference_id

    # Modify existing references
    def record_reference_is_ambiguous(self, reference_id: int) -> None:
        """
        Add an indication in the database to tell that the reference is ambiguous

        :param reference_id: the identifier of the reference
        :return: None
        """

        ElementComponentDAO.new(self.database, ElementComponent(
            0,
            reference_id,
            ElementComponentType.IS_AMBIGUOUS,
            ''
        ))

    ####################################################################################
    #                           SOURCE CODE MANIPULATION                               #
    ####################################################################################

    def record_file(self, path: Path, indexed: bool = True) -> int:
        """
        Record a source file in the database

        :param path: The path to the existing source file
        :param indexed: A boolean that indicates if the source file
                        was indexed by the parser
        :return: The identifier of the inserted file
        """

        if not path.exists() or not path.is_file():
            raise FileNotFoundError()

        # Create a new name hierarchy
        hierarchy = NameHierarchy(
            NameHierarchy.NAME_DELIMITER_FILE,
            [NameElement(
                '',
                str(path.absolute()),
                ''
            )]
        )

        # Retrieve the modification date in the correct format
        modification_time = datetime.fromtimestamp(
            os.path.getmtime(path)
        ).strftime("%Y-%m-%d %H:%M:%S")

        # Read the file
        lines = []
        if indexed:
            lines = open(path, 'r').readlines()

        # Insert a new node
        elem_id = self.__add_if_not_existing(
            hierarchy.serialize_name(),
            NodeType.NODE_FILE
        )

        # Insert a new file
        FileDAO.new(
            self.database,
            File(
                elem_id,
                str(path.absolute()),
                '',  # Empty language identifier for now
                modification_time,
                indexed,
                True,
                len(lines)
            )
        )

        if indexed:
            # Insert a new filecontent
            FileContentDAO.new(
                self.database,
                FileContent(elem_id, ''.join(lines))
            )

        # Return the newly created element id
        return elem_id

    def record_file_language(self, id_: int, language: str) -> None:
        """
            Set the language of an existing file inside the database
            :param id_: The identifier of the file
            :param language: A string that indicate the programming language of the file
            :return: None
        """

        file = FileDAO.get(self.database, id_)
        if file:
            file.language = language
            FileDAO.update(self.database, file)

    def __record_source_location(self, symbol_id: int, file_id: int,
                                 start_line: int, start_column: int, end_line: int, end_column: int,
                                 type_: SourceLocationType) -> None:
        """
        Wrapper for all the record_*_location

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
        loc_id = SourceLocationDAO.new(self.database, SourceLocation(
            0,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            type_
        ))

        # Now add an occurrence that refer to this location
        OccurrenceDAO.new(self.database, Occurrence(
            symbol_id, loc_id
        ))

    def record_symbol_location(self, symbol_id: int, file_id: int, start_line: int,
                               start_column: int, end_line: int, end_column: int) -> None:

        """
        Record a new source location of type TOKEN

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """

        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.TOKEN
        )

    def record_symbol_scope_location(self, symbol_id: int, file_id: int, start_line: int,
                                     start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new source location of type SCOPE

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """

        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.SCOPE
        )

    def record_symbol_signature_location(self, symbol_id: int, file_id: int, start_line: int,
                                         start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new source location of type SCOPE

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """

        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.SIGNATURE
        )

    def record_reference_location(self, reference_id: int, file_id: int, start_line: int,
                                  start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new reference location of type TOKEN

        :param reference_id: The reference identifier
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """

        self.__record_source_location(
            reference_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.TOKEN
        )

    def record_qualifier_location(self, symbol_id: int, file_id: int, start_line: int,
                                  start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new source location of type QUALIFIER

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """

        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.QUALIFIER
        )

    def record_local_symbol(self, name: str) -> int:
        """
        Record a new local symbol

        :param name: The name of the new local symbol
        :return: The identifier of the new local symbol
        """

        # Check that the symbol does not already exist
        local = LocalSymbolDAO.get_from_name(self.database, name)
        if not local:
            # Insert a new local symbol
            elem = Element()
            elem.id = ElementDAO.new(self.database, elem)
            local = LocalSymbol(elem.id, name)
            LocalSymbolDAO.new(self.database, local)

        return local.id

    def record_local_symbol_location(self, symbol_id: int, file_id: int, start_line: int,
                                     start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new source location of type LOCAL_SYMBOL

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
        """

        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.LOCAL_SYMBOL
        )

    def record_atomic_source_range(self, symbol_id: int, file_id: int, start_line: int,
                                   start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new source location of type ATOMIC_RANGE

        :param symbol_id: The identifier of the symbol
        :param file_id: The identifier of the source file in which the symbol is located
        :param start_line: The line at which the element starts.
        :param start_column: The column at which the element starts.
        :param end_line: The line at which the element ends.
        :param end_column: The line at which the element ends.
        :return: None
    """

        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.ATOMIC_RANGE
        )

    def record_error(self, msg: str, fatal: bool, file_id: int, start_line: int,
                     start_column: int, end_line: int, end_column: int) -> None:
        """
        Record a new indexer error in the database

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

        error_id = ErrorDAO.new(self.database, Error(
            elem.id,
            msg,
            fatal,
            True,
            ''
        ))
        self.__record_source_location(
            error_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            SourceLocationType.INDEXER_ERROR
        )
