# Test list comprehension versus loop
import time

n = 1000000000

lst = []
t0 = time.time()
for i in range(n):
   lst.append(i)
print("Loop with append: {t}".format(t=time.time() - t0))
      
t0 = time.time()
l = [i for i in range(n)]
print ("List comprehension: {t}".format(time.time() - s))
    
