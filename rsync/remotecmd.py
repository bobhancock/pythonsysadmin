""" Remote command execution using SSH. """

import sys, os, select
import paramiko
import collections
import multiprocessing
import threading

class RemoteCommand():
    def __init__(self, hostname, product_conf, hostport=22):
        self.host = hostname
        self.username = product_conf.username
        self.password = product_conf.password
        self.hostport = hostport
        self.t = None
        
        try:
            self.__connect()
        except Exception as e:
            raise e
    
    def __connect(self):
        """ Make ssh connection to host. """
        try:
            self.t = paramiko.Transport((self.host, self.hostport))
        except Exception as e:
            raise e
        
        try:
            self.t.connect(username=self.username, password=self.password)
        except Exception as e:
            raise e
        

    def execute(self, cmd):
        """ Open channel on transport, run command, capture output and return."""
        out = ''
    
        try:
            chan = self.t.open_session()
        except paramiko.SSHException as e:
            raise e
    
        try:
            chan.setblocking(0)
        except paramiko.SSHException as e:
            raise e
    
        try:
            chan.exec_command(cmd)
        except Exception as e:
            raise e
    
        # Read when data is available
        while select.select([chan,], [], []):
            x = chan.recv(1024)
            if not x:
                break
            out += x
            select.select([],[],[],.1)
    
        chan.close()
        print out
        #return out

def main():
    hostname = 'poc2'
    product_conf = collections.namedtuple('ProductConf',
                                      'name, username, password, remote_root, local_root')
    
    product_conf.username = 'adp_ftp'
    product_conf.password = 'adp_ftp'
    
    rc = RemoteCommand(hostname, product_conf)
    #p = multiprocessing.Process(target=rc.execute, args=('ls -la',))
    #p.set_daemon=True
    #p.start()
    #p.join()
    
    t = threading.Thread(target=rc.execute, args=('ls -la',))
    t.set_daemon=True
    t.start()
    t.join()
    
    #print(rc.execute('ls -la'))
    print 'Done'
if __name__ == '__main__':
    import sys
    sys.exit(main())