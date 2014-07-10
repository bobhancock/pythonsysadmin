"""
Test join and concatenation.

Bob Hancock - hancock.robert@gmail.com
"""
import pdb
import random
import time
import sys
from optparse import OptionParser


def test_data_uniform(size):
    """ Create a list of random strings of relative uniform size. """
    chunks = []
    for i in range(size):
        chunks.append(str(random.random()))
        
    return chunks


def test_data_nonuniform(size):
    """ Create a list of random strings of increasing non-uniform size.
    Shuffle the result to insure that there is not a monotonic increase in size
    of elements."""
    chunks = []
    for i in range(size):
        c= ""
        for j in range(i):
            c += str(random.random())
        chunks.append(c)
        
    random.shuffle(chunks)
    return chunks


def join_chunks(chunks, join_time):
    start = time.time()
    r = "".join(chunks)
    join_time.append(time.time() - start)
    
    
def concat_chunks(chunks, concat_time): 
    r = ""
    start = time.time()
    for c in chunks:
        r += c
    concat_time.append(time.time() - start)
    
    
def fmt_times(times):
    return "total time: {total} min: {min} max: {max} mean: {mean}".format(total=sum(times),min=min(times), max=max(times), mean=sum(times)/len(times))

#@profile    
def testit(n, uniform=True):
    """
    Returns a dict with the join and concat times.
    """
    
    concat_time = []
    join_time = []

    # Create lists of size n
    if uniform:
        chunks = test_data_uniform(n)
    else:
        chunks = test_data_nonuniform(n)

    # Concat and join each list n times and record the time for each.
    for i in range(n):
        join_chunks(chunks, join_time)
        concat_chunks(chunks, concat_time)
    
    u = "uniform" if uniform else "non-uniform"
    
    print("-"*40)
    print("{u} size data n={n}".format(u=u, n=n))
    print("join - "+fmt_times(join_time))
    print("concat - "+fmt_times(concat_time))
    print("")
    
    return {"join": join_time, "concat": concat_time}
    
def fmt_diff(dtimes):
    concat = sum(dtimes["concat"])
    join = sum(dtimes["join"])
    
    diff = max(concat, join) - min(concat, join)

    if concat < join:
        print("===> concat is {s} seconds faster.".format(s=diff))
    elif join < concat:
        print("===> join is {s} seconds faster.".format(s=diff))
    else:
        print("===>join and concat take the same amount of time.")
        
    print("-"*40)
    print("")
    

def main():
    usage = 'usage: %prog -d'
    parser = OptionParser(usage)
    parser.set_defaults(downloadFiles=False)
    parser.add_option("-d", "--debug", dest="is_debug", 
                      action="store_true",
                      help="Activate pdb.set_trace()")
    
    [options, arg] = parser.parse_args()
    is_debug = True if options.is_debug else False 
    
    fmt_diff(testit(50, uniform=True))
    fmt_diff(testit(50,uniform=False))
    if is_debug:
        pdb.set_trace()
        
    fmt_diff(testit(500, uniform=True))
    fmt_diff(testit(500, uniform=False))
    if is_debug:
        pdb.set_trace()
        
    fmt_diff(testit(5000, uniform=True))
    fmt_diff(testit(5000, uniform=False))   #you need a lot of memory!
    if is_debug:
        pdb.set_trace()

if __name__ == "__main__":
    sys.exit(main())