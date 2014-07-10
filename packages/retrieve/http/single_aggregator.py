""" Main program to run a single instance of the aggregator. 
Downloads a list of URLs to download_directory and then moves them
to a directory that acts as an rsync queue.

This queue is polled by a a remote system that rsyncs and deltes the files.
"""
import pdb
import sys
import os
import time
from optparse import OptionParser

import aggregator_settings
sys.path.insert(0, aggregator_settings.PACKAGE_PATH)
import aggregator
import aggregator_conf
import dry.logger 
import dry.system

def feed_list(feedsfile):
    """ Return a list of the contents fo the feed file. """
    feeds_file = feedsfile
    feeds = []
    
    try:
        fh = open(feeds_file, 'rb')
    except IOError as e:
        raise e
    
    try:
        for line in fh:
            buf = line.strip()
            if buf.startswith('#'):
                continue
            else:
                buf_list = buf.split(',')
                feeds.append(buf_list)
            
    except Exception as e:
        raise e
    finally:
        fh.close()
        
    return feeds

def go(configfile, logfile, feedfile, myname, isdebug=False, isdaemon=False):
    """ Top level to run aggregator. """
    config_file = configfile
    log_file = logfile
    feed_file = feedfile
    name = myname
    
    try:
        appconf = aggregator_conf.Appconf(config_file)
    except Exception as e:
        raise Exception('Appconf(config_file): %s' % e)
        #sys.stderr.write('Appconf(config_file): %s' % e)
        #return 1
    
    # If there are any configuration errors, they are written to stderr
    appconf_errors = appconf.verify_appconf()
    if len(appconf_errors.keys()):
        for k, v in appconf_errors.iteritems():
            sys.stderr.write('Configuration Error: %s: %s' % (k, v))
            return 1
            
   # setup logging
    try:
        #log = dry.logger.setupLogging(log_file, 'app', isdebug)
        log = dry.logger.setup_log_timed_rotating(log_file, 
                                                  logname='single_aggregator',
                                                  rotate_when='midnight',
                                                  debug=isdebug, 
                                                  backups = 1024)
        start = time.time()
        log.info('Program started')
    except Exception as e: 
        raise Exception('{f} Caught exception in dry.logger.setup_log_timed_rotating(): {e]'.format(e=e, f = __file__))
        #sys.stderr.write('Caught exception in setupLogging: %s' % e)
        #return 1		

    for k, v in appconf.appconf.iteritems():
        log.info('%s = %s' % (k, v))

    if not os.path.isfile(feed_file):
        log.critical('Cannot find feed file: %s' % feed_file)
        raise Exception('Cannot find feed file: %s' % feed_file)
        #return 1
    
    # Get feeds as a list of tuples to pass to 
    log.debug("Before: feeds = feed_list(feed_file)")
    feeds = feed_list(feed_file)
    log.debug("After: feeds = feed_list(feed_file)")
    
    if not feeds:
        log.critical('Feed list is empty')
        raise Exception('Feed list is empty')
        #return 1
    else:
        log.debug('%d feeds in %s' % (len(feeds), feed_file))
    
    if isdaemon:
        try:
            log.debug('Before: become_daemon')
            dry.system.become_daemon('.', appconf.appconf['daemon_log'], 
                          appconf.appconf['daemon_error_log'], 
                          appconf.appconf['daemon_pid'])
            log.debug('After: become_daemon')
        except Exception as e:
            msg='become_daemon() raised: %s' % (str(e))
            log.critical('%s' % (msg))
            raise Exception('%s' % (msg))
            #return 1

    log.debug("Before: aggregator.go(%s, feeds, appconf.appconf, %s, %s)" %
              (name, log_file, isdebug))
    aggregator.go(name, feeds, appconf.appconf,  
                   log_file, isdebug)
    log.debug("After: aggregator.go(%s, feeds, appconf.appconf, %s, %s)" %
              (name, log_file, isdebug))
        
    download_dir = appconf.appconf['download_dir']
    sync_dir = appconf.appconf['sync_dir']
    
    log.debug("Before: lst = os.listdir(%s)" % download_dir)
    lst = os.listdir(download_dir)
    log.debug("After: lst = os.listdir(%s)" % download_dir)
    
    for fil in lst:
        source = os.path.join(download_dir, fil)
        dest = os.path.join(sync_dir, fil)
        log.debug("Before: os.move(%s, %s)" % (source, dest))
        try:
            os.rename(source, dest)
        except OSError as e:
            log.error('Could not move %s to %s: %s' % (source, dest, e))
            continue
        
        log.debug("After: os.move(%s, %s)" % (source, dest))
        log.info('Moved %s to %s' % (source, dest))
        
    log.info('Elapsed time=%f.' % (time.time() - start))
    
    
# An example of a main() to call this module
def main():
    """
    main process
    """
    usage = '%prog [-Ddl] config_file log_file feed_file name'
    try:	
        parser = OptionParser(usage)
        parser.add_option("-D", "--debug", dest="isDebug", action="store_true",
                          help="Write debug records (produces a large log file)")
        parser.add_option("-d", "--daemon", dest="isDaemon", action="store_true",
                          help="Run as a daemon.")

        
        [options, args] = parser.parse_args()
        if len(args) < 4:
            parser.error('Incorrect number of arguments')
            return -1
        else:
            config_file = args[0]
            log_file = args[1]
            feed_file = args[2]
            name = args[3]
    except Exception as e:
        print e
        return 1

    options.isDebug = True if options.isDebug else False
    options.isDaemon = True if options.isDaemon else False
    try:
        go(config_file, 
                   log_file, 
                   feed_file, 
                   name,
                   options.isDebug,
                   options.isDaemon)
    except Exception as e:
        sys.stderr.write(e)


if __name__ == "__main__":
    # call main process and exit with its return code
    sys.exit(main())