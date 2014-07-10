import time
import math

iters = 100000000
t0 = time.time()
for i in range(iters):
    math.sqrt(iters)
print("Module lookup: {t}".format(t=time.time() - t0))
      
sq = math.sqrt
t0 = time.time()
for i in range(iters):
    sq(iters)
print("Module lookup: {t}".format(t=time.time() - t0))

 