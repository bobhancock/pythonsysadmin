""" Run a configurable rsync process as a daemon. 

The rsync boiler plate command line is specified in the configuration.
You must include at least a remote host and a remote dir, in that order.
"""
import pdb
import time
import sys
import os
from optparse import OptionParser
from ConfigParser import SafeConfigParser
import socket
import threading
import subprocess

import rsync_settings
sys.path.insert(0, rsync_settings.PACKAGE_PATH)

import dry.logger
import dry.system


class Appconf:
    """ Class representation of configuration file."""
    def __init__(self, filenameConfig):
        self.appconf = {}

        try:
            self.filenameConfig = filenameConfig
            self.config = SafeConfigParser()
            self.config.read(self.filenameConfig)
            self.appconf["log_file"] = self.config.get('program', "log_file")
            self.appconf["server_port"] = self.config.get('program', "server_port")
            self.appconf["inter_rsync_time"] = self.config.get('program', "inter_rsync_time")
            self.appconf["inter_heartbeat_time"] = self.config.get('program', "inter_heartbeat_time")
            #self.appconf["remote_host"] = self.config.get('program', "remote_host")
            self.appconf["rsync_boilerplate"] = self.config.get('program', 
                                                                "rsync_boilerplate",
                                                                raw=True)
            #self.appconf["rsync_bin"] = self.config.get('program', "rsync_bin")
            self.appconf['remote_dir'] = self.config.get('program', "remote_dir")
            self.appconf['rsync_log'] = self.config.get('program', "rsync_log")
            self.appconf['lock_file'] = self.config.get('program', "lock_file")
            self.appconf['server_shutdown'] = self.config.get('program', "server_shutdown")
            self.appconf['daemon_log'] = self.config.get('program', "daemon_log")
            self.appconf['daemon_error_log'] = self.config.get('program', "daemon_error_log")
            self.appconf['daemon_pid'] = self.config.get('program', "daemon_pid")
            
        except Exception as e:
            raise e

    def verify_appconf(self):
        """ Verify values in appconf. 
        Place errors in dictionary appconf_error and return.
        """
        appconf_error = {}

        key = "server_port"
        i = self.appconf[key]
        try:
            self.appconf[key] = int(i)
        except ValueError:
            appconf_error[key] = 'Not instance of int: %s' % str(i)

        key = "inter_rsync_time"
        i = self.appconf[key]
        try:
            self.appconf[key] = int(i)
        except ValueError:
            appconf_error[key] = 'Not instance of int: %s' % str(i)

        key = "inter_heartbeat_time"
        i = self.appconf[key]
        try:
            self.appconf[key] = int(i)
        except ValueError:
            appconf_error[key] = 'Not instance of int: %s' % str(i)

        # The remote and local dir have to be the same for rsynce
        key = "remote_dir"
        dr = self.appconf[key]
        if not os.path.isdir(dr):
            appconf_error[key] = "Cannot find directory %s" % dr

        #key = "rsync_bin"
        #fn = self.appconf[key]
        #if not os.path.isfile(fn):
            #appconf_error[key] = "Cannot find file %s" % fn

        return appconf_error


def shutdown(configfile, host=None):
    """ Send a shutdown request to the server """

    config_file = configfile
    
    if not os.path.isfile(config_file):
        print 'Cannot find configuration %s' % config_file
        return 1
    
    try:
        appconf = Appconf(config_file)
    except Exception as e:
        sys.stderr.write('Appconf(config_file): %s' % e)
        return 1
    
    app_conf = appconf.appconf
    appconf_errors = appconf.verify_appconf()
    if len(appconf_errors.keys()):
        for k, v in appconf_errors.iteritems():
            print('Configuration Error: %s: %s' % (k, v))
            return 1
 
    server_port = app_conf['server_port']
    server_shutdown = app_conf['server_shutdown']
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((host, server_port))
        sock.sendall(server_shutdown)
        sock.shutdown(1)
        sock.close()
    except Exception as e:
        msg='host=%s port=%d: %s' % (host, server_port, e)
        print >>sys.stderr, msg
        return(1)

    return(0)

class Rsync(threading.Thread):
    """ Class to implement rsync based on a configuration file. """
    def __init__(self, remote_host, rsync_bin, appconf, logger):
        threading.Thread.__init__(self)
        self.remote_host = remote_host
        self.rsync_bin = rsync_bin
        self.appconf = appconf
        self.log = logger
        self.Kill = False
        
    def run(self):
        self.log.info('Entered Rsync.run()')
        basetime = int(0)
        inter_sync_time = self.appconf['inter_rsync_time']
        
        try:
            while (not self.Kill):
                if (time.time() > basetime + inter_sync_time):
                    self.__rsyncFiles()
                    basetime = time.time()
                else:
                    time.sleep(float(2))
        except Exception as e:
            self.log.error('Rsync.run(): %s' % e)
            raise e

    def killMe(self):
        self.Kill = True
        self.log.debug('Rsync: self.Kill = True')

    def __rsyncFiles(self):
        """ rysnc files."""
        self.log.info('Entered __rsyncFiles')

        rsync_bin = self.rsync_bin
        rsync_boilerplate = self.appconf['rsync_boilerplate']
        remote_host = self.remote_host
        remote_dir = self.appconf['remote_dir']
        lock_file = self.appconf['lock_file']
        rsync_log = self.appconf['rsync_log']

        if os.path.isfile(lock_file):
            self.log.error('%s exists. Either previous invocation of rsync is still running or it terminated improperly.  This script will not rsync.' 
                           % lock_file)
            return
        else:
            # create the file
            try:
                self.log.debug("Before: fh_lock = open(lock_file, 'wb')")
                fh_lock = open(lock_file, 'wb')
                self.log.debug("After: fh_lock = open(lock_file, 'wb')")
            except IOError as e:
                self.log.error('Cannot open %s: %s' % (lock_file, e))
                return
                
            try:
                self.log.debug("Before: fh_lock.close()")
                fh_lock.close()
                self.log.debug("After: fh_lock.close()")
            except IOError as e:
                self.log.error('Cannot close %s: %s' % (lock_file, e))
                return
            
            # This is how you touch a file
            # Put this in dry
            #os.utime(lock_file, (time.time(), time.time()))

        
        now = time.strftime("%m/%d/%y %H:%M:%S", time.localtime())
        write_date_to_rsync_log = ('echo "%s" >> %s' % (now, rsync_log))
        
        # remot_dir is listed twice because the source (remote) and target
        # directories must be the same.
        cmdlineRunRsync =  rsync_boilerplate % (rsync_bin, 
                                                remote_host,
                                                remote_dir,
                                                remote_dir)
        execute_rsync = '%s >> %s' % (cmdlineRunRsync, rsync_log)
        
        try:
            try:
                subprocess.check_call(write_date_to_rsync_log, shell=True)
            except subprocess.CalledProcessError as e:
                self.log.warning('subprocess.check_call(write_date_to_rsync_log, shell=True): %s' 
                               % e)
            
            self.log.debug('Before rsync  %s' % (execute_rsync))
            start = time.time()                   
            try:
                subprocess.check_call(execute_rsync, shell=True)
            except subprocess.CalledProcessError as e:
                self.log.error('subprocess.check_call(%s, shell=True): %s.  Check: %s.' 
                               % (execute_rsync, e, rsync_log))
                return
            
            end = time.time()
            self.log.debug('After rsync  %s' % (execute_rsync))
            elapsed = end - start
            self.log.info('rsync  %s succeeded. Elapsed time=%d seconds.' 
                          % (remote_host, elapsed))
        finally:
            try:
                self.log.debug("Before: os.remove(lock_file)")
                os.remove(lock_file)
                self.log.debug("After: os.remove(lock_file)")
            except OSError as e:
                self.log.critical('Cannot remove lock file %s.  '
                                  +'This will prevent subsequent rsyncs '
                                  +'from executing.'
                                  % lock_file)

class Heartbeat(threading.Thread):
    """ Write string 'heartbeat' to log every n seconds, where 
    n = inter_rsync_time / 2.
    """
    def __init__(self, appconf, logger):
        # appconf is a dictionary with configuration values
        threading.Thread.__init__(self)
        self.appconf = appconf
        self.log = logger
        self.Kill = False

    def run(self):
        self.log.info('Entered Heartbeat.run()')
        basetime = int(0)
        inter_heartbeat_time = self.appconf['inter_heartbeat_time']
        inter_heartbeat_time = int(inter_heartbeat_time )

        try:
            while (not self.Kill):
                if (time.time() > basetime + inter_heartbeat_time):
                    self.log.info('heartbeat')
                    basetime = time.time()
                else:
                    time.sleep(float(1))
        except Exception as e:
            raise e

    def killMe(self):
        self.Kill = True
        self.log.debug('Heartbeat:self.Kill = True')
        
#---------------------------------------------
# Class to listen for shutdown request
#---------------------------------------------
class ListenForReq(threading.Thread):
    """ Listen for server request to shutdown. """
    def __init__(self, sockobj, listthreads, appconf, logger):
        threading.Thread.__init__(self)
        self.name = 'ListenForReq'
        self.appconf = appconf
        self.server_shutdown = self.appconf['server_shutdown']
        self.log = logger
        self.Kill = False
        self.sockobj = sockobj
        self.threads = listthreads
        self.connection = None
        self.address = None
        

    def run(self):
        self.log.debug('Entered ListenForReq.run()')
        server_shutdown_command = self.appconf['server_shutdown']
        while not self.Kill:
            try:
                clientsock, clientaddr = self.sockobj.accept()
                clientsock.settimeout(5)
                data = clientsock.recv(1024)

                if data.startswith(server_shutdown_command):
                    #self.clientsock.send('Echo=>%s %s' % (self.data, self.threads))
                    self.Kill = True
                    self.log.info('Received shutdown request')
                    for th in self.threads:
                        th.killMe()

                    # this socket has cmpleted its businees, so
                    # clos and return
                    #self.sockobj.shutdown(2)
                    #self.sockobj.close()
                    return

                time.sleep(float(5))
            except Exception as e:
                raise e

def run_rsync(configfile, isdebug=False, isdaemon=False, dellockfile=False,
              remote_host=None, rsync_bin=None):
    """ Run rsync process as a daemon. """
    config_file = configfile
    try:
        appconf = Appconf(config_file)
    except OSError as e:
        raise e
        #sys.stderr.write('Appconf(config_file): %s' % e)
        #return 1
    
    # If there are any configuration errors, they are written to stderr
    app_conf = appconf.appconf
    appconf_errors = appconf.verify_appconf()
    if len(appconf_errors.keys()):
        for k, v in appconf_errors.iteritems():
            raise Exception('Configuration Error: %s: %s' % (k, v))
            
   # setup logging
    try:
        #log = dry.logger.setupLogging(app_conf["log_file"], 'rsync_audit', isdebug)
        log = dry.logger.setup_log_timed_rotating(app_conf["log_file"],
                                                  logname='rsync',
                                                  rotate_when='midnight',
                                                  debug=isdebug, 
                                                  backups = 1024)

        log.info('Program started')
    except Exception as e: 
        raise Exception('Caught exception in setupLogging: %s' % e)

    for k, v in app_conf.iteritems():
        log.info('%s = %s' % (k, v))
    
    # make this a daemon
    if isdaemon:
        try:
            log.debug('Before: become_daemon')
            dry.system.become_daemon('.', app_conf['daemon_log'], 
                          app_conf['daemon_error_log'], 
                          app_conf['daemon_pid'])
            log.debug('After: become_daemon')
        except Exception as e:
            raise Exception('become_daemon() raised: %s' % (str(e)))

    if dellockfile:
        lock_file = app_conf["lock_file"]
        if os.path.isfile(lock_file):
            log.debug('%s exists' % lock_file)
            try:
                os.remove(lock_file)
                log.info('Deleted %s' % lock_file)
            except OSError as e:
                msg = 'Cannot delete %s.  ABORTING' % lock_file
                log.critical(msg)
                raise OSError(msg)
        
    # Setup server socket
    try:
        serverSocketBound = False
        thisHost = ''  #'' means local host
        thisPort = app_conf['server_port']

        log.debug('Before: sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)')
        sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        log.debug('Before: sockobj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)')
        sockobj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        log.debug('Before: sockobj.bind((thisHost, int(thisPort)))')
        sockobj.bind((thisHost, int(thisPort)))
        #sockobj.settimeout(5.0)
        
        serverSocketBound = True
        log.info('Bound server socket on port '+str(thisPort))
        sockobj.listen(1) # listen allows 1 pending session
        log.debug('After: sockobj.listen(1)') 
    except Exception as e:
        msg = ('While attempting to start server socket on port %s raised: %s' 
               % (str(thisPort), e))
        log.critical(msg)
        raise Exception(msg)

    threads = []
    # Start thread to write heartbeat
    try:
        log.debug('Before:hb = Heartbeat(appconf, log)')
        hb = Heartbeat(app_conf, log)
        log.debug('Before: hb.start()') 
        hb.start()
        log.debug('Before: threads.append(hb)') 
        threads.append(hb)
        log.debug('After: threads.append(hb)') 
    except Exception as e:
        msg = 'Caught exception while starting Heartbeat thread: %s' % e
        log.critical(msg)
        raise Exception(msg)
        
    
    # start thread to run rsync
    try:
        log.debug('Before: t = Rsync(appconf, log)')
        t = Rsync(remote_host, rsync_bin, app_conf, log)
        log.debug('Before: t.start()') 
        t.start()
        log.debug('Before: threads.append(t)') 
        threads.append(t)
        log.debug('After: threads.append(t)')
    except Exception as e:
        msg = 'Caught exception while starting Rsync thread: %s' % repr(e)
        log.critical(msg)
        raise Exception(msg)

    #------------------------------------------------
    # Start thread to listen for shutdown requests
    #------------------------------------------------
    if serverSocketBound:
        try: 
            log.debug('Before: l = listen(sockobj, threads, log)')
            l = ListenForReq(sockobj, threads, app_conf, log)
            log.debug('Before: l.start()') 
            l.start()
            log.debug('After: l.start()')
        except Exception as e:
            msg = 'Caught exception while starting ListenForReq(): %s' % str(e)
            log.error('%s' % (msg))
            raise Exception(msg)

    #------------------------------------------------
    # Wait for feed thread(s) to complete
    #------------------------------------------------
    log.debug('Before: for t in threads: th.join()')
    for th in threads:
        th.join()
    log.debug('After: for t in threads: th.join()')

    try:
        log.debug('Before: sockobj.close()') 
        sockobj.close()
        log.debug('After: sockobj.close()')
    except Exception as e:
        msg = 'Caught exception while closing server socket: %s' % str(e)
        log.error('%s' % (msg))
        raise Exception(msg)

    log.info('Shutdown complete')


#==========================================
# main()
#==========================================
def main():
    """
	main process
	"""
    usage = '%prog [-Ddl] config_file'
    try:	
        parser = OptionParser(usage)
        parser.add_option("-D", "--debug", dest="isDebug", action="store_true",
                          help="Write debug records (produces a large log file)")
        parser.add_option("-d", "--daemon", dest="isDaemon", action="store_true",
                          help="Run as a daemon.")
        parser.add_option("-l", "--dellockfile", dest="dellockfile", action="store_true",
                          help="Delete lock file on start up.")

        
        [options, args] = parser.parse_args()
        if len(args) < 1:
            parser.error('Incorrect number of arguments')
            return -1
        else:
            config_file = args[0]
    except Exception as e:
        print e
        return 1
    isdebug = True if options.isDebug else False
    isdaemon = True if options.isDaemon else False
    dellockfile = True if options.dellockfile else False    
    run_rsync(config_file, isdebug, isdaemon, dellockfile)

if __name__ == "__main__":
    # call main process and exit with its return code
    sys.exit(main())
