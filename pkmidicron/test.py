class A:
    def __init__(self, a):
        self.a = a

    def init(self, x):
        self.x = x

class B(A):
    def __init__(self, a):
        super().__init__(a)

    def init(self, x):
        super().init(x)
        self.y = x

b = B(1)
b.init(2)
print(b.a, b.x, b.y)
