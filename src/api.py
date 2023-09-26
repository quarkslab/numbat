import os
import pathlib
import datetime

import base
import dao


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

    # ------------------------------------------------------------------------ #
    # Database file management functions                                       #
    # ------------------------------------------------------------------------ #

    def open(self, path: pathlib.Path) -> None:
        """ 
            This method allow to open an existing sourcetrail database 
        """

        # Convert str input
        if type(path) == str:
            path = pathlib.Path(path)

        # Check that a database is not already opened
        if self.database:
            raise Exception('Database already opened')

        self.path = path
        # Check that the file has the correct extension
        if self.path.suffix != self.SOURCETRAIL_DB_EXT:
            self.path = self.path.with_suffix(self.SOURCETRAIL_DB_EXT)

        # Check that the file exists 
        self.path = self.path.absolute()
        if not self.path.exists() or not self.path.is_file():
            raise Exception('File not found')

        self.database = dao.SqliteHelper.connect(str(self.path))

    def create(self, path: pathlib.Path) -> None:
        """
            This method allow to create a sourcetrail database 
        """
        # Convert str input
        if type(path) == str:
            path = pathlib.Path(path)

        # Check that a database is not already opened
        if self.database:
            raise Exception('Database already opened')

        self.path = path
        # Check that the file has the correct extension
        if self.path.suffix != self.SOURCETRAIL_DB_EXT:
            self.path = self.path.with_suffix(self.SOURCETRAIL_DB_EXT)

        # Check that the file exists 
        self.path = self.path.absolute()
        if self.path.exists():
            raise Exception('File already exists')

        self.database = dao.SqliteHelper.connect(str(self.path))
        # Try to create the tables
        try:
            self.__create_sql_tables()
            self.__create_project_file()
            self.__add_meta_info()
        except Exception as e:
            # They already exists, fail
            self.close()
            raise e

    def commit(self) -> None:
        """
            This method allow to commit changes made to a sourcetrail database
        """
        if self.database:
            self.database.commit()
        else:
            raise Exception('Database is not opened yet')

    def clear(self) -> None:
        """
            Clear all elements present in the database 
        """
        self.__clear_sql_tables()

    def close(self) -> None:
        """
            This method allow to close a sourcetrail database
        """
        if self.database:
            self.database.close()
            self.database = None
        else:
            raise Exception('Database is not opened yet')

    def __create_sql_tables(self) -> None:
        """
            This method allow to create all the sql tables needed 
            by sourcetrail 
        """
        dao.ElementDAO.create_table(self.database)
        dao.ElementComponentDAO.create_table(self.database)
        dao.EdgeDAO.create_table(self.database)
        dao.NodeDAO.create_table(self.database)
        dao.SymbolDAO.create_table(self.database)
        dao.FileDAO.create_table(self.database)
        dao.FileContentDAO.create_table(self.database)
        dao.LocalSymbolDAO.create_table(self.database)
        dao.SourceLocationDAO.create_table(self.database)
        dao.OccurrenceDAO.create_table(self.database)
        dao.ComponentAccessDAO.create_table(self.database)
        dao.ErrorDAO.create_table(self.database)
        dao.MetaDAO.create_table(self.database)

    def __clear_sql_tables(self) -> None:
        """
            This method allow to clear all the sql tables 
            used by sourcetrail 
        """
        dao.ElementDAO.clear(self.database)
        dao.ElementComponentDAO.clear(self.database)
        dao.EdgeDAO.clear(self.database)
        dao.NodeDAO.clear(self.database)
        dao.SymbolDAO.clear(self.database)
        dao.FileDAO.clear(self.database)
        dao.FileContentDAO.clear(self.database)
        dao.LocalSymbolDAO.clear(self.database)
        dao.SourceLocationDAO.clear(self.database)
        dao.OccurrenceDAO.clear(self.database)
        dao.ComponentAccessDAO.clear(self.database)
        dao.ErrorDAO.clear(self.database)

    def __create_project_file(self) -> None:
        """
            This method create a simple project file 
            for sourcetrail
        """

        filename = self.path.with_suffix(self.SOURCETRAIL_PROJECT_EXT)
        filename.write_text(self.SOURCETRAIL_XML)

    def __add_meta_info(self) -> None:
        """
            Add the meta information inside sourcetrail database  
        """
        dao.MetaDAO.new(self.database, 'storage_version', '25')
        dao.MetaDAO.new(self.database, 'project_settings', self.SOURCETRAIL_XML)

    # ------------------------------------------------------------------------ #
    # Sourcetrail API (Existing one)                                           #
    # ------------------------------------------------------------------------ #

    def record_symbol(self, hierarchy: base.NameHierarchy) -> int:
        """
            Record a new Symbol in the database
        """

        ids = []

        # Add all the nodes needed 
        for i in range(0, hierarchy.size()):
            ids.append(self.__add_if_not_existing(
                hierarchy.serialize_range(0, i + 1),
                base.NodeType.NODE_SYMBOL
            ))

        # Add all the edges between nodes
        if len(ids) > 1:
            parent, children = ids[0], ids[1:]
            for child in children:
                elem = base.Element()
                elem.id = dao.ElementDAO.new(self.database, elem)

                dao.EdgeDAO.new(self.database, base.Edge(
                    elem.id,
                    base.EdgeType.MEMBER,
                    parent,
                    child
                ))

                # Return the id of the last inserted elements
        return ids[-1]

    def record_symbol_kind(self, id_: int, type_: base.NodeType) -> None:
        """
            Set the type of the symbol which is equivalent to setting the 
            type of the underlying node.
        """
        node = dao.NodeDAO.get(self.database, id_)
        if node:
            node.type = type_
            dao.NodeDAO.update(self.database, node)

    def record_symbol_definition_kind(self, id_: int, type_: base.SymbolType) -> None:
        """
            Set the type of definition of the corresponding element
        """
        symb = dao.SymbolDAO.get(self.database, id_)
        if symb and symb.type != type_:
            symb.type = type_
            dao.SymbolDAO.update(self.database, symb)
        else:
            symb = base.Symbol(id_, type_)
            dao.SymbolDAO.new(self.database, symb)

    def __record_source_location(self, symbol_id: int, file_id: int,
                                 start_line: int, start_column: int, end_line: int, end_column:
            int, type_: base.SourceLocationType) -> None:

        """
            Wrapper for all the record_*_location
        """
        # First add a new source location entry
        loc_id = dao.SourceLocationDAO.new(self.database, base.SourceLocation(
            0,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            type_
        ))

        # Now add an occurrence that refer to this location
        dao.OccurrenceDAO.new(self.database, base.Occurrence(
            symbol_id, loc_id
        ))

    def record_symbol_location(self, symbol_id: int, file_id: int, start_line: int,
                               start_column: int, end_line: int, end_column: int) -> None:

        """
            Record a new source location of type TOKEN
        """
        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.TOKEN
        )

    def record_symbol_scope_location(self, symbol_id: int, file_id: int, start_line: int,
                                     start_column: int, end_line: int, end_column: int) -> None:
        """
            Record a new source location of type SCOPE
        """
        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.SCOPE
        )

    def record_symbol_signature_location(self, symbol_id: int, file_id: int, start_line: int,
                                         start_column: int, end_line: int, end_column: int) -> None:
        """
            Record a new source location of type SCOPE
        """
        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.SIGNATURE
        )

    def record_reference(self, target_id: int, dest_id: int, type_: base.EdgeType) -> int:
        """
            Add a new reference (aka an edge) between two elements
        """
        elem = base.Element()
        elem.id = dao.ElementDAO.new(self.database, elem)

        dao.EdgeDAO.new(self.database, base.Edge(
            elem.id,
            type_,
            target_id,
            dest_id
        ))

        return elem.id

    def record_reference_location(self, reference_id: int, file_id: int, start_line: int,
                                  start_column: int, end_line: int, end_column: int) -> None:

        """
            Record a new reference location of type TOKEN
        """
        self.__record_source_location(
            reference_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.TOKEN
        )

    def record_reference_is_ambiguous(self, reference_id: int) -> None:
        """
            Add an indication in the database to tell that the reference is ambiguous
        """
        dao.ElementComponentDAO.new(self.database, base.ElementComponent(
            0,
            reference_id,
            base.ElementComponentType.IS_AMBIGUOUS,
            ''
        ))

    def record_reference_to_unsolved_symbol(self, symbol_id: int, reference_type: base.EdgeType,
                                            file_id: int, start_line: int, start_column: int, end_line: int,
                                            end_column: int):

        # Don't blame me, it's done like this in sourcetrail source code
        hierarchy = base.NameHierarchy(
            base.NameHierarchy.NAME_DELIMITER_UNKNOWN,
            [base.NameElement(
                '',
                'unsolved symbol',
                ''
            )]
        )

        # Insert the new node
        unsolved_symbol_id = self.record_symbol(hierarchy)

        # Add a new edge
        elem = base.Element()
        elem.id = dao.ElementDAO.new(self.database, elem)

        reference_id = dao.EdgeDAO.new(self.database, base.Edge(
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
            base.SourceLocationType.UNSOLVED
        )

        # Return edge id
        return reference_id

    def record_qualifier_location(self, symbol_id: int, file_id: int, start_line: int,
                                  start_column: int, end_line: int, end_column: int) -> None:

        """
            Record a new source location of type QUALIFIER
        """
        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.QUALIFIER
        )

    def record_file(self, path: pathlib.Path, indexed: bool = True) -> int:

        if not path.exists() or not path.is_file():
            raise Exception('File not found')

        # Create a new name hierarchy 
        hierarchy = base.NameHierarchy(
            base.NameHierarchy.NAME_DELIMITER_FILE,
            [base.NameElement(
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
            base.NodeType.NODE_FILE
        )

        # Insert a new file
        dao.FileDAO.new(
            self.database,
            base.File(
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
            dao.FileContentDAO.new(self.database,
                                   base.FileContent(
                                       elem_id,
                                       ''.join(lines)
                                   )
                                   )

            # Return the newly created element id
        return elem_id

    def record_file_language(self, id_: int, language: str) -> None:
        """
            Set the language of an existing file inside the database
        """
        file = dao.FileDAO.get(self.database, id_)
        if file:
            file.language = language
            dao.FileDAO.update(self.database, file)

    def record_local_symbol(self, name: str):
        # Check that the symbol does not already exist
        local = dao.LocalSymbolDAO.get_from_name(self.database, name)
        if not local:
            # Insert a new local symbol
            elem = base.Element()
            elem.id = dao.ElementDAO.new(self.database, elem)
            local = base.LocalSymbol(elem.id, name)
            dao.LocalSymbolDAO.new(self.database, local)

        return local.id

    def record_local_symbol_location(self, symbol_id: int, file_id: int, start_line: int,
                                     start_column: int, end_line: int, end_column: int) -> None:

        """
            Record a new source location of type LOCAL_SYMBOL
        """
        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.LOCAL_SYMBOL
        )

    def record_atomic_source_range(self, symbol_id: int, file_id: int, start_line: int,
                                   start_column: int, end_line: int, end_column: int) -> None:

        """
            Record a new source location of type ATOMIC_RANGE
        """
        self.__record_source_location(
            symbol_id,
            file_id,
            start_line,
            start_column,
            end_line,
            end_column,
            base.SourceLocationType.ATOMIC_RANGE
        )

    def record_error(self, msg: str, fatal: bool, file_id: int, start_line: int,
                     start_column: int, end_line: int, end_column: int) -> None:

        """
            Record a new indexer error in the database 
        """

        error_id = dao.ErrorDAO.new(self.database, base.Error(
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
            base.SourceLocationType.INDEXER_ERROR
        )

    # ------------------------------------------------------------------------ #
    # Sourcetrail API (New features)                                           #
    # ------------------------------------------------------------------------ #

    def __add_if_not_existing(self, name: str, type_: base.NodeType) -> int:
        """
            Create a new node if it doesn't already exist
              
            @Warning: This is not the same behavior as SourcetrailDB
            We are not allowing nodes with same serialized_name
        """
        node = dao.NodeDAO.get_by_name(self.database, name)
        if not node:
            elem = base.Element()
            elem.id = dao.ElementDAO.new(self.database, elem)

            dao.NodeDAO.new(self.database, base.Node(
                elem.id,
                type_,
                name
            ))

            return elem.id
        else:
            return node.id

    def get_symbol(self, hierarchy: base.NameHierarchy) -> int:
        """
            Return the corresponding Symbol from the database
        """

        serialized_name = hierarchy.serialize_name()
        node = dao.NodeDAO.get_by_name(self.database, serialized_name)
        if node:
            return node.id

    def record_symbol_child(self, parent_id: int, element: base.NameElement) -> int:
        """
            Add a child to an existing node without having to give the full
            hierarchy of the element
        """

        node = dao.NodeDAO.get(self.database, parent_id)
        if node:
            hierarchy = base.NameHierarchy.deserialize_name(node.name)
            hierarchy.extend(element)
            return self.record_symbol(hierarchy)


def main():
    srctrl = SourcetrailDB()
    try:
        srctrl.create('generated/database')
    except Exception as e:
        print(e)
        srctrl.open('generated/database')
        srctrl.clear()

    # ----- Test for SourcetrailDB core features ----- #
    file_id = srctrl.record_file(pathlib.Path('generated/file.py'))
    srctrl.record_file_language(file_id, 'python')

    symbol_id = srctrl.record_symbol(base.NameHierarchy(
        base.NameHierarchy.NAME_DELIMITER_JAVA,
        [base.NameElement(
            '',
            'MyType',
            ''
        )]
    ))
    srctrl.record_symbol_definition_kind(symbol_id, base.SymbolType.EXPLICIT)
    srctrl.record_symbol_kind(symbol_id, base.NodeType.NODE_CLASS)
    srctrl.record_symbol_location(symbol_id, file_id, 2, 7, 2, 12)
    srctrl.record_symbol_scope_location(symbol_id, file_id, 2, 1, 7, 1)

    member_id = srctrl.record_symbol(base.NameHierarchy(
        base.NameHierarchy.NAME_DELIMITER_JAVA,
        [base.NameElement(
            '',
            'MyType',
            ''
        ), base.NameElement(
            '',
            'my_member',
            ''
        )]
    ))
    srctrl.record_symbol_definition_kind(member_id, base.SymbolType.EXPLICIT)
    srctrl.record_symbol_kind(member_id, base.NodeType.NODE_FIELD)
    srctrl.record_symbol_location(member_id, file_id, 4, 2, 4, 10)

    method_id = srctrl.record_symbol(base.NameHierarchy(
        base.NameHierarchy.NAME_DELIMITER_JAVA,
        [base.NameElement(
            '',
            'MyType',
            ''
        ), base.NameElement(
            '',
            'my_method',
            ''
        )]
    ))
    srctrl.record_symbol_definition_kind(method_id, base.SymbolType.EXPLICIT)
    srctrl.record_symbol_kind(method_id, base.NodeType.NODE_METHOD)
    srctrl.record_symbol_location(method_id, file_id, 6, 6, 6, 14)
    srctrl.record_symbol_scope_location(method_id, file_id, 6, 1, 7, 1)

    useage_id = srctrl.record_reference(method_id, member_id, base.EdgeType.USAGE)
    srctrl.record_reference_location(useage_id, file_id, 7, 10, 7, 18)

    # ----- Test for new features ----- #

    # This should return the same id as the one we inserted
    symbol_id_ = srctrl.record_symbol(base.NameHierarchy(
        base.NameHierarchy.NAME_DELIMITER_JAVA,
        [base.NameElement(
            '',
            'MyType',
            ''
        )]
    ))
    assert (symbol_id == symbol_id_)

    # Add a child to a symbol without having to give his whole hierarchy
    srctrl.record_symbol_child(symbol_id, base.NameElement('', 'my_other_method', ''))

    srctrl.commit()
    srctrl.close()


if __name__ == '__main__':
    main()
