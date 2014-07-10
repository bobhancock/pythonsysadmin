""" The retrieval client that retrieves data from a remote FTP server. """
import pdb
import sys
import os
import time
import logging
import socket
import threading
import ftputil
from datetime import datetime
from optparse import OptionParser
from pysqlite2 import dbapi2 as sqlite
from ConfigParser import SafeConfigParser
import codecs
import resource
import uuid

import settings
if os.path.abspath(settings.PACKAGE_PATH) not in sys.path:
    sys.path.insert(0, os.path.abspath(settings.PACKAGE_PATH))

import dry.logger 
import dry.system 

__version__ = "1.1.3"
__author__ = '(Robert Hancock hancock.robert@gmail.com)'

#TO DO 
# Put verification in appconf
# Return named_tuple
class Appconf:
    """ Class representation of configuration file."""
    def __init__(self, filenameConfig):
        self.appconf = {}

        try:
            self.filenameConfig = filenameConfig
            self.config = SafeConfigParser()
            self.config.read(self.filenameConfig)

            self.appconf['ftp_host'] =  self.config.get('remote' ,"ftp_host")
            self.appconf['ftp_user'] =   self.config.get('remote', "ftp_user")
            self.appconf['ftp_password'] = self.config.get('remote', "ftp_password")
            self.appconf['ftp_remote_directory'] = self.config.get('remote', "ftp_remote_directory")
            self.appconf['ftp_duration_secs'] = self.config.getint('remote',
                                                              'ftp_duration_secs')



            self.appconf['ftp_local_directory'] =    self.config.get('local', "ftp_local_directory")
            self.appconf['sync_directory'] =   self.config.get('local', "sync_directory")
            self.appconf['journal_file_name'] =  self.config.get('local', "journal_file_name")
            self.appconf['journal_table_name'] =  self.config.get('local', "journal_table_name")
            self.appconf['sleep_in_seconds'] =   self.config.get('local', "sleep_in_seconds")
            self.appconf['xml_encoding'] =   self.config.get('local', "xml_encoding")

            self.appconf['daemon_log'] =   self.config.get('daemon', "daemon_log")
            self.appconf['daemon_error_log'] =   self.config.get('daemon', "daemon_error_log")
            self.appconf['daemon_pid'] =   self.config.get('daemon', "daemon_pid")
            
            self.appconf['server_port'] =   self.config.get('server', "server_port")
            self.appconf['server_shutdown_string'] =  self.config.get('server', "server_shutdown_string")
            self.appconf['inter_heartbeat_secs'] =  self.config.get('server', "inter_heartbeat_secs")
            
        except Exception as e:
            raise e

    def verify_appconf(self):
        """ Verify values in appconf. """
        appconf_error = {}

        key = 'ftp_local_directory'
        d = self.appconf[key]
        if not os.path.isdir(d):
            appconf_error[key] = 'No such file or directory: %s'  % d

        key = 'sync_directory'
        d = self.appconf[key]
        if not os.path.isdir(d):
            appconf_error[key] = 'No such file or directory: %s'  % d

        key = 'sleep_in_seconds'
        i = self.appconf[key]
        try:
            int(i)
        except ValueError:
            appconf_error[key] = 'invalid literal for int() with base 10: %s' % i

        key = 'daemon_log'
        d, f = os.path.split(self.appconf[key])
        if not os.path.isdir(d):
            appconf_error[key] = 'No such directory: %s'  % d

        key = 'daemon_error_log'
        d, f = os.path.split(self.appconf[key])
        if not os.path.isdir(d):
            appconf_error[key] = 'No such directory: %s'  % d

        key = 'daemon_pid'
        d, f = os.path.split(self.appconf[key])
        if not os.path.isdir(d):
            appconf_error[key] = 'No such directory: %s'  % d

        key = 'server_port'
        i = self.appconf[key]
        try:
            int(i)
        except ValueError:
            appconf_error[key] = 'Invalid literal for int() with base 10: %s' % i

        key = "xml_encoding"
        c = self.appconf[key]
        try:
            codecs.lookup(c)
        except LookupError:
            appconf_error[key] = 'Invalid encoding: %s' % c

        key = 'inter_heartbeat_secs'
        i = self.appconf[key]
        try:
            int(i)
        except ValueError:
            appconf_error[key] = 'Invalid literal for int() with base 10: %s' % i

        return appconf_error



           

class Poller(threading.Thread):
    """
    Polls a remote directory and download only the new files
    A list of successfully downloaded files is kept in the journal.
    """

    def __init__(self, name, appconf,  logger,  sleeptime=60, remotedir = ''):
        threading.Thread.__init__(self)	
        self.Kill = False
        self.name = name
        self.app_conf = appconf # application configuration object
        self.log = logger
        self.log.debug('Entered poller.__init__')

        self.ftp_host = self.app_conf['ftp_host']
        self.ftp_user = self.app_conf['ftp_user']
        self.ftp_password = self.app_conf['ftp_password']
        if remotedir:
            self.one_time_remote_dir = remotedir
        else:
            self.one_time_remote_dir = ''
        self.ftp_remote_directory = self.app_conf['ftp_remote_directory']
        self.ftp_local_directory = self.app_conf['ftp_local_directory']


        self.log.debug('Before: self.journal = journal(%s, %s)' \
                       % (self.app_conf['journal_file_name'], 
                          self.app_conf['journal_table_name']))
        
        self.journal = journal(self.app_conf['journal_file_name'],
                               self.app_conf['journal_table_name'])
        
        self.log.debug('After: self.journal = journal(%s, %s)' \
                       % (self.app_conf['journal_file_name'], 
                          self.app_conf['journal_table_name']))

        self.log.debug('After: self.journal.connect()')

        if not os.path.isfile(self.app_conf['journal_file_name']):
            self.log.debug('Before: self.journal.connect()')
            #If the database file does not exist, then the connect will create it
            self.journal.connect()

            self.log.debug('Before: self.journal.create()')
            self.journal.create_table()
            self.log.debug('After self.journal.create()')
            self.journal.disconnect()

        self.dir_list = []

        self.sleeptime = float(sleeptime)
        self.Kill = False
        #self.isActive = False
        self.socket_to_observer = None
        
        self.ftp_session_active = False
        self.host = None
        self.duration_secs = self.app_conf['ftp_duration_secs']

    def __str__(self):
        return self.name
    
    def _monitor_ftp_session(self):
        
        """ If the FTP session lasts more than max_secs, unconditionally shut it
        down.  This is to work around the rare condition with EDX where the 
        listdir fails, no error is raised and the socket does not timeout. 

        This procedure is run in a thread.
        """
        
        self.log.debug('{tn}|{cl}|{pr}|Entered'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name))
        
        base_time = current_time = time.time()
    
        while (current_time <= base_time + self.duration_secs
               and self.ftp_session_active):
            time.sleep(.5)
            current_time = time.time()
            self.log.debug('{tn}|{cl}|{pr}|{ct}|'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name,
                    ct=current_time))
        
        if self.ftp_session_active:
            try:
                self.log.warning('{tn}|{cl}|{pr}|Session timed out'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name))
                
                self.log.debug('{tn}|{cl}|{pr}|Before: self.host.close()'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name))
                
                self.host.close()    
            except Exception as e:
                self.log.error('{tn}|{cl}|{pr}|Timeout exceeded and host.close() failed: {ex}'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name,
                    ex=e))
                self.ftp_session_active = False
                return
                
            self.ftp_session_active = False
            self.log.debug('{tn}|{cl}|{pr}|After: self.host.close()'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name))

        self.log.debug('{tn}|{cl}|{pr}|Leaving'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name))

        return

    def run(self):
        """ Get files in remote directory, parse and send to observer. """
        basetime = int(0)
        while not self.Kill:
            #while not self.isActive:
            #	time.sleep(10)
            if (time.time() > basetime + self.sleeptime):	
                try:
                    self.log.debug('Before: local_files = self.__getremotefiles()')
                    self.log.info('Check for new files.')
                     
                    local_files = self.__get_remote_files()
                    self.log.debug('After: local_files = self.__getremotefiles()')

                    if len(local_files):
                        # if len(local_files) != 0 this means files were dowloaded
                        self.log.info('FILESDOWNLOADED|{l}'.format(l=local_files))
                        self.log.debug('Entered: if len(local_files): %d' % len(local_files) )
                        self.log.debug('Before: self.journal.connect()')
                        try:
                            self.journal.connect()    
                        except Exception as e:
                            self.log.fatal("self.journal.connect(): %s" % e)
                            return
                        self.log.debug('After: self.journal.connect()')

                        self.log.debug('Before: for fil in local_files:')
                        # Log each file downloaded to the journal
                        for tup in local_files:
                            self.log.debug('%d tuples to process' % len(local_files))
                            fil, remote_file_date, full_remote_fname = tup
                            self.log.debug('fil=%s' % fil)
                            self.log.debug('Before: news_item = self.__parse_XML(fil)')

                            #update journal
                            self.log.debug('Before: self.journal.insert_row(%s, %s, %s)'\
                                           % (self.name, remote_file_date,
                                              full_remote_fname))
                            try:
                                if self.one_time_remote_dir:
                                    pass
                                else:
                                    self.journal.insert_row(self.name,
                                                            remote_file_date, 
                                                            full_remote_fname)
                                    self.log.info('Processed %s' % full_remote_fname)
                            except Exception as e:
                                self.log.error('self.journal.insert_row(%s, %s, %s): %s' \
                                               % (self.name, remote_file_date, 
                                                  full_remote_fname, e))
                                continue
                            self.log.debug('After: self.journal.insert_row(%s, %s, %s)' \
                                           % (self.name, remote_file_date, 
                                              full_remote_fname))

                            # Move to the sync directory
                            path, fname = os.path.split(fil)
                            dest_path_fname = os.path.join(self.app_conf['sync_directory'],
                                                           fname)

                            try:
                                self.log.debug('Before: move(%s, %s)' % (fil, 
                                                                         dest_path_fname))

                                os.rename(fil, dest_path_fname)
                                
                                self.log.debug('After: move(%s, %s)' % (fil, 
                                                                        dest_path_fname))
                                self.log.info('moved %s to %s' % (fil, 
                                                                  dest_path_fname))
                            except IOError as e:
                                self.log.error('move(%s, %s): %s' % (fil, 
                                                                     dest_path_fname, 
                                                                     e))

                        # Disconnect from journal
                        self.log.debug('Before: self.journal.disconnect()')
                        try:
                            self.journal.disconnect()
                        except Exception as e:
                            self.log.error('self.journal.disconnect():%s' % e)
                        self.log.debug('After: self.journal.disconnect()')
                    else:
                        if self.one_time_remote_dir:
                            break
                except Exception as e:
                    self.log.error('subject.run():%s' % e)

                basetime = time.time()		

            #self.log.debug('Before: time.sleep() at bottom of main while loop')
            if self.one_time_remote_dir:
                return
            else:
                time.sleep(float(5))
            #self.log.debug('After: time.sleep() at bottom of main while loop')
        return

    def __get_remote_files(self):
        """ Retrieve remote files via FTP and return a list of tuples
        (local_fname, remote_file_date, full_remote_fname)"""
        remote_fnames = []
        local_fnames = []
        self.ftp_session_active = False
        self.log.debug('Entered __getremotefiles')

        self.log.debug('Before: self.journal.connect()')
        try:
            self.journal.connect()    
        except Exception as e:
            self.log.fatal("self.journal.connect(): %s" % e)
            return local_fnames
        
        self.log.debug('After: self.journal.connect()')

        self.log.debug('Before: host = ftputil.FTPHost(%s, %s, %s)' \
                       % (self.ftp_host, self.ftp_user, self.ftp_password))
        try:
            self.host = ftputil.FTPHost(self.ftp_host, self.ftp_user, self.ftp_password)
        except Exception as e:
            self.log.warning('host = ftputil.FTPHost(%s, %s, %s): %s'\
                           % (self.ftp_host, self.ftp_user, self.ftp_password, e))
            return local_fnames
        
        self.log.debug('After: host = ftputil.FTPHost(%s, %s, %s)' \
                       % (self.ftp_host, self.ftp_user, self.ftp_password))

        # Start a thread to monitor this session.  If the session lasts
        # more than n seconds, unconditionally shut it down.
        self.ftp_session_active = True
        
        n = int(time.time())
        monitor_thread_name = str(uuid.UUID(int=n))
        
        self.log.debug('{tn}|{cl}|{pr}|Before: ftp_session_monitor_thread:{mt}'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name,
                    mt=monitor_thread_name))
        
        ftp_session_monitor_thread = threading.Thread(
            target=self._monitor_ftp_session, 
            args=(),
            name=monitor_thread_name)
        
        self.log.debug('{tn}|{cl}|{pr}|After: ftp_session_monitor_thread:{mt}'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name,
                    mt=monitor_thread_name))        
        
        ftp_session_monitor_thread.daemon=True
        
        self.log.debug('{tn}|{cl}|{pr}|Before: ftp_session_monitor_thread.start():{mt}'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name,
                    mt=monitor_thread_name))
        
        ftp_session_monitor_thread.start()
        
        self.log.debug('{tn}|{cl}|{pr}|Before: ftp_session_monitor_thread.start():{mt}'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name,
                    mt=monitor_thread_name))

        try:
            if self.one_time_remote_dir:
                remote_target_dir = self.one_time_remote_dir
            else:
                remote_target_dir = self.ftp_remote_directory

            self.log.debug('Before: host.chdir(%s)' % remote_target_dir)
            self.host.chdir(remote_target_dir)
            self.log.debug('After: host.chdir(%s)' % remote_target_dir)
        except Exception as e:
            self.log.warning('host.chdir(%s): %s' % (remote_target_dir, e))
            self.ftp_session_active = False
            return local_fnames

        self.log.debug('Before: remote_fnames = self.host.listdir(host.curdir)')
        remote_fnames = []
        try:
            # This is where it sometimes hangs with EDX. 
            remote_fnames = self.host.listdir(self.host.curdir)
        except Exception as e:
            self.log.warning('remote_fnames = self.host.listdir(host.curdir): %s' % e)
            self.ftp_session_active = False
            return local_fnames
        
        if not self.ftp_session_active:
            template = '{tn}|{cl}|{pr}|After: remote_fnames = ' \
                           + 'host.listdir(host.curdir), self.ftp_session_activ=False'
            self.log.debug(template.format(tn=self.name,
                                           cl=self.__class__,
                                           pr=sys._getframe().f_code.co_name))
            
        self.log.debug('After: remote_fnames = host.listdir(host.curdir)')

        if not remote_fnames:
            self.log.debug('{tn}|{cl}|{pr}|remote_fnames is empty'.format(
                    tn=self.name,
                    cl=self.__class__,
                    pr=sys._getframe().f_code.co_name))
            
        count_downloaded_files = 0
        self.log.debug('Before: for remote_fname in remote_fnames:')
        
        for remote_fname in remote_fnames:
            self.log.debug('remote_fname=%s' % remote_fname)

            self.log.debug('Before: stat_result = host.stat(%s)' % remote_fname)
            try:
                stat_result = self.host.stat(remote_fname)
            except Exception as e:
                self.log.warning('After: stat_result = host.stat(r%s): %s' % (remote_fname,e))
                continue
            
            self.log.debug('After: stat_result = host.stat(r%s)' % remote_fname)

            self.log.debug('Before: full_remote_fname = os.path.join(%s, %s)' \
                           % (self.ftp_remote_directory, remote_fname))
            try:
                full_remote_fname = os.path.join(self.ftp_remote_directory, remote_fname)
            except Exception as e:
                self.log.warning('After: full_remote_fname = os.path.join(%s, %s): %s' \
                               % (self.ftp_remote_directory, remote_fname,e))
                continue
            
            self.log.debug('After: full_remote_fname = os.path.join(%s, %s)' \
                           % (self.ftp_remote_directory, remote_fname))

            # This is the time in epoch seconds
            self.log.debug('Before: remote_file_date = %s' % str(stat_result[8]))

            try:
                remote_file_date = str(stat_result[8])
            except Exception as e:
                self.log.warning('After: remote_file_date = %s:%s' % (stat_result[8],e))
                continue
            self.log.debug('After: remote_file_date = %s' % str(stat_result[8]))

            self.log.debug('Before: is_new_file =  self.journal.is_file_new(%s, %s, %s):'\
                           % (self.name, remote_file_date, full_remote_fname))
            try:
                if self.one_time_remote_dir:
                    is_new_file = True
                else:
                    is_new_file = False
                    is_new_file = self.journal.is_file_new(self.name, remote_file_date, full_remote_fname)
            except Exception as e:
                self.log.warning('is_new_file =  self.journal.is_file_new(%s, %s, %s): %s' \
                               % (self.name, remote_file_date, full_remote_fname, e))
                continue
            
            self.log.debug('After: is_new_file =  self.journal.is_file_new(%s, %s, %s) is_newfile = %s' \
                           % (self.name, remote_file_date, full_remote_fname, is_new_file))

            if is_new_file:
                self.log.debug('Before: if host.path.isfile(%s):' % remote_fname)
                if self.host.path.isfile(remote_fname):
                    self.log.debug('After: if host.path.isfile(%s):' % remote_fname)

                    self.log.debug('Before: local_fname = os.path.join(%s, %s)' \
                                   % (self.ftp_local_directory, remote_fname))
                    local_fname = os.path.join(self.ftp_local_directory, remote_fname)
                    self.log.debug('After: local_fname = os.path.join(%s, %s)' \
                                   % (self.ftp_local_directory, remote_fname))

                    self.log.debug('Before: host.download(%s, %s, \'b\')' % (remote_fname, local_fname))
                    # 10/30/2009
                    # Because LCD retrieval has been reporting too many open files after having been running 
                    # for a long time, we will trap the resource limits and write the list of open files.
                    soft, hard =  resource.getrlimit(resource.RLIMIT_NOFILE)
                    cfiles = open_files(os.getpid())
                    if cfiles > 50:
                        log.error('The ftp retrieval process has {c} files open.'.format(c = cfiles))
                        
                    self.log.debug('Number of open files:{cf}.  Max files that can be opened soft={s} hard={h}'.format(
                        cf = cfiles, s=soft, h=hard))
                    
                    try:
                        self.host.download(remote_fname, local_fname, 'b')  # remote, local, binary mode
                    except Exception as e:
                        self.log.error('host.download(%s, %s, \'b\'): %s' % (remote_fname, local_fname, e))
                        continue
                    self.log.debug('After: host.download(%s, %s, \'b\')' % (remote_fname, local_fname))
                    self.log.info('Downloaded %s' % full_remote_fname)

                    self.log.debug('Before: local_fnames.append(%s)'% local_fname)
                    local_fnames.append((local_fname, remote_file_date, full_remote_fname))
                    self.log.debug('After: local_fnames.append(%s)'% local_fname)

                    count_downloaded_files += 1

        self.log.info('Downloaded %d files' % count_downloaded_files)
        self.log.debug('Before: host.close()')
        
        
        try:
            self.host.close()
        except Exception as e:
            self.log.warning('host.close():%s' % e)
            
        self.ftp_session_active = False
        ftp_session_monitor_thread.join()
        self.log.debug('After: host.close()')

        self.log.debug('Before: self.journal.disconnect()')
        try:
            self.journal.disconnect()
        except Exception as e:
            self.log.warning('self.journal.disconnect():%s' % e)
        self.log.debug('After: self.journal.disconnect()')

        self.ftp_session_active = False
        return local_fnames

    def setKill(self, boolean):
        self.Kill = boolean
        self.log.debug('poller.Kill=%s' % self.Kill)


class journal():
    """
	Keep a table of files downloaded by a subject.

	Table structure
	subject | date | filename
    """
    def __init__(self, filename, tablename):
        self.file_name = filename # the physical disk file = database name
        self.table_name = tablename	# table name
        self.conn = None
        self.cursor = None

    def connect(self):
        """ Connect to sqlite table. """
        try:
            self.conn = sqlite.connect(self.file_name)
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise e

    def disconnect(self):
        try:
            self.conn.close()
        except Exception as e:
            rt = e
            raise e

    def create_table(self):
        """ Create a sqlite table. """
        try:
            sql_tuple = (self.table_name, )
            table_create_str = 'create table %s (subject text, date text, filename text, timestamp text)' % self.table_name
            self.cursor.execute(table_create_str)

            unique_index_str = 'create unique index subject_date_filename on %s (subject, date, filename)' % self.table_name
            self.cursor.execute(unique_index_str)
        except Exception as e:
            raise e

    def insert_row(self, subject, date_string, file_name):
        ''' Add row to database. '''
        sub = subject
        date_str = date_string
        fname = file_name
        dt = datetime.now()
        timestamp = '%d_%d_%d_%d_%d_%d_%d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute,dt.second, dt.microsecond)

        try:
            # use tuple to prevent SQL injection attack '''
            sql_tuple =  (sub, date_str, fname, timestamp)
            insert_str = "insert into %s values (?,?,?,?)" % self.table_name

            self.cursor.execute(insert_str , sql_tuple)
            self.conn.commit()
        except Exception as e:
            raise e

    def is_file_new(self, subject, date_string, file_name):
        """ Query journal table for subject + date + filename.
			If found, then the file has already been downloaded.
		"""
        sub = subject
        date_str = date_string
        fname = file_name

        try:

            sql_tuple =  ( sub,date_str, fname)
            select_str = 'select * from %s where subject=? and date=? and filename=?'  % self.table_name

            self.cursor.execute(select_str, sql_tuple)

            if len(self.cursor.fetchall()) > 0:
                return False
            else:
                return True
        except Exception as e:
            raise e

class Heartbeat(threading.Thread):
    """ Write string 'heartbeat' to log every n seconds, where 
    n = sleep_in_seconds / 2.
    """
    def __init__(self, appconf, logger):
        # appconf is a dictionary with configuration values
        threading.Thread.__init__(self)
        self.name = "Heartbeat"
        self.appconf = appconf
        self.log = logger
        self.Kill = False

    def run(self):
        self.log.info('Entered Heartbeat.run()')
        basetime = int(0)
        sleep_in_seconds = int(self.appconf['sleep_in_seconds'])
        inter_heartbeat_secs = int(self.appconf['inter_heartbeat_secs'])

        try:
            while (not self.Kill):
                if (time.time() > basetime + inter_heartbeat_secs):
                    self.log.info('heartbeat')
                    basetime = time.time()
                else:
                    time.sleep(float(1))
        except Exception as e:
            raise e

    def setKill(self, boolean):
        self.Kill = True
        self.log.debug('Heartbeat:self.Kill = True')


class ListenForReq(threading.Thread):
    """ Listen for request to shutdown server. """
    def __init__(self, sockobj, listthreads, appconf, logger):
        threading.Thread.__init__(self)
        self.name = 'ListenForReq'
        self.appconf = appconf
        self.server_shutdown = self.appconf['server_shutdown_string']
        self.log = logger
        self.Kill = False
        self.sockobj = sockobj
        self.threads = listthreads
        self.connection = None
        self.address = None


    def run(self):
        self.log.debug('Entered ListenForReq.run()')
        server_shutdown_command = self.appconf['server_shutdown_string']
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
                        th.setKill(self.Kill)

                    # this socket has completed its businees, so
                    # close and return
                    #try:
                        #if self.sockobj:
                            #self.sockobj.shutdown(2)
                    #except Exception as e:
                        #self.log.warning('self.sockobj.shutdown(2): %s' % e)

                    try:
                        self.sockobj.close()
                    except Exception as e:
                        self.log.warning('self.sockobj.close(): %s' % e)

                    return

                time.sleep(float(5))
            except Exception as e:
                raise e

def go(configfile, logfile, remotedir=None, isdebug=False, isdaemon=False):
    """ Drives FTP retreival process. """
    config_file = configfile
    log_file = logfile

    try:
        #log = dry.logger.setupLogging(log_file, 'rd_news_feed', isdebug)
        log = dry.logger.setup_log_timed_rotating(log_file, 
                                                  logname='ftp',
                                                  rotate_when='midnight',
                                                  debug=isdebug, 
                                                  backups = 1024)
                
        log.info('Program started')
    except Exception as e: 
        sys.stderr.write('Caught exception in setupLogging: %s' % e)
        return 1		

    if not os.path.isfile(config_file):
        log.critical('Cannot find %s.  ABORTING' % config_file)
        return

    try:
        appconf = Appconf(config_file)
    except Exception as e:
        sys.stderr.write('Appconf(config_file): %s' % e)
        return 1

    appconf_errors  = {}
    appconf_errors = appconf.verify_appconf()
    if len(appconf_errors.keys()):
        for k, v in appconf_errors.iteritems():
            log.critical('Configuration Error: %s: %s' % (k, v))
        return 1
    else:
        for k, v in appconf.appconf.iteritems():
            log.info('%s = %s' % (k, v))


    # Setup server socket
    # a remote dir is specified it means this is a one-shot back load
    threads = []
    serverSocketBound = False
    if not remotedir:
        try:
            thisHost = ''  #'' means local host
            thisPort = int(appconf.appconf['server_port'])
    
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
            log.warning('While attempting to start server socket on port %s raised: %s' % (str(thisPort), e))
    
    
        if isdaemon:
            # make this a daemon
            try:
                log.debug('Before: become_daemon')
                dry.system.become_daemon('.', appconf.appconf['daemon_log'], 
                                         appconf.appconf['daemon_error_log'], 
                                         appconf.appconf['daemon_pid'])
                log.debug('After: become_daemon')
            except Exception as e:
                msg='become_daemon() raised: %s' % (str(e))
                log.critical('%s' % (msg))
                return 1
    
       
        # Start thread to write heartbeat
        try:
            log.debug('Before:hb = Heartbeat(appconf, log)')
            hb = Heartbeat(appconf.appconf, log)
            log.debug('Before: hb.start()') 
            hb.start()
            log.debug('Before: threads.append(hb)') 
            threads.append(hb)
            log.debug('After: threads.append(hb)') 
        except Exception as e:
            log.critical('Caught exception while starting Heartbeat thread: %s' % e)
            return
    
    # start thread to retrieve files
    try:
        log.debug("Before: t = (poller, appconf, log, appconf['sleep_in_seconds'], remotedir)")
        t = Poller('poller', 
                   appconf.appconf, 
                   log, 
                   appconf.appconf['sleep_in_seconds'], 
                   remotedir)
        log.debug('Before: t.start()') 
        t.start()
        log.debug('Before: threads.append(t)') 
        threads.append(t)
        log.debug('After: threads.append(t)')
    except Exception as e:
        msg = 'Caught exception while starting subject thread: %s' % str(e)
        log.critical('%s' % (msg))
        raise e

    # Start thread to listen for shutdown requests
    if serverSocketBound:
        try: 
            log.debug('Before: l = listen(sockobj, threads, log)')
            l = ListenForReq(sockobj, threads, appconf.appconf, log)
            log.debug('Before: l.start()') 
            l.start()
            log.debug('After: l.start()')
        except Exception as e:
            msg = 'Caught exception while starting ListenForReq(): %s' % str(e)
            log.error('%s' % (msg))

    # Wait for feed thread(s) to complete
    log.debug('Before: for t in threads: t.join()')
    for n in threads:
        log.info('Thread member=%s' % n.name)

    for th in threads:
        th.join()
    log.debug('After: for th in threads: th.join()')

    log.info('Shutdown complete')
    logging.shutdown()

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

    server_port = int(app_conf['server_port'])
    server_shutdown = app_conf['server_shutdown_string']

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


def open_files(pid):
    """ Return number of open files for this pid. """
    directory = '/proc/{pid}/fd'.format(pid = pid)
    
    return len(os.listdir(directory))

#==========================================
# main()
#==========================================
def main():
    """ main process """

    usage = """%prog [-Dd] config_file log_file <remote_dir>\n\n
          If remote_dir is specified, the value in the configuration is
          overrddedn and this program retrieves the contents of the directory
          and then exits.  This is for loading historical data.\n
          """
    try:	
        parser = OptionParser(usage)
        parser.add_option("-D", "--debug", dest="isDebug", action="store_true",
                          help="Write debug records (produces a large log file)")
        parser.add_option("-d", "--daemon", dest="isDaemon", action="store_true",
                          help="Run as a daemon")

        [options, args] = parser.parse_args()
        if len(args) < 2:
            parser.error('Incorrect number of arguments')
            return -1
        else:
            config_file = args[0]
            log_file = args[1]
            remotedir = ''
            if len(args) > 2:
                remotedir = args[2]

    except Exception as e:
        print e
        return 1

    isdaemon = True if options.isDaemon else False
    isdebug = True if options.isDebug else False

    go(config_file, log_file, remotedir,  isdebug, isdaemon)

if __name__ == "__main__":
    # call main process and exit with its return code
    sys.exit(main())
