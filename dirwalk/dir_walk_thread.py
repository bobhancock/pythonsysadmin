import os
from Queue import Queue
import threading

def find_files(base_dir, consumer_q):                         
    """
    Find each file under the base dir and place it on the consumer queue.
    """
    for dirpath, dirs, files in os.walk(base_dir, topdown=False):
        for f in files:
            fname = os.path.join(dirpath, f)
            stat = os.stat(fname).st_mtime
            consumer_q.put(fname, stat)                
                

def logit(fh_out, consumer_q):
    while True:
        r = consumer_q.get()
        if not r:
            break
        
        fname, stat = r
        fh_out.write("{f}|{s}\n".format(f=fname,s=stat))
        
base_dirs = ("/var/tmp/dirwalk/test0", "/var/tmp/dirwalk/test1",
             "/var/tmp/dirwalk/test2","/var/tmp/dirwalk/test3",
             "/var/tmp/dirwalk/test4")

# Start execution
producer_func = find_files
consumer_q = Queue()
producers = []


fh_out =  open("/var/tmp/dirwalk_threaded.txt", "w") 
    
# consumer
for dr in base_dirs:
    th = threading.Thread(name="producer", target=producer_func,
                          args=(dr, consumer_q))
    th.daemon = True
    producers.append(th)
    th.start()

for th in producers:
    th.join()
    