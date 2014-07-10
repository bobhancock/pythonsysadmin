import threading
import time

class ListenForShutdownReq(threading.Thread):
    """ Listen for a request to shutdown the server. 
    It assumes that each thread has boolean field 'killMe'
    that when set to True will cause the thread to die 
    elegantly.
    """
    def __init__(self, sockobj, 
                 listthreads, 
                 sleepsecs, 
                 shutdownstring):
        threading.Thread.__init__(self)
        self.name = 'ListenForShutdownReq'
        self.shutdown_string = shutdownstring
        self.sleep_secs = sleepsecs
        self.Kill = False
        self.sockobj = sockobj
        self.threads = listthreads
        self.connection = None
        self.address = None


    def run(self):
        while not self.Kill:
            try:
                clientsock, clientaddr = self.sockobj.accept()
                clientsock.settimeout(5)
                data = clientsock.recv(1024)

                if data.startswith(shutdown_string):
                    self.Kill = True
                    for th in self.threads:
                        th.killMe()

                    return

                time.sleep(float(5))
            except Exception as e:
                raise e