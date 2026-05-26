import sys
def execute_error_block(error_message):
    print('============== ERROR BLOCK ==============')
    print(error_message)
    print(f"\n------------Stopping the program ------------")
    sys.exit()