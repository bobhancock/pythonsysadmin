from prof.timer import Timer
from redis import Redis
rdb = Redis()

with Timer(verbose=True) as t:
    rdb.lpush("foo", "bar")
print "=> elasped lpush: %s s" % t.secs

with Timer() as t:
    rdb.lpop("foo")
print "=> elasped lpop: %s s" % t.secs
