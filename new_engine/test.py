class Main:
    def __init__(self):
        self.a = 5
        self.sub = Sub(self)

class Sub:
    def __init__(self, main):
        print(main.sub.a)

Main()