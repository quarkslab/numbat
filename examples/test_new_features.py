"""
    This example use numbat to create a sourcetrail project (or open it if it already exists)
    which contains a class providing one method and one field. This example only use the
    same methods as the one defined in the SourcetrailDB project.
"""

from numbat import SourcetrailDB
from numbat.base import SymbolType, EdgeType

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

    # ----- Test for new features ----- #
    file_id = srctrl.record_file(pathlib.Path('file.py'))
    srctrl.record_file_language(file_id, 'python')

    cls_id = srctrl.record_class(name='MyType')

    srctrl.record_symbol_definition_kind(cls_id, SymbolType.EXPLICIT)
    srctrl.record_symbol_location(cls_id, file_id, 2, 7, 2, 12)
    srctrl.record_symbol_scope_location(cls_id, file_id, 2, 1, 7, 1)

    member_id = srctrl.record_field(cls_id, name='my_member')
    srctrl.record_symbol_definition_kind(member_id, SymbolType.EXPLICIT)
    srctrl.record_symbol_location(member_id, file_id, 4, 2, 4, 10)

    method_id = srctrl.record_method(cls_id, name='my_method')
    srctrl.record_symbol_definition_kind(method_id, SymbolType.EXPLICIT)
    srctrl.record_symbol_location(method_id, file_id, 6, 6, 6, 14)
    srctrl.record_symbol_scope_location(method_id, file_id, 6, 1, 7, 1)

    useage_id = srctrl.record_reference(method_id, member_id, EdgeType.USAGE)
    srctrl.record_reference_location(useage_id, file_id, 7, 10, 7, 18)

    srctrl.commit()
    srctrl.close()

    print('Ending')
   
    
if __name__ == '__main__':
    main()
