from pkmidicron import engine

print('>>> ctor')
p1 = engine.Patch()
print('>>> binding')
b = p1.addBinding()
print('>>> remove')
p1.removeBinding(b)
b = None
print('>>> del')
p1 = None
print('>>> done')

