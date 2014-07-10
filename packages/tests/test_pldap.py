""" Functional tests for pldap. """
import pdb
import unittest
import sys
import os
import datetime
#import iw.mock
#sys.path.insert(0, os.path.dirname(iw.mock.__file__))
sys.path.insert(0, '/local/src/pypackages')
#from iw.mock import ldap
#reload(ldap)
import ldap
import time
import pldap.con
    
from ldif import LDIFParser, LDIFWriter

#skip_dn = ["uid=foo,ou=People,dc=example,dc=com",
   #"uid=bar,ou=People,dc=example,dc=com"]
skip_dn = []

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

#ldif_file = "/var/tmp/update/20101115_5003.ldif"
#if not os.path.isfile(ldif_file):
   #print ldif_file+" does not exist!"
   #sys.exit()
   
#parser = MyLDIF(open(ldif_file, 'rb'), sys.stdout)
#parser.parse()
# Ubuntu settings
server = "ldap://localhost:389"
root_dn="dc=example,dc=com"
admin_dn = "cn=admin,{r}".format(r=root_dn)
admin_pwd="secret"
groups_dn = "ou=groups,{r}".format(r=root_dn)
users_dn = "ou=people,{r}".format(r=root_dn)
homedir = "/raid/ftp/eris_ftp/eris_output/RX30"

 #Sun settings
#server = "ldap://ny01mhf5026.mhf.mhc:22389"
#root_dn="ou=ftp,dc=fissp,dc=com"
#admin_dn = "uid=ftpadmin,{r}".format(r=root_dn)
#admin_pwd="bzqx27fvr"
#groups_dn = "ou=RatingsXpress,ou=ftpgroups,{r}".format(r=root_dn)
#users_dn = "ou=RatingsXpress3,ou=ftpusers,{r}".format(r=root_dn)
#homedir = "/raid/ftp/eris_ftp/eris_output/RX30"

max_users = 10
max_groups = 16

def erase():
    pass

def init():
    pass

def add_groups(con):
    for i in range(1,max_groups):
        groupname = "group_"+str(i)
        desc = groupname
        con.add_group(groupname, description=desc, gidnumber=None)

def delete_groups(con):
    for g in con.GROUPS:
        try:
            con.delete_group(g)
        except Exception:
            pass

def add_users(con):
    for i in range(1, max_users):
        con.add_user("user"+str(i), 
                     "secret")
        
def delete_users(con):
    users = con.get_all_usernames()
    for u in users:
        try:
            con.delete_user(u)
        except Exception:
            pass
        print('Deleted user {u}'.format(u=u))

def add_users_to_groups(con):
    for g in con.GROUPS:
        for i in range(1, max_users):
            con.add_user_to_group("user"+str(i), g)
            
def get_users_groups(con):
    for i in range(1, max_users):
        groups = con.get_user_groups("user"+str(i))
    
def main():
    con = pldap.con.ConfiguredConnection(server,
                                     admin_dn,
                                     admin_pwd,  
                                     root_dn,
                                     groups_dn,
                                     users_dn,
                                     homedir)
                                     
    a = time.time()
    #add_groups(con)
    #print("Added groups")
    #add_users(con)
    #print("Added users")
    #add_users_to_groups(con)
    #print("Added users to groups")
    get_users_groups(con)
    print("Got users in groups")
    
    #delete_users(con)
    #print("Deleted users")
    #delete_groups(con)
    #print("Deleted groups")
    
    groups = con.get_all_groups()
    groups.sort()
    print groups
    con.unbind()
    print("Elasped time: {et}".format(et=time.time() - a))
    
if __name__ == "__main__":
    sys.exit(main())
    