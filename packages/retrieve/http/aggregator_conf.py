""" Aggregator configuration. 
These are the settings that apply to all aggregators forked
by the aggregator manager.
"""
import os
from ConfigParser import SafeConfigParser

class Appconf:
    """ Class representation of configuration file."""
    def __init__(self, filenameConfig):
        self.appconf = {}

        try:
            self.filenameConfig = filenameConfig
            self.config = SafeConfigParser()
            self.config.read(self.filenameConfig)

            self.appconf['inter_query_time'] = self.config.get('aggregator', "inter_query_time")
            self.appconf['timeout'] = self.config.get('aggregator', "timeout")
            self.appconf['deferred_groups_max'] = self.config.get('aggregator', "deferred_groups_max")
            self.appconf['download_dir'] = self.config.get('aggregator', "download_dir")
            self.appconf['sync_dir'] = self.config.get('aggregator', "sync_dir")
            
            self.appconf['use_proxy'] = self.config.get('proxy', "use_proxy")
            self.appconf['proxy_host'] = self.config.get('proxy', "proxy_host")
            self.appconf['proxy_username'] = self.config.get('proxy', "proxy_username")
            self.appconf['proxy_password'] = self.config.get('proxy', "proxy_password")
            
            self.appconf['daemon_log'] = self.config.get('daemon', "daemon_log")
            self.appconf['daemon_error_log'] = self.config.get('daemon', "daemon_error_log")
            self.appconf['daemon_pid'] = self.config.get('daemon', "daemon_pid")

        except Exception as e:
            raise e

    def verify_appconf(self):
        """ Verify values in appconf. """
        appconf_error = {}
        
        key = 'inter_query_time'
        i = self.appconf[key]
        try:
            int(i)
        except ValueError:
            appconf_error[key] = 'invalid literal for int() with base 10: %s' % i
    
        key = 'timeout'
        i = self.appconf[key]
        try:
            int(i)
        except ValueError:
            appconf_error[key] = 'invalid literal for int() with base 10: %s' % i

        key = 'deferred_groups_max'
        i = self.appconf[key]
        try:
            int(i)
        except ValueError:
            appconf_error[key] = 'invalid literal for int() with base 10: %s' % i

        key = "download_dir"
        directory = self.appconf[key]
        if not os.path.isdir(directory):
            appconf_error[key] = ('Cannot find directory %s' % directory)

        key = "sync_dir"
        directory = self.appconf[key]
        if not os.path.isdir(directory):
            appconf_error[key] = ('Cannot find directory %s' % directory)

        key = 'use_proxy'
        if (self.appconf[key]).lower() != 'true' and (self.appconf[key]).lower() != "false":
            appconf_error[key] = 'Must be either True or False'
        else:
            if (self.appconf[key]).lower() == 'true':
                self.appconf[key] = True
            else:
                (self.appconf[key]) = False
    
        return appconf_error