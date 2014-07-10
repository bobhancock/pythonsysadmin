import os
from dry.logger import setup_logging
from dry.co import coroutine

@coroutine
def find_file(target_coroutine):
    while True:
        home = (yield)
        for dirpath, dirs, files in os.walk(home, topdown=True):
            for f in files:
                fname = os.path.join(dirpath, f)            
                target_coroutine.send(fname)
            
@coroutine
def stat_file(target_courotine):
    while True:
        fname= (yield)
        target_courotine.send( (fname, os.stat(fname).st_atime))
    
@coroutine
def logit(fh_out):
    while True:
        fname, stat = (yield)
        fh_out.write("{f}|{s}\n".format(f=fname, s=stat))

    
#home = "/var/tmp/dirwalk/test0"    
home = "/var/tmp/dirwalk"    
fout = "/var/tmp/dirwalk_pipeline.txt"

with open(fout, "w") as fh:
    f = find_file( stat_file( logit(fh)))
    f.send(home)
    
print("Done")