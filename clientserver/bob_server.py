from gevent.server import StreamServer
import gevent
import signal
from gevent.monkey import patch_all
import time
import sys

# handler will be run for each incoming connection in a dedicated greenlet
def echo(socket, address):
    #print ('New connection from %s:%s' % address)
    # makefile because we readline()
    fileobj = socket.makefile()
    
    line = fileobj.readline()
    #print("read {l}".format(l=line))
    if not line:
        #break
        return
    if line.strip().lower() == 'quit':
        print ("client quit "+str(time.time()))
        fileobj.write("ACK\n")
        fileobj.flush()
#        break
    else:
        request_num = line.split(":")[0]
        fileobj.write(line)
        fileobj.flush()
#        print ("echoed %r" % line)


if __name__ == '__main__':
    port = 2020
    server = StreamServer(('0.0.0.0', port), echo)
    # to start the server asynchronously, use its start() method;
    # we use blocking serve_forever() here because we have no other jobs
    print ('Starting echo server on port {p}'.format(p=port))
    # Add some signal handlers to quit the server gracefully.
    gevent.signal(signal.SIGTERM, exit, server)
    gevent.signal(signal.SIGQUIT, exit, server)
    gevent.signal(signal.SIGINT, exit, server)
    
    server.serve_forever()
