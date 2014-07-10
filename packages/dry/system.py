import sys
import os
import time
import socket
import threading
import re
import subprocess
from collections import namedtuple


def become_daemon(our_home_dir='.', out_log='/dev/null', err_log='/dev/null', pidfile='/var/tmp/daemon.pid'):
    """ Make the current process a daemon. 	"""
    try:
        # First fork
        try:
            if os.fork() > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #1 failed" (%d) %s\n' % (e.errno, e.strerror))
            sys.exit(1)

        os.setsid()
        os.chdir(our_home_dir)
        os.umask(0)

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                # You must write the pid file here.  After the exit()
                # the pid variable is gone.
                fpid = open(pidfile, 'wb')
                fpid.write(str(pid))
                fpid.close()
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #2 failed" (%d) %s\n' % (e.errno, e.strerror))
            sys.exit(1)

        si = open('/dev/null', 'r')
        so = open(out_log, 'a+', 0)
        se = open(err_log, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    except Exception as e:
        sys.stderr.write(str(e))


def shutdown(host='localhost', port=1025, shutdown_string='die'):
    """ Send a shutdown request to the server.
    This is used with the AdminSocket class. """

    assert isinstance(port, int)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))
    sock.sendall(shutdown_string)
    sock.shutdown(1)
    sock.close()
    
    
class AdminSocket(threading.Thread):
    """	This class is an administrative socket that listens for shutdown
    requests.  A shutdown requests consists of a string that starts
    with the server shutdown string defined in the configuration file.
    """
    def __init__(self, shutdownstring, port,  log):
        threading.Thread.__init__(self)
        self.thread_name = '%s_%s' % ('AdminSocket', self.getName())
        self.log = log
        self.shutdown_string = shutdownstring
        self.port = port
        self.clientsock = None
        self.clientaddr = None
        self.shutdown = False

    def run(self):
        try:
            inter_query_shutdown = float(5.0)
        except ValueError as e:
            self.log.critical('(%s) sleepsecs = float(%s): %s' % 
                              (self.thread_name,
                               str(5.0), 
                               e))
            raise e

        try:
            self.log.debug('(%s) Before socket.socket()' % (self.thread_name))

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.log.debug('(%s) After socket.socket()' % (self.thread_name))
        except socket.error as e:
            self.log.critical('(%s) Strange error creating socket: %s'\
                              % (self.thread_name,e))
            raise e

        try:
            self.log.debug('(%s) Before socket.setsockopt()' % 
                           (self.thread_name))
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.log.debug('(%s) After socket.setsockopt()' %
                           (self.thread_name))
        except socket.error as e:
            self.log.critical('(%s) Could not set socket options: %s' % 
                              (self.thread_name,e))
            raise e

        try:
            self.log.debug('(%s) Before server_socket.bind()' % (self.thread_name))

            server_socket.bind((socket.gethostname(), self.port))

            self.log.debug('(%s) After server_socket.bind()' % (self.thread_name))
        except socket.error as e:
            self.log.critical('(%s) Could not bind to port %d: %s' % 
                              (self.thread_name,self.port, e))
            raise e

        try:
            self.log.debug('(%s) Before server_socket.listen()' % (self.thread_name))

            server_socket.listen(5)

            self.log.debug('A(%s) fter server_socket.listen()' % (self.thread_name))
        except Exception as e:
            self.log.error('(%s) socket.listen() had a problem: %s' \
                           % (self.thread_name,e))
            raise e

        while not self.shutdown:
            try:
                self.log.debug('(%s) Before server_socket.accept()' % 
                               (self.thread_name))

                (self.clientsock, self.clientaddr) = server_socket.accept()

                self.log.info('(%s) After: accept() got connection to admin socket' 
                              % (self.thread_name))
            except Exception as e:
                self.log.error('(%s) client_connection, clientaddr = server_socket.accept(): %s' % 
                               (self.thread_name,e))

            data_buf = ''
            data = ''

            while True:
                try:
                    data_buf = self.clientsock.recv(1024)
                    if not len(data_buf):
                        break
                    else:
                        data = data + data_buf
                except Exception as e:
                    raise e

            try:
                if data.strip().startswith(self.shutdown_string):
                    self.shutdown = True
                    self.log.info('Received shutdown request')
                else:
                    self.log.warning('Received unidentifiable data on admin socket.')

                time.sleep(3.0)
            except Exception as e:
                raise e

    
def pygrep(pattern, *files):
    """ grep like behavior
    returns list of found entries in format
    file:linenumber:text
        
    Arguments:
    
    pattern - a string.
    
    *files - a sequence of file names to search
    """
    try: 
        listFound = []	
        search = re.compile(pattern).search

        for f in files:
            for index, line in enumerate(open(f)):
                if search(line):
                    listFound.append(str(f)+':'+str(index+1)+':'+str(line[:-1]))
    except Exception as e:
        raise e

    return listFound


# Superceded by libary psutil
class PSList():
    """ Class representation of system ps -ef list.
    On init a copy of the list is stored in memory.
    find() searches for matches on any of the column heading elements.
    update() updates the list to the current state.
    """
    def __init__(self):
        self.fname = None
        self.f = None # file handle
        self.inmem_pslist = None
        self.__make()
        
    def __make(self):
        # open tmp file
        self.fname = '/tmp/ps.{0}'.format(time.time())
        try:
            with open(self.fname, 'w+') as self.f:
                subprocess.check_call('ps -ef', shell=True, stdout=self.f)
                self.f.seek(0)
                self.inmem_pslist = self.f.readlines()
        except subprocess.CalledProcessError as e:
            raise e
        except Exception as e:
            raise e
        
        if os.path.isfile(self.fname):
            os.remove(self.fname)
        
                                      
    def find(self, uid=None, pid=None, ppid=None, c=None, 
             stime=None, tty=None, time=None, cmd=None, 
             cmd_exact_match=False):
        """ If there is a match on all the arguments passed, then place the named tuple
        of the current line in the found list.  This is the equivalent of performing
        piped greps
        
        ps -ef|grep 19384| grep python
        
        This says to look for a process with the PID of 19384 and has the word 
        python somewhere in the line.
        
        This class breaks out the separate elements of a process list entry.
        
        In this example:
        rhancock  2240  2072  0 Apr23 ?   00:00:00 python /usr/share/system-config-printer/applet.py
        
        the elements break down into:
        uid = rhancock
        pid = 2240
        ppid = 2072
        c = 0
        stime = Apr23
        tty = ?
        time = 00:00:00
        cmd = python /usr/share/system-config-printer/applet.py
        
        Arguments
            The default for all element arguments in None.  If supply an element value
            it becomes part of a compound boolean AND.  All elements must match for
            find to be true.
            
            When cmd_exact_match is True is will test for an exact match of a command string
            If False, test if the string occurs anyhwere in the cmd.

        Returns
           List of named tuples.
           namedtuple('ps_list', 'uid, pid, ppid, c, stime,tty,time, cmd')
           
           If a match is not found, it returns an empty list.

        Example:
        ps = PSList()
        # Is a process with the string foo.py instantiated?
        list_matches = ps.find(cmd='foo.py', cmd_exact_match=False)
        
        If any ps listing where the command line contains "foo.py" is found, then
        the entire ps entry is entered into the found list.
        
        # Is a process with the string foo.py instantiated?
        list_matches = ps.find(cmd='foo.py', cmd_exact_match=True)
        
        In this case, the match will be found ONLY if the command line portion
        of the ps list contains exactly "foo.py" and nothing else.
        
        All matches are case sensitive.
        """

        found = []
        args={}
        pslist = namedtuple('ps_list', 'uid, pid, ppid, c, stime,tty,time, cmd')

        # Determine which elements to search for
        if uid:
            args['uid'] = uid
        if pid:
            args['pid'] = pid
        if ppid:
            args['ppid'] = ppid
        if c:
            args['c'] = c
        if stime:
            args['stime'] = stime
        if tty:
            args['tty'] = tty
        if time:
            args['time'] = time
        if cmd:
            args['cmd'] = cmd

        for line in self.inmem_pslist:
            # The inmem_pslist consists of the entire output from
            # ps -ef.
            # For each line in the ps list search for a match
            # on items in args.  If all args match, then move
            # the named tuple to the name found.
            l = line.split()
            if len(l) > 7:
                ps_list = pslist(uid=l[0], pid=l[1], ppid=l[2], c=l[3], 
                                 stime=l[4], tty=l[5], time=l[6], 
                                 cmd=' '.join(l[7:]).strip())

                # Loop through all the passed arguments, if one is false, break out
                for key, argval in args.items():
                    attr = getattr(ps_list, key)                        
                    if key == 'cmd' and cmd_exact_match:
                        # Is this an exact match?
                        if attr == argval:
                            matched = True
                        else:
                            matched = False
                            break
                    else:
                        if str(argval) in attr:
                            matched = True
                        else:
                            matched = False
                            break

                if matched:
                    found.append(ps_list)

        return found

    def update(self):
        self.__make()
        return self        