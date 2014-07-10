import os
import sys
# Path to packages
PACKAGE_PATH="/usr/local/src/python/pythonforsysadmins/packages"
if not os.path.isdir(PACKAGE_PATH):
    sys.stderr.write('settings.PACKAGE_PATH {dr} cannot be found.'.format(
        dr = PACKAGE_PATH))
    sys.exit(1)    
    
logdir = os.path.join(os.path.dirname(__file__), "log")
if not os.path.isdir(logdir):
    os.mkdir(logdir)

# Activate debug logging.
DEBUG = True
DRY_RUN = True


