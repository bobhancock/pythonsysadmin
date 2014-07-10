""" 
1. rsync files from a remote server
2. Issue a command to the remote server to delete files more than n days old.
3. Compress all files more than n days old on the local server


STATUS
   The file deletion process is run as a cronjobj on the production server.
   The skeleton code for making a remote request at the end of the rsync
   process is kept here, but commented out.
   
TO DO
- Insure that all logging statement use a name of product or process.
- Better interrogation of stderr output from rsync.
"""
#import pdb
import os
import sys
import time
import logging
import multiprocessing
import threading
import subprocess
import datetime
import shutil
import collections
from optparse import OptionParser
#import paramiko
import select
import gzip

import settings
sys.path.insert(0, settings.PACKAGE_PATH)

import dry.logger

__version__ = "1.0"


def do_rsync(product_conf):
    """ rysnc files from remote servers.
    
    Arguments
        product_conf - named tuple with the fields
            name, 
            username, 
            password,
            remote_root,
            local_root, 
            exclude_dirs_file
            
    Raises
        Exception on logger error
        OSError - when certain system calls fail.
    """
    
    # Make the tuple elements into local variables to 
    # cutdown on multiple calls to the tuple.
    if not isinstance(product_conf, tuple):
        raise TypeError('''do_rsync(): Argument product_conf must be of type
        collections.namedtuple not {t}'''.format(t=type(product_conf)))
    
    remote_host = settings.REMOTE_HOST
    name = product_conf.name
    user_name = product_conf.username
    remote_dir = product_conf.remote_root
    local_dir = product_conf.local_root
    exclude_dirs_file = product_conf.exclude_dirs_file
    proc_dir = os.path.join(settings.APPLICATION_DIR, product_conf.name)
    rsync_bin = settings.RSYNC_BIN
    
    rsync_log = os.path.join(proc_dir, settings.LOG_FILE)
    rsync_stdout = os.path.join(proc_dir, settings.RSYNC_STDOUT)
    rsync_stderr = os.path.join(proc_dir, settings.RSYNC_STDERR)
    lock_file = os.path.join(proc_dir, settings.LOCK_FILE)
    log_file = os.path.join(proc_dir, '{name}_rsync.log'.format(name=name))
    
    # Setup logging for this process
    try:
        log = dry.logger.setupLogging(log_file, 
                                      name,
                                      settings.DEBUG)
    except Exception as e:
        log.error('''{n}: log = dry.logger.setupLogging({logfile}, 
        {name}, {debug}'''.format(n = name,
                                  logfile = log_file, 
                                  name=name,
                                  debug=settings.DEBUG))
        return
    
    log.info('{name}: rsync() started'.format(name=name))
    start_time = time.time()
  
    if not os.path.isdir(proc_dir):
        try:
            os.makedirs(proc_dir)
        except OSError as e:
            msg = '{n}: Cannot create {procdir}: {ex}'.format(n=name,procdir=proc_dir, ex=e)
            log.error(msg)
            raise OSError(msg)
        
    # Insure that the local directory does not end in '/'
    if local_dir.endswith('/'):
        local_dir = local_dir[:-1]    
    
    # Verify that the local directory for the rsync exists
    if not os.path.isdir(local_dir):
        try:
            os.makedirs(local_dir)
            log.debug('{n} Created directory {localdir}'.format(
                n=name, 
                localdir=local_dir))
        except OSError as e:
            msg = '{n}: Could not create {localdir}: {ex}'.format(
                n=name, 
                localdir=local_dir, 
                ex=e)
            log.critical(msg)
            raise IOError(msg)

    log.debug('{n}: Verified existence of {localdir}'.format(n=name, localdir=local_dir))
    
    # Insure that the remote directory ends in '/'
    if not remote_dir.endswith('/'):
        remote_dir = remote_dir+'/'
        log.debug('{n}: Added "/" to {remotedir}'.format(n=name, remotedir=remote_dir))
        

    # If True in settings, then unconditionally delete the lock
    # file before proceeding. 
    if settings.DELETE_LOCKFILE:
        if os.path.isfile(lock_file):
            log.debug('{n}: {l} exists'.format(n=name,l=lock_file))
            try:
                os.remove(lock_file)
                log.info('{n}: {l} deleted'.format(n=name,l=lock_file))
            except OSError as e:
                msg = 'Cannot delete %s.  ABORTING: %s' % (lock_file, e)
                log.critical(msg)
                raise OSError(msg)
    
    # If a lock file exists there is an instance or rsync for this product already running
    if os.path.isfile(lock_file):
        log.error('''{n}: {n} exists. Either previous invocation of rsync is 
        still running or it terminated improperly.  This script will not 
        rsync.'''.format(n=name, l=lock_file))
        return
    else:
        with open(lock_file, 'wt') as fh_lock:
            fh_lock.write('I am a semaphore')
            log.debug('Created lock file')

    # Check the size of the rsync_stdout file.  If it is too big
    # then delete it.  It grows with each invocation and we 
    # use it only to verify the last run.
    # This file is simply the output of stdout when rsync is invoked with -v
    if os.path.isfile(rsync_stdout):
        if os.path.getsize(rsync_stdout) > (1024 * 1000000):
            try:
                os.remove(rsync_stdout)
                log.debug('{n}: Deleted {rstdout}'.format(n=name, 
                                                          rstdout=rsync_stdout))
            except OSError as e:
                log.warning('Could not delete %s.: %s' % (rsync_stdout, e))

    now = time.strftime("%m/%d/%y %H:%M:%S", time.localtime())
    
    # Write the current time so if we have to debug we have
    # a starting point.
    with open(rsync_stdout, 'at') as fh_stdout:
        fh_stdout.write('\n'+now+'\n')
        fh_stdout.flush()
        log.debug('{n}: Opened {rstdout}'.format(n=name, rstdout=rsync_stdout))
    
        
    if settings.DRY_RUN:
        rsync_args = 'avzn'
    else:
        rsync_args = 'avz'
        
    if exclude_dirs_file:
        # =====> N.B. This needs to be on one line.  You cannot break with triple quotes
        # or the continuation character.  It must be one unbroken string passed to subprocess.
        cmdline_rsync = '{rsyncbin} -{args} --exclude-from={exclude} {username}@{remotehost}:{remotedir} {localdir}'.format(
            rsyncbin = rsync_bin,
            args=rsync_args,
            exclude = exclude_dirs_file,
            username = user_name,
            remotehost = remote_host,
            remotedir = remote_dir,
            localdir = local_dir)
    else:
        cmdline_rsync = '{rsyncbin} -{args} {username}@{remotehost}:{remotedir} {localdir}'.format(
            rsyncbin = rsync_bin,
            args=rsync_args,
            username = user_name,
            remotehost = remote_host,
            remotedir = remote_dir,
            localdir = local_dir)
    
    log.debug('cmdline_rsync={0}'.format(cmdline_rsync))

    # Run rsync as a subprocess
    try:
        log.debug('{n}: Before rsync {c}'.format(n=name, c=cmdline_rsync))
        start = time.time()                   
        try:
            with open(rsync_stdout, 'at') as fh_stdout:
                with open(rsync_stderr, 'at') as fh_stderr:
                    subprocess.check_call(cmdline_rsync, 
                                          shell=True, 
                                          stdout=fh_stdout, 
                                          stderr=fh_stderr)
        except subprocess.CalledProcessError as e:
            log.error('''n}: subprocess.check_call({c}, shell=True): {ex}. 
            Check: {r}.'''.format(c=cmdline_rsync, ex=e, r=rsync_log))
            return

        end = time.time()
        log.debug('{n}: After rsync {r}'.format(n=name, r=cmdline_rsync))
        elapsed = end - start
        log.info('{n}: rsync with {r} succeeded. Elapsed time={e} seconds.'.format(
                      n=name, r=remote_host, e=str(elapsed)))
        
    finally:
        try:
            log.debug("{n}: Before: os.remove(lock_file)".format(n=name))
            os.remove(lock_file)
            log.debug("{n}: After: os.remove(lock_file)".format(n=name))

        except OSError as e:
            log.critical('{n}: Cannot remove lock file {l}.  '
                              +'This will prevent subsequent rsyncs '
                              +'from executing.'.format(n=name, l=lock_file))
            
        try:
            if not fh_stdout.closed:
                fh_stdout.close()
            if not fh_stderr.closed:
                fh_stderr.close()
        except IOError as e:
            log.error(e)
            
    # Since we are capturing stdout with -v we should have a record of
    # all files that were rsynced. Copy this file with a date time stamp.
    lt = time.localtime()
    timestamp = '{y}{m}{d}_{h}{M}{s}'.format(y=lt.tm_year, m=lt.tm_mon, d=lt.tm_mday,
                                             h=lt.tm_hour, M=lt.tm_min, s=lt.tm_sec)
    if os.path.isfile(rsync_stdout):
        dest_file = os.path.join(proc_dir, '{0}.{1}'.format(rsync_stdout, timestamp))
        shutil.copy(rsync_stdout, dest_file)
    else:
        log.warning('{n}: After rsync, could not find {r}'.format(n=name, r=rsync_stdout))
        
    
    # Interrogate the stderr file to see if there is any text that
    # does not start with "#"
    if os.path.isfile(rsync_stderr):
        dest_file = os.path.join(proc_dir, '{0}.{1}'.format(rsync_stderr, timestamp))
        shutil.copy(rsync_stderr, dest_file)
        
        # Read this file to see if there are any lines that do not begin with "#"
        # If only lines that start id a pound symbol are found, delete the file.
        error_found = False
        with open(dest_file) as fh_stderr_copy:
            for line in fh_stderr_copy:
                if not line.startswith('#'):
                    error_founc = True
                    log.error('''{n}: {fh} has error stderr text'''.format(
                        n=name, 
                        fh=dest_file))
                    
        if not error_found:
            os.remove(dest_file)
            
    elapsed_time = time.time() - start_time
    log.info('{name}: rsync() complete: {t}'.format(name=name, t=elapsed_time))
                
def find_files_to_compress(product_conf, output_q):
    """ Find files on the archive server older than n days and
    place them on the output q.
    This is the producer portion of the file compression section
    
    Arguments
        product_conf - named tuple; see above for details.
        output_q - a JoinableQueue
        
    Raises
       TypeError - invalid argument types
    """
    if not isinstance(product_conf, tuple):
        raise TypeError('product_conf must be of type collections.namedtuple')
    
    if not isinstance(output_q, multiprocessing.queues.JoinableQueue):
        raise TypeError("output_q must be of type multiprocessing.JoinableQueue")
    
    if not os.path.isdir(product_conf.local_root):
        raise IOError("Cannot find product_conf.local_root:{dr}".format(
            dr = product_conf.local_root))
    
    p_name = product_conf.name
    
    # aging vars
    t = datetime.datetime.today()
    today_at_midnight = datetime.datetime(t.year, t.month, t.day, 0, 0, 0, 0)
    LOG.debug('{n}: today_at_midnight = {m}'.format(n=p_name, m=today_at_midnight))

    age_in_days = int(settings.AGING_DAYS_FOR_COMPRESSION)
    interval = datetime.timedelta(days=age_in_days) 
    LOG.debug('{n}: interval={i}'.format(n=p_name, i=interval))

    aging_date = today_at_midnight - interval
    LOG.debug('{n}: aging_date=%s.format(n=p_name,' % aging_date)

    aging_date_epoch = time.mktime(aging_date.timetuple())
    LOG.debug('{n}: aging_date_epoch={a}'.format(n=p_name, a=aging_date_epoch))
    
    for dirpath, dirs, files in os.walk(product_conf.local_root, topdown=False):
        for f in files:
            fullpath_filename = os.path.join(dirpath, f)
            LOG.debug('{n}: Checking {f}.'.format(n=p_name, f=fullpath_filename))

            if fullpath_filename.endswith('.txt') or fullpath_filename.endswith('.xml'):
                if os.path.getmtime(fullpath_filename)  < aging_date_epoch:
                    # Place on the queue to make it eligible for compression
                    output_q.put(fullpath_filename)
                    LOG.debug('{n}: Put on queue - {f}.'.format(
                        n=p_name, 
                        f=fullpath_filename))

                    
def compress_files(input_q):
    """ Read full path filenames from the queue and compress them.
    This is the consumer procedure of the file compression routine.
    
    If the item from the queue equals None, this is a sentinel that signals
    this procedure to exit.
    
    If a file with this name already exists, it will not overwrite it.
    
    Arguments
       input_q - JoinableQueue
    """
    LOG.debug('Started instance of compress_files')
    while True:
        LOG.debug('Before: fullpath_filename = input_q.get()')
        fullpath_filename = input_q.get()
        LOG.debug('After: {ff} = input_q.get()'.format(ff=fullpath_filename))
        
        if fullpath_filename is None:
            break
        
        if (not fullpath_filename.endswith('.gz') 
            and not fullpath_filename.endswith('.zip')):
            old_dir = os.getcwd()
            
            # Full path directory portion of fullpath filename.
            dirpath = os.path.dirname(fullpath_filename)
            
            try:
                os.chdir(dirpath)
            except Exception as e:
                LOG.warning('os.chdir({d}): {ex}'.format(d=dirpath, ex=e))
                os.chdir(old_dir)
                continue
            
            source_file = fullpath_filename
            gzfile = source_file+'.gz'
            source_size = os.path.getsize(source_file)
            
            try:
                f_in = open(source_file, 'rb')
            except IOError as e:
                LOG.error('f_in = open(%s, \'rb\'): %s' % (source_file, e))
                os.chdir(old_dir)
                continue
            
            try:
                f_out = gzip.open(gzfile, 'wb')
            except IOError as e:
                LOG.error("f_out = gzip.open(%s, 'wb'): %s" % (gzfile, e))
                f_in.close()
                os.chdir(old_dir)
                continue
            
            f_out.writelines(f_in)
            f_out.close()
            f_in.close()
            
            if os.path.isfile(gzfile):
                try:
                    os.remove(source_file)
                except Exception as e:
                    LOG.error("os.remove(%s): %s" % (source_file, e))
                    
            compressed_size = os.path.getsize(gzfile)
            
            compression_ratio = 100 - ((float(compressed_size) 
                                        / float(source_size)) * 100)
            
            compression_ratio = round(compression_ratio, 2)

            LOG.info('''Compressed {s} from {sz} bytes to {cz} bytes: 
            {rat}%'''.format(s=source_file, 
                             sz=source_size, 
                             cz=compressed_size,
                             rat=compression_ratio))            
            
            os.chdir(old_dir)
        else:
            LOG.warning('{f} already exists.  Will not overwrite.'.format(
                f=fullpath_filename))
    
    
def main():
    """ Run rsync process. """
    rsync_bin = settings.RSYNC_BIN
    dellockfile = settings.DELETE_LOCKFILE
    lock_file = settings.LOCK_FILE
    global LOG
    
    # setup logging
    try:
        LOG = dry.logger.setupLogging(os.path.join(
            settings.APPLICATION_DIR, 'rx_rsync.log'), 
                                      'rx_rsync',
                                      settings.DEBUG)
        LOG.info('Program started')
    except Exception as e: 
        raise Exception('Caught exception in setupLogging: %s' % e)

    start_time = time.time()

    # A named tuple with configuration info for each product.
    product_confs = settings.product_confs
    
    max_products = processes = len(product_confs)
    max_cpus = multiprocessing.cpu_count()
    
    # rsync the files from the remote server.
    pool = multiprocessing.Pool(processes=max_products)  
    pool.imap_unordered(do_rsync, product_confs)
    pool.close()
    pool.join()
    
    # Single version for debugging.
    #do_rsync(product_confs[0])

    # Since gzip can be CPU intensive we want to compress each file with a separate
    # CPU.  We create max_products processes (the producer) that scan the
    # directory trees
    # of each product for eligible files.  When a file is found, it is placed on a 
    # shared queue.  The consumer reads the queue and compresses each file.
    #
    # When the producer is finished it needs to place a sentinel, 
    # in this case None, on the 
    # queue.  You need a sentinel for each consumer processes.
    # Find files more than n days old and compress.
    q = multiprocessing.JoinableQueue()
    
    consumer_processes = []
    
    for n in range(max_cpus):
        consumer_p = multiprocessing.Process(target=compress_files, args=(q,))
        consumer_p.set_daeom=True
        consumer_p.start()
        consumer_processes.append(consumer_p)
                                             
    producer_processes = []
    
    for product_conf in product_confs:
        producer_p = multiprocessing.Process(target=find_files_to_compress, 
                                             args=(product_conf, q))
        producer_p.set_daemon = True
        producer_p.start()
        producer_processes.append(producer_p)
        
    # Block until all the producer processes are complete
    for p in producer_processes:
        p.join()
        
    # Producers are finished, so place a sentinel on the queue for each
    # consumer process.
    for n in range(max_cpus):
        q.put(None)
   

    # Wait unitl all the consumer process are finished.
    # They will exit when the find the None sentinel in the queue.
    for pr in consumer_processes:
        pr.join()        

    end_time = time.time()
    elapsed_time = end_time - start_time
    LOG.info('Elapsed time in seconds: {el}'.format(el=elapsed_time))
    LOG.info('Shutdown complete.')
    logging.shutdown()

if __name__ == '__main__':
    sys.exit(main()) 