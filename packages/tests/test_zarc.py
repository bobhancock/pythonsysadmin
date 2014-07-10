import unittest
import sys
import os
import iw.mock
sys.path.insert(0, os.path.dirname(iw.mock.__file__))
from iw.mock import ldap
reload(ldap)
import ldap

from ldif import LDIFParser, LDIFWriter

import settings
sys.path.insert(0, settings.PACKAGE_PATH)
import pldap.con
import dry.logger


def con():
    try:
        con = pldap.con.ConfiguredConnection(settings.server,
                                             settings.admin_dn,
                                             settings.admin_pwd,  
                                             settings.root_dn,
                                             settings.groups_dn,
                                             settings.users_dn,
                                             settings.homedir)
    except Exception as e:
        sys.stderr.write(e)
        return None

    return con

def log():
    return dry.logger.setup_log_size_rotating(settings.log_file,
                                              debug=True)

def setup():
    return con(), log()



#skip_dn = ["uid=foo,ou=People,dc=example,dc=com",
    #"uid=bar,ou=People,dc=example,dc=com"]
#skip_dn = []

#class MyLDIF(LDIFParser):
    #def __init__(self, input, output):
        #LDIFParser.__init__(self, input)
        #self.writer = LDIFWriter(output)

    #def handle(self, dn, entry):
        #for i in skip_dn:
            #if i == dn: 
                #return

        #if "RatingsXpress3" in dn:
            #self.writer.unparse(dn, entry)

ldif_file = "/var/tmp/update/20101115_5003.ldif"
if not os.path.isfile(ldif_file):
    print ldif_file+" does not exist!"
    sys.exit()

parser = MyLDIF(open(ldif_file, 'rb'), sys.stdout)
parser.parse()