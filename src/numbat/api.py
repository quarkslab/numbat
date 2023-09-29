import os
import pathlib
import datetime

from .base import Element, ElementComponent, ElementComponentType, Edge, \
    EdgeType, Node, NodeType, Symbol, SymbolType, File, FileContent, \
    LocalSymbol, SourceLocation, SourceLocationType, Occurrence, Error, \
    NameElement, NameHierarchy

from .dao import ComponentAccessDAO, EdgeDAO, ElementComponentDAO, FileDAO, \
    ElementDAO, ErrorDAO, FileContentDAO, LocalSymbolDAO, MetaDAO, \
    NodeDAO, OccurrenceDAO, SourceLocationDAO, SqliteHelper, SymbolDAO

from .exceptions import NoDatabaseOpen, AlreadyOpenDatabase, NumbatException


class SourcetrailDB(object):
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

    def __init__(self) -> None:
        self.database = None
        self.path = None

    # ------------------------------------------------------------------------ #
    # Database file management functions                                       #
    # ------------------------------------------------------------------------ #

    def open(self, path: pathlib.Path | str, clear: bool = False) -> None:
        """ 
            This method allow to open an existing sourcetrail database 
            :param path: The path to the existing database
            :type path: pathlib.Path | str
            :param clear: If set to True the database is cleared (Optional)
            :type clear: bool
            :return: None
            :rtype: NoneType
        """

        # Convert str input
        if type(path) == str:
            path = pathlib.Path(path)

        # Check that a database is not already opened
        if self.database:
            raise AlreadyOpenDatabase()

        self.path = path
        # Check that the file has the correct extension
        if self.path.suffix != self.SOURCETRAIL_DB_EXT:
            self.path = self.path.with_suffix(self.SOURCETRAIL_DB_EXT)

        # Check that the file exists 
        self.path = self.path.absolute()
        if not self.path.exists() or not self.path.is_file():
            raise FileNotFoundError('%s not found' % str(self.path))

        try:
            self.database = SqliteHelper.connect(str(self.path))
        except Exception as e:
            raise NumbatException(*e.args)

        if clear:
            # Clear the database if the user ask to
            self.clear()

    def create(self, path: pathlib.Path) -> None:
        """
            This method allow to create a sourcetrail database 
            :param path: The path to the new database
            :type path: pathlib.Path | str
            :return: None
            :rtype: NoneType
        """

        # Convert str input
        if type(path) == str:
            path = pathlib.Path(path)

        # Check that a database is not already opened
        if self.database:
            raise AlreadyOpenDatabase()

        self.path = path
        # Check that the file has the correct extension
        if self.path.suffix != self.SOURCETRAIL_DB_EXT:
            self.path = self.path.with_suffix(self.SOURCETRAIL_DB_EXT)

        # Check that the file exists 
        self.path = self.path.absolute()
        if self.path.exists():
            raise FileExistsError('%s already exists' % str(self.path))

        try:
            self.database = SqliteHelper.connect(str(self.path))
        except Exception as e:
            raise NumbatException(*e.args)

        # Try to create the tables
        try:
            self.__create_sql_tables()
            self.__create_project_file()
            self.__add_meta_info()
        except Exception as e:
            # They already exists, fail
            self.close()
            raise NumbatException(*e.args)

    def commit(self) -> None:
        """
            This method allow to commit changes made to a sourcetrail database.
            Any change made to the database using this API will be lost if not 
            committed before closing the database. 
            :return: None
            :rtype: NoneType
        """

        if self.database:
            self.database.commit()
        else:
            raise NoDatabaseOpen()

    def clear(self) -> None:
        """
            Clear all elements present in the database. 
            :return: None
            :rtype: NoneType
        """

        if self.database:
            self.__clear_sql_tables()
        else:
            raise NoDatabaseOpen()

    def close(self) -> None:
        """
            This method allow to close a sourcetrail database.
            The database must be closed after use in order to liberate
            memory and resources allocated for it.
            :return: None
            :rtype: NoneType
        """

        if self.database:
            self.database.close()
            self.database = None
        else:
            raise NoDatabaseOpen()

    def __create_sql_tables(self) -> None:
        """
            This method allow to create all the sql tables needed 
            by sourcetrail 
            :return: None
            :rtype: NoneType
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

    def __clear_sql_tables(self) -> None:
        """
            This method allow to clear all the sql tables 
            used by sourcetrail 
            :return: None
            :rtype: NoneType
        """

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

    def __create_project_file(self) -> None:
        """
            This method create a simple project file 
            for sourcetrail
            :return: None
            :rtype: NoneType
        """

        filename = self.path.with_suffix(self.SOURCETRAIL_PROJECT_EXT)
        filename.write_text(self.SOURCETRAIL_XML)

    def __add_meta_info(self) -> None:
        """
            Add the meta information inside sourcetrail database  
            :return: None
            :rtype: NoneType
        """

        MetaDAO.new(self.database, 'storage_version', '25')
        MetaDAO.new(self.database, 'project_settings', self.SOURCETRAIL_XML)

    # ------------------------------------------------------------------------ #
    # Sourcetrail API (Existing one)                                           #
    # ------------------------------------------------------------------------ #

    def record_symbol(self, hierarchy: NameHierarchy) -> int:
        """
            Record a new Symbol in the database
            :param hierarchy: The hierarchy of the symbol to insert
            :type hierarchy: NameHierarchy
            :return: An unique integer that identify the inserted element
            :rtype: int
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

    def record_symbol_kind(self, id_: int, type_: NodeType) -> None:
        """
            Set the type of the symbol which is equivalent to setting the 
            type of the underlying node.
            :param id_: The identifier of the element 
            :type id_: int
            :param type_: The new type for the symbol 
            :type type_: NodeType
            :return: None
            :rtype: NoneType
        """

        node = NodeDAO.get(self.database, id_)
        if node:
            node.type = type_
            NodeDAO.update(self.database, node)

    def record_symbol_definition_kind(self, id_: int, type_: SymbolType) -> None:
        """
            Set the type of definition of the corresponding element
            :param id_: The identifier of the element 
            :type id_: int
            :param type_: The new type for the symbol 
            :type type_: SymbolType
            :return: None
            :rtype: NoneType
        """

        symb = SymbolDAO.get(self.database, id_)
        if symb and symb.type != type_:
            symb.type = type_
            SymbolDAO.update(self.database, symb)
        else:
            symb = Symbol(id_, type_)
            SymbolDAO.new(self.database, symb)

    def __record_source_location(self, symbol_id: int, file_id: int,
                                 start_line: int, start_column: int, end_line: int, end_column: int,
                                 type_: SourceLocationType) -> None:
        """
            Wrapper for all the record_*_location
            :param symbol_id: The identifier of the symbol 
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element start. 
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :param type_: The type of the source location.
            :type type_: SourceLocationType 
            :return: None
            :rtype: NoneType
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
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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
            :param reference_id: The reference idnetifier
            :type reference_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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

    def record_local_symbol_location(self, symbol_id: int, file_id: int, start_line: int,
                                     start_column: int, end_line: int, end_column: int) -> None:
        """
            Record a new source location of type LOCAL_SYMBOL
            :param symbol_id: The identifier of the symbol 
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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
            :type symbol_id: int
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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

    def record_reference(self, target_id: int, dest_id: int, type_: EdgeType) -> int:
        """
            Add a new reference (aka an edge) between two elements
            :param target_id: The source identifier of the reference
            :type target_id: int
            :param dest_id: The destination identifier of the reference  
            :type dest_id: int 
            :param type_: The type of reference to add
            :type type_: EdgeType
            :return: None
            :rtype: NoneType
        """

        elem = Element()
        elem.id = ElementDAO.new(self.database, elem)

        EdgeDAO.new(self.database, Edge(
            elem.id,
            type_,
            target_id,
            dest_id
        ))

        return elem.id

    def record_reference_is_ambiguous(self, reference_id: int) -> None:
        """
            Add an indication in the database to tell that the reference is ambiguous
            :param reference_id: the identifer of the reference
            :type reference_id: int
            :return: None
            :rtype: NodeType
        """

        ElementComponentDAO.new(self.database, ElementComponent(
            0,
            reference_id,
            ElementComponentType.IS_AMBIGUOUS,
            ''
        ))

    def record_reference_to_unsolved_symbol(self, symbol_id: int, reference_type: EdgeType,
                                            file_id: int, start_line: int, start_column: int, end_line: int,
                                            end_column: int) -> int:
        """
            Record a reference to an unsolved symbol.
            :param symbol_id: The identifier of the symbol 
            :type symbol_id: int
            :param reference_type: The type of reference
            :type reference_type: EdgeType
            :param file_id: The identifier of the source file in which the symbol is located
            :type file_id: int 
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: The identifier of the new reference
            :rtype: int
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
        unsolved_symbol_id = self.record_symbol(hierarchy)

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

    def record_file(self, path: pathlib.Path, indexed: bool = True) -> int:
        """
            Record a source file in the database 
            :param path: The path to the existing source file
            :type path: pathlib.Path
            :param indexed: A boolean that indicates if the source file 
                            was indexed by the parser
            :type indexed: bool
            :return: The identifier of the inserted file
            :rtype: int
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
        modification_time = datetime.datetime.fromtimestamp(
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
            FileContentDAO.new(self.database,
                               FileContent(
                                   elem_id,
                                   ''.join(lines)
                               )
                               )

        # Return the newly created element id
        return elem_id

    def record_file_language(self, id_: int, language: str) -> None:
        """
            Set the language of an existing file inside the database
            :param id_: The identifier of the file 
            :type id_: int
            :param language: A string that indicate the programming language of the file
            :type language: str
            :return: None
            :rtype: NodeType
        """

        file = FileDAO.get(self.database, id_)
        if file:
            file.language = language
            FileDAO.update(self.database, file)

    def record_local_symbol(self, name: str) -> int:
        """
            Record a new local symbol
            :param name: The name of the new local symbol
            :type name: str
            :return: The identifier of the new local symbol
            :rtype: int
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

    def record_error(self, msg: str, fatal: bool, file_id: int, start_line: int,
                     start_column: int, end_line: int, end_column: int) -> None:
        """
            Record a new indexer error in the database 
            :param msg: The description of the error
            :type msg: str
            :param fatal: A boolean indicating if the error stop the execution of the parser
            :type fatal: bool
            :param file_id: The identifier of the source file being parsed
            :type file_id: int
            :param start_line: The line at which the element starts.
            :type start_line: int
            :param start_column: The column at which the element starts.
            :type start_column: int
            :param end_line: The line at which the element ends.
            :type end_line: int
            :param end_column: The line at which the element ends.
            :type end_column: int
            :return: None
            :rtype: NoneType
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

    # ------------------------------------------------------------------------ #
    # Sourcetrail API (New features)                                           #
    # ------------------------------------------------------------------------ #

    def __add_if_not_existing(self, name: str, type_: NodeType) -> int:
        """
            Create a new node if it does not already exist
              
            @Warning: This is not the same behavior as SourcetrailDB
            We are not allowing nodes with same serialized_name

            :param name: The serialized_name of the node
            :type name: str
            :param type_: The type of the node to insert
            :type type_: NodeType
            :return: The identifier of the new node or the identifier of 
                     the existing one
            :rtype: int
        """

        node = NodeDAO.get_by_name(self.database, name)
        if not node:
            elem = Element()
            elem.id = ElementDAO.new(self.database, elem)

            NodeDAO.new(self.database, Node(
                elem.id,
                type_,
                name
            ))

            return elem.id
        else:
            return node.id

    def get_symbol(self, hierarchy: NameHierarchy) -> int | None:
        """
            Return the corresponding Symbol from the database
            :param hierarchy: The hierarchy of the symbol to retrieve
            :type hierarchy: NameHierarchy
            :return: The identifier of the existing symbol or None if the symbol
                     does not exist.
            :rtype: int | None
        """

        serialized_name = hierarchy.serialize_name()
        node = NodeDAO.get_by_name(self.database, serialized_name)
        if node:
            return node.id

    def record_symbol_child(self, parent_id: int, element: NameElement) -> int | None:
        """
            Add a child to an existing node without having to give the full
            hierarchy of the element
            :param parent_id: The identifier of the existing parent
            :type parent_id: int
            :param element: The new element to insert
            :type element: NameElement
            :return: The identifier of the newly inserted symbol or None if the parent
                     does not exist.
            :rtype: int | None
        """

        node = NodeDAO.get(self.database, parent_id)
        if node:
            hierarchy = NameHierarchy.deserialize_name(node.name)
            hierarchy.extend(element)
            return self.record_symbol(hierarchy)

    def record_class(self, prefix: str = '', name: str = '', postfix: str = '',
                     delimiter: str = NameHierarchy.NAME_DELIMITER_CXX) -> int | None:
        """
            Higher level method that hide the NameHierarchy from the user
            :param prefix: The prefix of the element to insert
            :type prefix: str
            :param name: The name of the element to insert
            :type name: str
            :param postfix: The postfix of the element to insert
            :type postfix: str
            :param delimiter: The delimiter of the element 
            :type delimiter: str
            :return: The identifier of the new class or None if it could not be inserted
            :rtype: int | None
        """

        class_id = self.record_symbol(NameHierarchy(
            delimiter,
            [NameElement(
                prefix,
                name,
                postfix
            )]
        ))

        if class_id:
            self.record_symbol_kind(class_id, NodeType.NODE_CLASS)
            return class_id

    def record_function(self, prefix: str = '', name: str = '', postfix: str = '',
                        delimiter: str = NameHierarchy.NAME_DELIMITER_CXX) -> int | None:
        """
            Higher level method that hide the NameHierarchy from the user
            :param prefix: The prefix of the element to insert
            :type prefix: str
            :param name: The name of the element to insert
            :type name: str
            :param postfix: The postfix of the element to insert
            :type postfix: str
            :param delimiter: The delimiter of the element 
            :type delimiter: str
            :return: The identifier of the new function or None if it could not be inserted
            :rtype: int | None
        """

        func_id = self.record_symbol(NameHierarchy(
            delimiter,
            [NameElement(
                prefix,
                name,
                postfix
            )]
        ))

        if func_id:
            self.record_symbol_kind(func_id, NodeType.NODE_FUNCTION)
            return func_id

    def record_method(self, parent: int, prefix: str = '', name: str = '',
                      postfix: str = '') -> int | None:
        """
            Higher level method that hide the NameHierarchy from the user
            :param parent: The identifier of the class in which the method is defined.
            :type parent: int
            :param prefix: The prefix of the element to insert
            :type prefix: str
            :param name: The name of the element to insert
            :type name: str
            :param postfix: The postfix of the element to insert
            :type postfix: str
            :return: The id of the new method or None if it could not be inserted
            :rtype: int | None
        """

        method = self.record_symbol_child(parent, NameElement(
            prefix,
            name,
            postfix
        ))
        if method:
            self.record_symbol_kind(method, NodeType.NODE_METHOD)
            return method

    def record_field(self, parent: int, prefix: str = '', name: str = '',
                     postfix: str = '') -> int | None:
        """
            Higher level method that hide the NameHierarchy from the user
            :param parent: The identifier of the class in which the field is defined.
            :type parent: int
            :param prefix: The prefix of the element to insert
            :type prefix: str
            :param name: The name of the element to insert
            :type name: str
            :param postfix: The postfix of the element to insert
            :type postfix: str
            :return: The id of the new field or None if it could not be inserted
            :rtype: int | None
        """

        field = self.record_symbol_child(parent, NameElement(
            prefix,
            name,
            postfix
        ))
        if field:
            self.record_symbol_kind(field, NodeType.NODE_FIELD)
            return field
