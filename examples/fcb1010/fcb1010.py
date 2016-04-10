
def init():
    print('fcb1010.init')

class Dtor:
    def __del__(self):
        print("fcb1010.Dtor.print")
d = Dtor()

