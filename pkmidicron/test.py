import rtmidi
import sys
import types
import time
import gc


s = """
class A:
    def __del__(self):
        print('__del__')
a = A()
"""

mod = types.ModuleType('spam')
exec(s, mod.__dict__)
print('deleting...', mod.a)
print([m for m in gc.get_objects() if isinstance(m, types.ModuleType) and m.__name__ == 'spam'])
mod = None
print([m for m in gc.get_objects() if isinstance(m, types.ModuleType) and m.__name__ == 'spam'])
print('done')


#m = 
#rtmidi.delete_module(rtmidi.new_module('mine'),)
#m = None
# print('refs: %i' % sys.getrefcount(m))
# print('refs: %i' % sys.getrefcount(m))
# m = None
#print('exit')
#time.sleep(100)
