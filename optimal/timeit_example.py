"""
Compare the libray function for square root with multiplication.
"""
import math
from timeit import timeit

print( timeit(stmt="math.pow(2, 24)", setup="import math", number=10000))
print( timeit(stmt="2**24", setup="import math", number=10000))
