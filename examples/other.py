from numbat import SourcetrailDB

def main():
    srctrl = SourcetrailDB()
    try:
        srctrl.create('database')
    except Exception as e:
        print(e)
        srctrl.open('database')
        srctrl.clear()

    print('Starting')

    cls = srctrl.record_class(name='MyClass')
    method = srctrl.record_method(cls, name='MyMethod')

    srctrl.commit()
    srctrl.close()

    print('Ending')
   
    
if __name__ == '__main__':
    main()
