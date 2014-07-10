""" Traverse a directory structure and delete all files older than n days. 
"""
import pdb
import sys
import os
import datetime
import time
import collections
import optparse 
import ConfigParser 
import multiprocessing
import threading

import settings
sys.path.insert(0, settings.PACKAGE_PATH)

import dry.logger 

__author__ = ('hancock.robert@gmail.com (Robert Hancock)')
__version__ = "1.1.0f"

LOG = None

def app_conf(config_file):
    """ Read the confinguration file and return a named tuple. 
    Raises 
        OSError if config_file cannot be found.
        ValueError if a non-integer value is supplied.
        
    Return
        A named tuple with the configuration key - value combinations.
    """
    
    if not os.path.isfile(config_file):
        raise OSError('Cannot finD {f}'.format(f=config_file))
    
    app_config = collections.namedtuple('application_config',
                                        '''base_dirs, 
                                        age_in_days,
                                        cpus_allocated''')

    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    appconf_dict = {}

    appconf_dict['base_dirs'] = config.get('dir', 'base')
    
    #if not os.path.isdir(appconf_dict['base_dirs']):
        #raise OSError('base_dirs: {dr} cannot be found'.format(
            #dr=appconf_dict['base_dirs']))
    
    try:
        appconf_dict['age_in_days'] = config.getint('age', 'in_days')
    except ValueError as e:
        raise ValueError('age_in_days: {ex}'.format(ex=e))
    
    try:
        appconf_dict['cpus_allocated'] = config.getint('cpus', 'allocated')
    except ValueError as e:
        raise ValueError('cpus_allocated: {ex}'.format(ex=e))

    return app_config(**appconf_dict)

def get_base_dirs(basedirs, log):
    """
    Arguments
        basedirs   A colon separated string of directories.
        log        A logger handle
    
    Returns
        A list of valid directories.
    """
    base_dirs = []
    buf = basedirs.split(':')
    for item in buf:
        if not os.path.isdir(item):
            log.error('Invalid base directory in config file: {dr}'.format(dr=item))
        else:
            base_dirs.append(item)
            
    return base_dirs
        
def exclusion_list(filename):
    """ Make exclusion file into a dictionary.
    We only place the value in the key of the dict to allow an O(1) lookup. 
    
    Arguments
        A valid file name
        
    Raises
        OSError if the file contains an invlaid directory.
        IOError if there is a problem reading the file.
        
    Returns
        A dictionary of files and directories to be excluded from the 
        interrogation process.
    """
    
    exclusions = {}
    
    try:
        with open(filename) as fh:
            for line in fh:
                if line[0] == '#':
                    continue
                
                line = line.strip()
                if line != '':
                    if not os.path.isdir(line):
                        raise OSError('{l} is not a vailid directory.'.format(
                            l = line))
                    exclusions[line] = ''
    except IOError as e:
        raise IOError('file = {f}: {ex}'.format(f = filename, ex = e))
    
    return exclusions


def delete_file(q):
    """ Read full path filenames from the queue and delete them.
    This is the consumer procedure of the file compression routine.

    If the item from the queue equals None, this is a sentinel that signals
    this procedure to exit.
    
    Arguments
        q    a JoinableQueue
        
    """
    LOG.debug('Started instance of delete_file')
    while True:
        LOG.debug('Before: fullpath_filename = input_q.get()')
        fullpath_filename = q.get()
        LOG.debug('After: {ff} = input_q.get()'.format(ff=fullpath_filename))

        if fullpath_filename is None: # Sentinel
            LOG.debug('Found sentinel.')
            q.task_done()
            break
        
        if os.path.isfile(fullpath_filename):
            if settings.DRY_RUN:
                LOG.info('DRY RUN deleted file {f}.'.format(f = fullpath_filename))
            else:
                mtime = os.path.getmtime(fullpath_filename)
                time_tuple = time.localtime(mtime)
                timestamp = '{y}_{m}_{d} at {h}:{M}:{s}'.format(
                    y = time_tuple.tm_year,
                    m = time_tuple.tm_mon,
                    d = time_tuple.tm_mday,
                    h = time_tuple.tm_hour,
                    M = time_tuple.tm_min,
                    s = time_tuple.tm_sec)
                try:
                    os.remove(fullpath_filename)
                    LOG.info('Deleted file {f}: mtime={t}.'.format(
                        f = fullpath_filename,
                        t = timestamp))
                except OSError as e:
                    LOG.error("os.remove(%s): %s" % (fullpath_filename, e))
        else:
            LOG.warning('{f} cannot be found.'.format(f=fullpath_filename))
            
        q.task_done()


def delete_dir(q):
    """ Read full path dirnames from the queue and delete them if
    the directory is empty.
    
     If the item from the queue equals None, this is a sentinel that signals
     this procedure to exit.
     
    Arguments
        q    a JoinableQueue
        
     """

    LOG.debug('Started instance of delete_dir')
    while True:
        LOG.debug('Before: fullpath_dirname = input_q.get()')
        fullpath_dirname = q.get()
        LOG.debug('After: {ff} = q.get()'.format(ff=fullpath_dirname))

        if fullpath_dirname is None: # Sentine
            LOG.debug('Found sentinel.')
            q.task_done()
            break

        if os.path.isdir(fullpath_dirname):
            if len(os.listdir(fullpath_dirname)) == 0: # is dir empty?
                if settings.DRY_RUN:
                    LOG.info('DRY RUN Deleted directory {dr}.'.format(
                        dr = fullpath_dirname))
                else:
                    try:
                        os.rmdir(fullpath_dirname)
                        LOG.info('Deleted directory {f}.'.format(
                            f = fullpath_dirname))
                    except OSError as e:
                        LOG.error("os.remove(%s): %s" % (fullpath_dirname, e))
            else:
                LOG.warning('{d} is not empty.'.format(d = fullpath_dirname))
        else:
            LOG.warning('{f} cannot be found..'.format(f=fullpath_dirname))    
            
        q.task_done()

        
def find_files(home, age_in_days, exclude_dirs, exclude_files, q_files):
    """ Find files that are old enough to delete and are not in any of
    the exclusion or static lists and put them on the queue.
    
    Arguments
        home           The base of the directory tree to interrogate
        age_in_days    Files older than this will be put on the queue.
        exclude_dirs   A list of directories to exclude from interrogation.
        exclude_files  A list of files to exclude from interrogation.
        q_files        A JoinableQueue on which files older than age_in_days will be places.
    """
    # aging vars
    t = datetime.datetime.today()
    today_at_midnight = datetime.datetime(t.year, t.month, t.day, 0, 0, 0, 0)
    LOG.debug('today_at_midnight = %s' % today_at_midnight)

    interval = datetime.timedelta(days=age_in_days) 
    LOG.debug('interval=%s' % interval)

    aging_date = today_at_midnight - interval
    LOG.debug('aging_date=%s' % aging_date)

    aging_date_epoch = time.mktime(aging_date.timetuple())
    LOG.debug('aging_date_epoch=%f' % aging_date_epoch)

    # Traverse the directory structure and place directories and files
    # elgible for deletion into lists.
    # TO DO 
    # since the amount of files could be huge, restructure this as
    # a pipline of generators and coroutines.
    for dirpath, dirs, files in os.walk(home, topdown=False):
        for f in files:
            fullpath_f = os.path.join(dirpath, f)
            LOG.debug('Checking %s.' % fullpath_f)

            if fullpath_f not in exclude_files and dirpath not in exclude_dirs:
                # Is it old enough to be deleted?
                if os.path.getmtime(fullpath_f) < aging_date_epoch:
                    q_files.put(fullpath_f)
            else:
                if f in exclude_files:
                    LOG.debug('%s in exclusion_files' % f)
                elif fullpath_f in exclude_files:
                    LOG.debug("%s in exclusion_files" % fullpath_f)
                else:
                    LOG.debug("Something odd happened while examining %s" % fullpath_f)    
                    
def find_empty_dirs(home, exclude_dirs, static_dirs, q_dirs):
    """ Find empty directories and place them on a queue. 

    Arguments
        home           The base of the directory tree to interrogate
        exclude_dirs   A list of directories to exclude from interrogation.
        static_dirs    A list of directories that can remain even if they are empty.
        q_dirs         A JoinableQueue on which empty dirs are placed.
    """
    global LOG
    
    for dirpath, dirs, files in os.walk(home, topdown=True):
        for dr in dirs:
            fullpath_d = os.path.join(dirpath, dr)
            LOG.debug('Checking for empty dir %s.' % fullpath_d)
    
            if fullpath_d not in exclude_dirs and fullpath_d not in static_dirs:
                if len(os.listdir(fullpath_d)) == 0:
                    # directory is empty, add to queue
                    q_dirs.put(fullpath_d)

def main():
    """ main process """
    global LOG

    usage = '%prog [-DdFV] config_file log_file'
    parser = optparse.OptionParser(usage)
    parser.add_option("-D", "--exclude_dirs_file",
                      action="store", type="string", dest="exclude_dirs_file",
                      help="Directories excluded from consideration.")
    parser.add_option("-d", "--static_dirs_file",
                      action="store", type="string", dest="static_dirs_file",
                      help="Delete directory contents, but not directory.")
    parser.add_option("-F", "--exclude_files_file",
                      action="store", type="string", dest="exclude_files_file",
                      help="Files excluded from consideration.")
    parser.add_option("-V", "--version",
                      action="store_true", dest="pversion",
                      help="Print version")
    #parser.add_option("-f", "--static_files",
            #action="store", type="string", dest="static_files"),

    [options, args] = parser.parse_args()
    if options.pversion:
        print("delfiles version {v}".format(v=__version__))
        return 0
    
    if len(args) < 2:
        parser.error('Incorrect number of arguments')
        return 1
    else:
        config_file = args[0]
        log_file = args[1]

    # setup logging
    try:
        LOG = dry.logger.setup_log_size_rotating(log_file, 
                                                 logname='delfiles',
                                                 debug=settings.DEBUG)
    except Exception as e: 
        sys.stderr.write('Caught exception in setupLogging: %s' % e)
        return 1		

    LOG.info('Program started')
    if settings.DRY_RUN:
        LOG.info('This is a DRY RUN.')
        
    start_time = time.time()
    exclude_dirs = []
    static_dirs = []

    if not os.path.isfile(config_file):
        LOG.info('Cannot find {f}.'.format(f = config_file))
        return 1
    
    # read config
    try:
        appconf = app_conf(config_file)
    except (ConfigParser.NoSectionError, 
            ConfigParser.DuplicateSectionError,
            ConfigParser.NoOptionError, 
            ConfigParser.InterpolationError,
            ConfigParser.MissingSectionHeaderError,
            ConfigParser.ParsingError,
            ValueError,
            OSError) as e:
        msg=('Fatal Error: Caught exception in appconf: %s: %s' 
             % (e.__class__, e))
        LOG.critical(msg)
        return 1
    
    max_cpus = multiprocessing.cpu_count()
    
    if appconf.cpus_allocated == 0:
        cpus_allocated = max_cpus
    else:
        if appconf.cpus_allocated > max_cpus:
            cpus_allocated = max_cpus
        else:
            cpus_allocated = appconf.cpus_allocated
                     
    if settings.DEBUG:
        dc = appconf._asdict()
        for k, v in dc.iteritems():
            LOG.debug('%s = %s' % (k, v))    
            
    # process command line options
    if options.exclude_dirs_file:
        if  os.path.isfile(options.exclude_dirs_file):
            try:
                
                exclude_dirs = exclusion_list(options.exclude_dirs_file)
            except (IOError, OSError) as e:
                LOG.critical('exclusion_list({l}): {ex}'.format(
                    ex=e,
                    l = options.exclude_dirs_file))
                return 1
        else:
            LOG.critical('Cannot find {f}.'.format(f = options.exclude_dirs_file))
            return 1
    else:
        exclude_dirs = []
        
    LOG.info('Size of exclude_dirs={n}'.format(n=len(exclude_dirs)))

    if options.static_dirs_file:
        if os.path.isfile(options.static_dirs_file):
            try:
                static_dirs = exclusion_list(options.static_dirs_file)
            except (IOError, OSError) as e:
                LOG.critical('exclusion_list({l}): {ex}'.format(
                    ex=e, 
                    l = options.static_dirs_file))
                return 1
        else:
            LOG.critical('Cannot find {f}.'.format(f = options.static_dirs_file))
            return 1
    else:
        static_dirs = []
        
    LOG.info('Size of static_dirs={n}'.format(n=len(static_dirs)))

    if options.exclude_files_file:
        if os.path.isfile(options.exclude_files_file):
            try:
                exclude_files = exclusion_list(options.exclude_files_file)
            except (IOError, OSError) as e:
                LOG.critical('exclusion_list({l}): {ex}'.format(
                    ex=e, 
                    l = options.exclude_files_file))
                return 1
        else:
            LOG.critical('Cannot find {f}.'.format(f=options.exclude_files_file))
            return 1        
    else:
        exclude_files = []
        
    LOG.info('Size of exclude_files={n}'.format(n=len(exclude_files)))

    base_dirs = get_base_dirs(appconf.base_dirs, LOG)

    if not base_dirs:
        LOG.critical('No valid base directories were specificed in the config file.')
        return 1
    
    #====== Setup process to delete aged files. ======================#
    # Setup consumer processes (delete files) to read queue.
    # Place aged file names on queue
    # Place sentitnels on queue to signify that there are no more files to come.
    # Join the queue to allow it to server all entries.
    # Join the consumer processes to allow them to finish.
    q_files = multiprocessing.JoinableQueue()
    file_delete_consumer_processes = []

    for n in range(cpus_allocated):
        file_delete_consumer_p = multiprocessing.Process(target=delete_file, 
                                                         args=(q_files,))
        file_delete_consumer_p.set_daeom=True
        file_delete_consumer_p.start()
        file_delete_consumer_processes.append(file_delete_consumer_p)
    
    # Producer finds files more than n days old and places them
    # on a queue.  As they are placed on q_files the consumer
    # process deletes them.
    # Since there is a lot of IO blocking, the find files processes can be put
    # into threads instead of processes.
    threads = []
    
    for b_dir in base_dirs:
        th = threading.Thread(target=find_files, args=(
            b_dir, 
            appconf.age_in_days,
            exclude_dirs,
            exclude_files,
            q_files))
        
        th.daemon=True
        threads.append(th)
        th.start()
        
    for thread in threads:
        thread.join()
        
    # Single dir for testing    
    #find_files(appconf.base_dir, 
               #appconf.age_in_days,
               #exclude_dirs,
               #exclude_files,
               #q_files)
    
    # Now that the producers are finished, place a sentinel on the queues for each
    # consumer process to signify the end of the queue.
    LOG.debug('Before adding None to q_files')
    for nx in range(len(file_delete_consumer_processes)):
        LOG.debug('Before adding None to q_files: {nx}'.format(nx = nx))
        q_files.put(None)
    LOG.debug('After adding None to q_files')        
    
    LOG.debug('Before q_files.join()')
    q_files.join()
    LOG.debug('After q_files.join()')

    # Wait unitl all the file delete consumer processes are finished.
    # Part of the directory deletion process is to see if the directory is
    # empty before deleting it, so the entire file deletion process needs to
    # complete before the dir deletion begins.
    LOG.debug('Before for process in file_delete_consumer_processes:')
    
    # It is possible that some of theses process could have already have found the
    # the sentinel and stopped and hence cannot join.
    for proc in file_delete_consumer_processes:
        #if proc.is_alive():
        proc.join()        
        
    LOG.debug('After for process in file_delete_consumer_processes:')        
    
    #======= You have deleted all the eligible files, now delete 
    # the empry directories. =====
    # Same sequence of events as the aged files above.
    # You have deleted all the eligible files, now find empty directories.
    # Any empty directories that are not in the exclude or static lists
    # will be deleted.
    q_dirs = multiprocessing.JoinableQueue()
    dir_delete_consumer_processes = []

    LOG.debug('Before setup of dir_delete_consumer processes')
    for n in range(cpus_allocated):
        dir_delete_consumer_p = multiprocessing.Process(target=delete_dir, 
                                                        args=(q_dirs,))
        dir_delete_consumer_p.set_daeom = True
        dir_delete_consumer_p.start()
        dir_delete_consumer_processes.append(dir_delete_consumer_p)    

    empty_dir_threads = []
    for base in base_dirs:
        th = threading.Thread(target=find_empty_dirs, args=(base, 
                                             exclude_dirs,
                                             static_dirs, 
                                             q_dirs))
        th.daemon = True
        empty_dir_threads.append(th)
        th.start()
         
    for thread in empty_dir_threads:
        thread.join()
        
    for n in range(cpus_allocated):
        q_dirs.put(None)
    
    LOG.debug('Before for p in dir_delete_consumer_processes:')
    for p in dir_delete_consumer_processes:
        p.join()
    LOG.debug('After for p in dir_delete_consumer_processes:')        
    
    LOG.debug('Before q_dirs.join()')
    q_dirs.join()
    LOG.debug('After q_dirs.join()')

    LOG.info("Program completed.")
    elapsed_time = time.time() - start_time
    LOG.info('Elapsed time = {t} seconds'.format(t = elapsed_time))

if __name__ == "__main__":
    sys.exit(main())
