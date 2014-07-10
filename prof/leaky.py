class MyBigFatObject(object):
    pass

def computate_something(_cache={}):
    _cache[42] = dict(foo=MyBigFatObject(),
                      bar=MyBigFatObject())
    # a very explicit and easy-to-find "leak" 
    x = MyBigFatObject() # this one doesn't leak