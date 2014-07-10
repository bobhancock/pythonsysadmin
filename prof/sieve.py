"""
prime sieve
"""
import pdb
from sys import exit
from time import clock

n = input('Prime Number(>2) Upto:')
if n < 2:
    exit(1)
t = clock()                       # Starting counter


#@profile
def sieve():
    # initializing list of odd numbers from 3 to n
    s = range(3, n, 2)
    p = [2]                     # initializing list of primes with 2
    large, limit = s[-1], s.index(s[-1])
    i = 0                       # pointer to the first non zero element of s
    while True:
        while not s[i]:         # finding first non zero element of s
            s[i] = 0
            i += 1
        p.append(s[i])          # adding that to the list p

        m = s[i]
        if m ** 2 > large:
            pdb.set_trace()
            s[i] = 0            # add all rest of element of s and break loop
            p += [prime for prime in s if prime]

           #p = []
           # for prime in s:
           #     if prime:
           #        p.append(prime)
                    
            break
        ind = (m * (m - 1) / 2) + i

        while ind <= limit:
            s[ind] = 0          # marking all the multiples
            ind += m
        s[i] = 0                # marking the prime already found

    # print p
    print 'Number of Primes upto %d: %d' % (n, len(p))
    print 'Time Taken:', clock() - t, 'seconds'

sieve()
