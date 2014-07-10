""" Aggregator manager. 
This is the module that reads the database for a list of urls and then
forks the appropriate number of processes.
"""
import os
import sys
from multiprocessing import Process, cpu_count
from ConfigParser import SafeConfigParser
from optparse import OptionParser


from aggregator_settings import PACKAGE_PATH
sys.path.insert(0, PACKAGE_PATH)

from aggregator_conf import appconf, verify_appconf
from dry.logger import setupLogging as setup_logging
from dry.system import become_daemon as become_daemon
from retrieval_list import RetrievalList

from aggregator import run_aggregator

def main():
    
    try:	
        usage = """%prog [-Dd]\n\n"""
        parser = OptionParser(usage)
        parser.add_option("-D", "--debug", dest="isDebug", action="store_true",
                          help="Write debug records (produces a large log file)")
        parser.add_option("-d", "--daemon", dest="isDaemon", action="store_true",
                          help="Run as a daemon")

        [options, args] = parser.parse_args()
    except Exception as e:
        print e
        return 1
    
    # setup logging
    try:
        options.isDebug = True if options.isDebug else False
        log = setup_logging(appconf['log_file'], 'aggregator', options.isDebug)
        log.info('Program started')
    except Exception as e: 
        sys.stderr.write('Caught exception in setupLogging: %s' % e)
        return 1		

    appconf_errors  = {}
    appconf_errors = verify_appconf()
    
    log.debug("Before: if len(appconf_errors.keys()):")
    if len(appconf_errors.keys()):
        for k, v in appconf_errors.iteritems():
            log.critical('Configuration Error: %s: %s' % (k, v))
        sys.exit(1)
    else:
        for k, v in appconf.iteritems():
            log.info('%s = %s' % (k, v))

    options.isDaemon = True if options.isDaemon else False
    if options.isDaemon:
        # make this a daemon
        try:
            log.debug('Before: become_daemon')
            become_daemon('.', appconf['daemon_log'], 
                          appconf['daemon_error_log'], 
                          appconf['daemon_pid'])
            log.debug('After: become_daemon')
        except Exception as e:
            msg='become_daemon() raised: %s' % (str(e))
            log.critical('%s' % (msg))
            return 1

    max_processes = cpu_count() 
    
    # TESTING
    # --> Read list of feeds from an imported dictionary
    #get max records in SQLite table of feeds
    # Divide by number of processes
    # create a list of tuples for each process

    from feed_addr import rss_feed as rss_feeds
    listfeeds = list(rss_feeds)

    process_list = []
    logfile = "/var/tmp/aggregator.log",
    debug = False
    aggregator_name = "Test"
    
    p = Process(target=run_aggregator, 
                args=(listfeeds, appconf, 
                      aggregator_name, logfile,
                      debug))
    p.start()
    p.join()
    process_list.append(p)
    
    for pr in process_list:
        pr.join()
        
    #?? Can we just launch the process and let it run or does the manager needs to 
    # do something specific to track them??
if __name__ == "__main__":
    sys.exit(main())
