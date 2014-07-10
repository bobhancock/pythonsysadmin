class NoSlots(object):
    def init(self, i, lst):
        self.x = i
        self.y = lst

def Slots(object):
    __slots__ = ('x', 'y')
    x = 10
    def __init__(self):
        self.y = 2    