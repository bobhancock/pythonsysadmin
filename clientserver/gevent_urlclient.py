import sys
import urllib2
import time
from statlib import stats

import gevent
from gevent import monkey
# patches stdlib (including socket and ssl modules) to cooperate with other greenlets
monkey.patch_all()
from gevent import queue

urls = ["http://www.python.org",
	"http://www.ibm.com",
	"http://google.com",
	"http://www.bbc.co.uk/",
	"http://www.json.org/",
	"http://www.lemonde.fr/",
	"http://yahoo.com",
	"http://www.amazon.com",
	"http://www.cnn.com",
	"http://www.nytimes.com",
	"http://www.bradmehldau.com",
	"http://bobhancock.org",
	"http://eventlet.net/doc/design_patterns.html",
	"http://golang.org/doc/effective_go.html",
	"http://docs.sun.com/source/816-6698-10/replicat.html",
	"http://rss.cnn.com/rss/cnn_world.rss",
	"http://rss.cnn.com/rss/cnn_us.rss",
	"http://rss.cnn.com/rss/si_topstories.rss",
	"http://rss.cnn.com/rss/money_latest.rss",
	"http://rss.cnn.com/rss/cnn_allpolitics.rss",
	"http://rss.cnn.com/rss/cnn_crime.rss",
	"http://rss.cnn.com/rss/cnn_tech.rss",
	"http://rss.cnn.com/rss/cnn_space.rss",
	"http://rss.cnn.com/rss/cnn_health.rss",
	"http://rss.cnn.com/rss/cnn_showbiz.rss",
	"http://rss.cnn.com/rss/cnn_travel.rss",
	"http://rss.cnn.com/rss/cnn_living.rss",
	"http://rss.cnn.com/rss/cnn_freevideo.rss",
	"http://rss.cnn.com/rss/cnn_mostpopular.rss",
	"http://rss.cnn.com/rss/cnn_latest.rss",
	"http://www.nytimes.com/services/xml/rss/nyt/Business.xml",
	"http://finance.yahoo.com/rss/headline?s=mhp",
	"http://www.ft.com/servicestools/newstracking/rss#world",
	"http://finance.yahoo.com/rss/headline?s=mhp",
	"http://golang.org"]

qtimes = queue.Queue()
qerr = queue.Queue()
qstart = queue.Queue()


def get_url(url):
    global  qtimes, qerr, qstart
    #//print ('Starting %s' % url)
    start = time.time()
    qstart.put(start)
    try:
        data = urllib2.urlopen(url).read()
    except Exception as e:
        msg="{u} exception: {e}".format(u=url, e=e)
        qerr.put(msg)
              
    qtimes.put(time.time() - start)
    #print ('%s: %s bytes: %r' % (url, len(data), data[:50]))
    print ('%s: %s bytes' % (url, len(data)))


def main():
    global qtimes,qerr
    reps = int(sys.argv[1])
    
    for j in range(reps):
        jobs = [gevent.spawn(get_url, url) for url in urls]
        #print("Size of jobs is {n}".format(n=len(jobs)))
        gevent.joinall(jobs, timeout=30)
    
    if not qerr.empty():
        qerr.put(StopIteration)
        for err in qerr:
            print(err)
           
    print("jobs size {s}".format(s=len(jobs)))
    print("qstart size {n}".format(n=qstart.qsize()))
    print("qtimes size {n}".format(n=qtimes.qsize()))
    qtimes.put(StopIteration)
    times = []
    for item in qtimes:
        times.append(item)
        
    print("Min {t}".format(t=min(times)))
    print("Max {t}".format(t=max(times)))
    print("Mean {t}".format(t=stats.mean(times)))
    print("StdDev {t}".format(t=stats.stdev(times)))
    

if __name__ == "__main__":
    sys.exit(main())
