# This is the configuration file for an aggregator instance.
#
# log_file - The audit log.
# proxy = The proxy URL or host name.  If blank, the aggregator assume
#          that no proxy is required and attempts to directly access the web sites.
# cache_dir = The directory where raw XML filses are written and kept as a cache
# proxy_username = Username to authenticate at proxy.
# proxy_password = Password to authenticat at proxy.
# deffered_groups = Number of simultaneous connections.
# inter_query_time = In seconds, for cache expiration.
# timetout = In seconds, the time to wait for a website to finish downloading.
appconf = {
    'log_file':'/local/apps/rd_rss_feed/log/aggregator.log',
    'proxy': 'corp-55w-proxy.mhc',
    'proxy_username': 'bob_hancock',
    'proxy_password': 'S1rgu3y!',
    'cache_dir': '/local/data/rss',
    'deferred_groups': 60,
    'inter_query_time': 240,
    'timeout': 30
    }