from numbat import SourcetrailDB
from numbat.base import NameHierarchy, NameElement, SymbolType, NodeType, EdgeType

import pathlib

def main():
    srctrl = SourcetrailDB()
    try:
        srctrl.create('database')
    except Exception as e:
        print(e)
        srctrl.open('database')
        srctrl.clear()

    print('Starting')

    # ----- Test for SourcetrailDB core features ----- #

    file_id = srctrl.record_file(pathlib.Path('file.py'))
    srctrl.record_file_language(file_id, 'python')

    symbol_id = srctrl.record_symbol(NameHierarchy(
        NameHierarchy.NAME_DELIMITER_JAVA,
        [NameElement(
            '',
            'MyType',
            ''
        )]
    ))
    srctrl.record_symbol_definition_kind(symbol_id, SymbolType.EXPLICIT)
    srctrl.record_symbol_kind(symbol_id, NodeType.NODE_CLASS)
    srctrl.record_symbol_location(symbol_id, file_id, 2, 7, 2, 12)
    srctrl.record_symbol_scope_location(symbol_id, file_id, 2, 1, 7, 1)

    member_id = srctrl.record_symbol(NameHierarchy(
        NameHierarchy.NAME_DELIMITER_JAVA,
        [NameElement(
            '',
            'MyType',
            ''
        ), NameElement(
            '',
            'my_member',
            ''
        )]
    ))
    srctrl.record_symbol_definition_kind(member_id, SymbolType.EXPLICIT)
    srctrl.record_symbol_kind(member_id, NodeType.NODE_FIELD)
    srctrl.record_symbol_location(member_id, file_id, 4, 2, 4, 10)

    method_id = srctrl.record_symbol(NameHierarchy(
        NameHierarchy.NAME_DELIMITER_JAVA,
        [NameElement(
            '',
            'MyType',
            ''
        ), NameElement(
            '',
            'my_method',
            ''
        )]
    ))
    srctrl.record_symbol_definition_kind(method_id, SymbolType.EXPLICIT)
    srctrl.record_symbol_kind(method_id, NodeType.NODE_METHOD)
    srctrl.record_symbol_location(method_id, file_id, 6, 6, 6, 14)
    srctrl.record_symbol_scope_location(method_id, file_id, 6, 1, 7, 1)

    useage_id = srctrl.record_reference(method_id, member_id, EdgeType.USAGE)
    srctrl.record_reference_location(useage_id, file_id, 7, 10, 7, 18)

    # Just for testing purpose, let's say that true is a local symbol
    local_symbol = srctrl.record_local_symbol('true')
    srctrl.record_local_symbol_location(local_symbol, file_id, 4, 14, 4, 17)

    # ----- Test for new features ----- #

    # This should return the same id as the one we inserted
    symbol_id_ = srctrl.record_symbol(NameHierarchy(
        NameHierarchy.NAME_DELIMITER_JAVA,
        [NameElement(
            '',
            'MyType',
            ''
        )]
    ))
    assert (symbol_id == symbol_id_)

    # Add a child to a symbol without having to give his whole hierarchy
    srctrl.record_symbol_child(symbol_id, NameElement('', 'my_other_method', ''))

    srctrl.commit()
    srctrl.close()

    print('Ending')

if __name__ == '__main__':
    main()
