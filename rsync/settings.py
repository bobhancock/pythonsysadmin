""" Settings for rsync to archive.
Files in remote_root are synced to local root.
"""
import os
import sys
import collections
# Perform an rsync dry run where you log the events but do not
# actually transfer the files.
DRY_RUN = False

# The lock file acts as a sempahore to tell the program that there is
# already an rsync in process.  If there was failure, you will want
# to set this to true before the next invocation.
DELETE_LOCKFILE = False

# Debug logging
DEBUG = False

# Compress any files older than this.
AGING_DAYS_FOR_COMPRESSION=90

SSH_PORT = 22
LOG_FILE = 'rsync.log'
RSYNC_STDOUT = 'rsync_stdout.log' # file for stdout
RSYNC_STDERR =  'rsync_stderr.log' # file for stderr
LOCK_FILE = 'rsync.lock'
RSYNC_BIN = '/usr/bin/rsync'



# Named tuple that holds the configuration information for each product.
# name = unique identifier (e.g., ratings, research, etc)
# username = the username used to log into the remote system
# password = the password for an ssh connection
# remote_root = the remote directory from which to start the rsync
# local_root - the local directory to where the files are synced
ProductConf = collections.namedtuple('ProductConf',
                                      '''name, 
                                      username, 
                                      password,
                                      remote_root,
                                      local_root, 
                                      exclude_dirs_file''')
product_confs = []

# Each product will have its own process directory under the application
# directory with the same file names.
REMOTE_HOST='nj09mhf5006.edmz.mycompay.com'    
PACKAGE_PATH = '/net/151.108.224.74/fgr_arch/rx_archive/apps/pypackages'
base_dir = '/net/151.108.224.74/fgr_arch/rx_archive'
APPLICATION_DIR = os.path.join(base_dir, 'apps/rx_rsync')

product_confs.append(ProductConf._make(
    ['ratings', 
    'bob', 
    'w1lHelm!k3mPff',
    '/raid/ftp/eris_ftp/eris_output/RX20',
    os.path.join(base_dir, 'raid/ftp/eris_ftp/eris_output/RX20'),
    os.path.join(APPLICATION_DIR, 'ex_dirs')]))

## RatingsResearch
product_confs.append(ProductConf._make(
    ['researchratings',
     'bob',
     'adp',
     '/raid/ftp/adp_ftp/rxcr/ratings/',
     os.path.join(base_dir, 'raid/ftp/adp_ftp/rxcr/ratings'),
     os.path.join(APPLICATION_DIR, 'ex_dirs')]))

product_confs.append(ProductConf._make(
    ['researchresearch',
     'bob',
     'adp',
     '/raid/ftp/adp_ftp/rxcr/research/',
     os.path.join(base_dir, 'raid/ftp/adp_ftp/rxcr/research'),
     os.path.join(APPLICATION_DIR, 'ex_dirs')]))

if not os.path.isdir(APPLICATION_DIR):
    sys.stderr.write('Cannot find {appdir}'.format(appdir=APPLICATION_DIR))
    sys.exit(1)

