""" LDAP configured connection client for RatingsXpress. """
import sys
import time
import datetime
import atexit
import collections
import copy
import ldap
import ldif
import multiprocessing
import threading
import Queue
from StringIO import StringIO
from ldap.cidict import cidict
from dry import lst

__author__ = ('hancock.robert@gmail.com (Robert Hancock)')
__version__ = "1.4"

# Constants
# LDAP is inconsistent as to which terms are case sensitive.  These strings work with
# OpendLDAP and the Sun implementation.
_organizationalPerson = "organizationalPerson"
_posixGroup = "posixGroup"
_posixAccount = "posixAccount"
_uidNumber = "uidNumber"
_gidNumber = "gidNumber"
_memberUid = "memberUid"
_uid = "uid"
_add = "add"
_remove = "remove"
_userPassword = "userPassword"
_homeDirectory = "homeDirectory"
_description = "gecos"
_cn = "cn"

class LDAPSearchResult:
    """A class to abstract LDAP results.
    """
    dn = ''
    
    def __init__(self, entry_tuple):
        """Create a new LDAPSearchResult object."""
        (dn, attrs) = entry_tuple
        if dn:
            self.dn = dn
        else:
            return
    
        self.attrs = cidict(attrs)
    
    def get_attributes(self):
        """Get a dictionary of all attributes.
        get_attributes()->{'name1':['value1','value2',...], 
        'name2: [value1...]}
        """
        return self.attrs
    
    def set_attributes(self, attr_dict):
        """Set the list of attributes for this record.
        
        The format of the dictionary should be string key, list of
        string alues. e.g. {'cn': ['M Butcher','Matt Butcher']}
        
        set_attributes(attr_dictionary)
        """
    
        self.attrs = cidict(attr_dict)
    
    def has_attribute(self, attr_name):
        """Returns true if there is an attribute by this name in the
        record.
        
        has_attribute(string attr_name)->boolean
        """
        return self.attrs.has_key( attr_name )
    
    def get_attr_values(self, key):
        """Get a list of attribute values.
        get_attr_values(string key)->['value1','value2']
        """
        return self.attrs[key]
    
    def get_attr_names(self):
        """Get a list of attribute names.
        get_attr_names()->['name1','name2',...]
        """
        return self.attrs.keys()
    
    def get_dn(self):
        """Get the DN string for the record.
        get_dn()->string dn
        """
        return self.dn
    
    def pretty_print(self):
        """Create a nice string representation of this object.
        
        pretty_print()->string
        """
        str = "DN: " + self.dn + "n"
        for a, v_list in self.attrs.iteritems():
            str = str + "Name: " + a + "n"
            
        for v in v_list:
            str = str + "  Value: " + v + "n"
            str = str + "========"
            
        return str
    
    def to_ldif(self):
        """Get an LDIF representation of this record.
        
        to_ldif()->string
        """
        out = StringIO()
        ldif_out = ldif.LDIFWriter(out)
        ldif_out.unparse(self.dn, self.attrs)
        return out.getvalue()      

   
class ConfiguredConnection():
    """
    A configured LDAP connection
    
    """
    def __init__(self, 
                 server,
                 admin_dn, 
                 admin_password, 
                 root_dn,
                 groups_dn, 
                 users_dn,
                 default_homedir, 
                 default_gid='710',
                 threads=4):
        
        self.server = server
        self.admin_dn = admin_dn
        self.admin_password = admin_password
        self.root_dn = root_dn
        self.groups_dn = groups_dn
        self.users_dn = users_dn
        self.default_homedir = default_homedir
        self.default_gid = str(default_gid)
        self.thread_count = threads
        self.GROUPS = []
        
        try:
            self.con = self._init(server)
        except Exception as e:
            raise e
        
        try:
            self.con.bind(admin_dn, admin_password)
        except Exception as e:
            raise e
        
        self._cache_groups()
                 
    def _init(self, server):
        return ldap.initialize(server)

    def _bind(self, bind_dn, pw):
        self.con.bind(bind_dn, pw, ldap.AUTH_SIMPLE)
        
    def unbind(self):
        self.con.unbind()
        
    def version(self):
        return __version__
    
    def _get_search_results(self, results):
        """
        Reduces ldap search results to a list.
        
        args:    a set of ldap results.
        return:  a list of LDAPSearchResult objects
        """
        res = []
        
        if type(results) == tuple and len(results) == 2 :
            (code, arr) = results
        elif type(results) == list:
            arr = results
        
        if len(results) == 0:
            return res
        
        for item in arr:
            res.append( LDAPSearchResult(item) )
        
        return res 
            
    def _is_entry(self,  base_dn, name, objectclass):
        """ cn is used as the attribute to identify both user names and group names.
        
        args:  
           base_dn - the root for which to start searching
           name    - username
           objectclass
        
                
        return: 
           True if username exists, otherwise false.
        """
            
        filt = '(objectclass={c})'.format(c=objectclass)
        attrs = ['cn']
        try:
            results = self.con.search_s(base_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        except ldap.NO_SUCH_OBJECT:
            return False
        except Exception as e:
            raise e
    
        result_objs = self._get_search_results(results)
        
        for obj in result_objs:
            if "cn" in obj.get_attr_names():
                atr = obj.get_attr_values('cn')
                if name in obj.get_attr_values('cn'):
                    return True
                
        return False
    
    def is_user(self, name):
        """
        args:
            name - username
            
        return:
            True if user exists, else False
        """
        try:
            retval = self._is_entry(self.users_dn, name, _organizationalPerson)
        except ldap.NO_SUCH_OBJECT:
            retval = False
            
        return retval

    def is_group(self, name):
        try:
            retval = self._is_entry(self.groups_dn, name, _posixGroup)
        except ldap.NO_SUCH_OBJECT:
            retval = False
            
        return retval
    
    def _unique_number(self, objclass, attribute):
        """ Return a unique number for the given attribute.
        
        Return   1 unable to obtain any numbers from ldap

        Exception
           If search fails raise exception
        """
        #(cn=*)\" number
        filt = '(objectclass={c})'.format(c=objclass)
        attrs = [attribute]
        numbers = []
        numbers_l = []

        try:
            results = self.con.search_s(self.root_dn, 
                                        ldap.SCOPE_SUBTREE, 
                                        filt, 
                                        attrs )
        except Exception as e:
            raise e
    
        result_objs = self._get_search_results(results)
        
        for obj in result_objs:
            if attribute in obj.get_attr_names():
                numbers_l.append(obj.get_attr_values(attribute))
        
        maxval = 0
        for num in lst.flatten(numbers_l):
            num = int(num)
            if num > maxval:
                maxval = num
           
        return maxval + 1
        
    def unique_uidnumber(self):
        """ Return a uidnumber that is unique within this connection. """
        return self._unique_number(_organizationalPerson, _uidNumber)
    
    def unique_gidnumber(self):
        """ Return a gidnumber that is unique within this connection. """
        return self._unique_number(_posixGroup, _gidNumber)
    
    def _is_number(self, numb, attribute, objectclass):
        """ Is the value a number representation: True or False. """
        filt = '(objectclass={oc})'.format(oc=objectclass)
        attrs = [attribute]
        numbers_l = []
        numbers = []
        results = self.con.search_s( self.users_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        res = self._get_search_results(results)
        
        for item in res:
            if item.has_attribute(attribute):
                numbers_l.append(item.get_attr_values(attribute))
                
        fnumbers = lst.flatten(numbers_l)
        for num in fnumbers:
            if numb == int(num):
                return True
            
        return False
        
    def is_uidnumber(self, uidnumber):
        return self._is_number(uidnumber, _uidNumber, _posixAccount)
        
    def is_gidnumber(self, gidnumber):
        return self._is_number(gidnumber, _gidNumber, _posixAccount)
    
    def is_uid(self, uidval):
        """ Does this uid exist? True or False. """
        filt = '(objectclass=organizationalPerson)'
        attrs = []
        uids_l = []
        results = self.con.search_s( self.users_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        res = self._get_search_results(results)
        
        for item in res:
            if item.has_attribute(_uid):
                uids_l.append(item.get_attr_values(_uid))
                
        fuids = lst.flatten(uids_l)
        for uid in fuids:
            if uidval == uid:
                return True
            
        return False
         
        
    def add_user(self, username, 
                 password, 
                 homedir=None, 
                 uidnumber=None,
                 gidnumber=None,
                 description=None):
        """
        args:
           username - unique username
           password - strong passwrd
           home_directory - if None, then default is used.
           uidnumber - if not supplied a unique value is given
           attributes - if supplied, is a dictionary dict[attr_name] = [attr_values]
        
        return:
           True or raises exception
        """
        if not homedir:
            homedir = self.default_homedir
        
        if not uidnumber or self.is_uidnumber(uidnumber):
            uidnumb = str(self.unique_uidnumber())
        else:
            uidnumb = str(uidnumber)
            
        if not description:
            gecos = 'Not specified'
        else:
            gecos=description
            
        if not gidnumber:
            gidnumber = self.default_gid
        else:
            if not type(gidnumber) == str:
                try:
                    gidnumber = str(gidnumber)
                except Exception as e:
                    gidnumber = self.default_gid
            
        add_record = [
            ('ou', ['RatingsXpress']), 
            ('uid', [username]),
            ("gidNumber", [gidnumber]), 
            ('givenName', [username]),
            ('sn', [username]),
            ('cn', [username]),
            ('userPassword', [password]),
            ('homeDirectory', [homedir]),
            ('uidnumber', [uidnumb]),
            ("loginShell", ["/sbin/noshell"]),
            ("gecos", [gecos]),
            ("objectClass", ['top', 
                             "person", 
                             "organizationalPerson",
                             "inetorgperson", "posixAccount"])
        ]
        
        user_dn = "uid={u},{udn}".format(u=username, udn=self.users_dn)
            
        try:
            self.con.add_s(user_dn, add_record)
        except Exception as e:
            raise e
                
        return True
    
    def get_user_description_as_dict(self):
        """ Return dict[username] = description """
        user_description = {}
        connections = []
        threads = []
        q_user = Queue.Queue()
        q_user_description = Queue.Queue()
         
        # Load users queue
        users = self.get_all_usernames()
        for username in users:
            q_user.put(username)
        for n in range(self.thread_count):
            q_user.put(None) #sentinels   
            
        for i in range(self.thread_count): 
            connection = ConfiguredConnection(self.server,
                                              self.admin_dn, 
                                              self.admin_password, 
                                              self.root_dn, 
                                              self.groups_dn, 
                                              self.users_dn,
                                              self.default_homedir,
                                              threads=1)
            connections.append(connection)
            t = threading.Thread(target=self._get_user_description_worker, 
                                 args=(username, q_user, q_user_description, connection.con))
            t.daemon = True
            threads.append(t)
            t.start()
            
            
        for th in threads:
            th.join()
            
        for con in connections:
            con.unbind()            

        while not q_user_description.empty():
            username, description = q_user_description.get()
            user_description[username] = description
            
        return user_description
        
    
    def _get_user_description_worker(self, username, q_user, q_user_description, connection=None):
        """
        Get the description for the users.
        """
        attrs = ["gecos"]
        
        while True:
            username = q_user.get()
            if username == None:
                q_user.task_done()
                break
            
            filt = '(cn={u})'.format(u=username)
        
            results = self.con.search_s(self.users_dn, ldap.SCOPE_SUBTREE, filt, attrs)
            res = self._get_search_results(results)
        
            # The attributes are returned as lists, but in this case each attribute can
            # have only one value.
            user = res[0]
            if user.has_attribute('gecos'):
                gecos = (user.get_attr_values('gecos'))[0]
            else:
                gecos = "Not found"
                
            q_user_description.put( (username, gecos) )
            q_user.task_done()

            
    def get_user_groups_as_dict(self):
        """ Return a dictionary of dict[username] = (group, ...) """
        user_groups = {}
        users = self.get_all_usernames()
        groups_members = self.get_groups_members_as_dict()
        for user in users:
            user_groups[user] = []
            for group, members in groups_members.iteritems():
                if user in members:
                    user_groups[user].append(group)
                    
        return user_groups

    def get_groups_members_as_dict(self):
        """ Return a dictionary of dict[group] = (memberuid, ...)
        
        """
        group_members = {}
        for group in self.GROUPS:
            members = self.get_group_members(group) # returns tuple
            group_members[group] = members
            
        return group_members
            
            
    def get_user_groups(self, username):
        """ Return a list of all groups in which this user is a member.
        We always refer to the cache first.  
        
        args:
            username - the username that maps to uid
            
        return:
            list of groups in which this user is a member
        """
        if not self.is_user(username):
            return None
            
        filt = '(objectclass=posixGroup)'
        groups_l = [] # list of groups
        groups = []
        attrs = []
        user_groups = []
        q_groups = Queue.Queue()
        q_user_groups = Queue.Queue()
         
        #print('{tm} Start get_user_groups'.format(tm= datetime.datetime.today().strftime("%a, %d %b %Y %H:%M:%S +0000")))
        a = time.time()
            
        # Load the groups queue.
        for group in self.GROUPS:
            q_groups.put(group)
        for n in range(self.thread_count):
            q_groups.put(None) #sentinels
            
        # Get memberuids of groups and if username is a member, the
        # group is placed on q_user_groups.
        threads = []
        connections = []
        for i in range(self.thread_count): 
            connection = ConfiguredConnection(self.server,
                                              self.admin_dn, 
                                              self.admin_password, 
                                              self.root_dn, 
                                              self.groups_dn, 
                                              self.users_dn,
                                              self.default_homedir,
                                              threads=1)
            connections.append(connection)
            t = threading.Thread(target=self._get_user_groups_worker, 
                                 args=(username, q_groups, q_user_groups, connection.con))
            t.daemon = True
            threads.append(t)
            t.start()
            
        #q_groups.join()        
        for th in threads:
            th.join()

        while not q_user_groups.empty():
            user_groups.append(q_user_groups.get())
            
        for con in connections:
            con.unbind()

        #q_user_groups.join()
        #print('{tm} Stop get_user_groups'.format(tm= datetime.datetime.today().strftime("%a, %d %b %Y %H:%M:%S +0000")))            
        #print("Get user groups: {et}".format(et= time.time() -a))
        return user_groups
    
    
    def _get_user_groups_worker(self, username, q_groups, q_user_groups, connection=None):
        """
        Get the memberuids for the group and if the username is a
        member, place the group name on q_user_groups.
        """
        while True:
            group = q_groups.get()
            if group == None:
                q_groups.task_done()
                break
            
            # Returning the memberuids as keys of a dictionary
            # means the lookup is always O(1).  If returned as a
            # tuple then the membership test is O(n).
            memberuids = self.get_groups_members_as_hash(group, connection)
            if username in memberuids:
                q_user_groups.put(group)
            q_groups.task_done()
            
                   
    def get_group_members(self, group, connection=None):
        """ 
        args:    group - group name
                 
        return:  tuple of group memberuids
        
        It first checks the cache and only queries ldap if the group is not found.
        """
        return tuple(self.get_users_in_group(group, connection))
    
    def get_groups_members_as_hash(self, group, connection=None):
        """
        Return the memberuids of the group as a hash table. i.e,, keys of a 
        dictionary.
        
        args:
           connection allows you to pass an alternate connection object from
           that used by default at the class level.
        """
        tup = self.get_group_members(group, connection)
        return dict((m, True) for m in tup)
        
        
    def _cache_groups(self):
        """ Get all the groups for this DN and write them to  self.GROUPS
        """
        filt = '(objectclass=posixGroup)'
        attrs = []
        
        results = self.con.search_s( self.groups_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        res = self._get_search_results(results)
            
        # Put list of all groups into cache
        for item in res:
            if item.has_attribute(_cn):
                g_attr = item.get_attr_values(_cn)
                # g_attr is a list and should normmaly contain only one element
                if len(g_attr) > 1:
                    fgroups = lst.flatten(g_attr)
                    for group in fgroups:
                        self.GROUPS.append(group)
                else:
                    self.GROUPS.append(g_attr[0])
         
    def get_all_groups(self):
        """ Return a list of all groups. """
        return(self.GROUPS)
    
    def get_all_usernames(self):
        """
        Get all usernames in this branch.
        Return 
            dict[memberuid] = ""
        """
        #filt = 'cn={g}'.format(g=ouname)
        #filt = 'cn=*'
        filt = 'uid=*'
        attrs = []
        
        users_l = []
        users = {}
        
        results = self.con.search_s(self.users_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        res = self._get_search_results(results)
        
        for group in res:
            if group.has_attribute('uid'):
                users_l.append(group.get_attr_values('uid'))
                
        fusers = lst.flatten(users_l)
        for memberuid in fusers:
            if memberuid not in users:
                users[memberuid] = ""
                
        return users
    
    def get_user_profile(self, username):
        """
        For username, return the tuple:
           (gecos, homedir, uidnumber, gidnumber, user_password)
        """
        global _homeDirectory,_uidNumber, _gidNumber
        
        if not self.is_user(username):
            return None
        
        filt = '(cn={u})'.format(u=username)
        attrs = ["*"]
        
        results = self.con.search_s(self.users_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        res = self._get_search_results(results)
        
        # The attributes are returned as lists, but in this case each attribute can
        # have only one value.
        user = res[0]
        if user.has_attribute('gecos'):
            gecos = (user.get_attr_values('gecos'))[0]
        else:
            gecos = None
            
        if user.has_attribute(_homeDirectory):
            homedir = (user.get_attr_values(_homeDirectory))[0]
        else:
            homedir = None
            
        if user.has_attribute(_uidNumber):
            uidnumber = (user.get_attr_values(_uidNumber))[0]
        else:
            uidnumber = None
            
        if user.has_attribute(_gidNumber):
            gidnumber = (user.get_attr_values(_gidNumber))[0]
        else:
            gidnumber = None

        if user.has_attribute(_userPassword):
            user_password = (user.get_attr_values(_userPassword))[0]
        else:
            user_password = None
            
        return (gecos, homedir, uidnumber, gidnumber, user_password)
            
                
    def get_users_in_group (self, groupname, connection=None):
        """
        args - groupname, not the dn
        
        returns
           #list of users in group
           dictionary with key of memberuid
        """
        if not self.is_group(groupname):
            raise ldap.NO_SUCH_OBJECT(groupname)
    
        #group_dn = "cn={g},{dn}".format(g=groupname, dn=self.groups_dn)
        filt = '(objectclass=posixGroup)'
        filt = 'cn={g}'.format(g=groupname)
        attrs = []
        
        users_l = []
        users = {}
        
        # This line is the bottle neck when threaded.
        if connection:
            results = connection.search_s(self.groups_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        else:
            results = self.con.search_s(self.groups_dn, ldap.SCOPE_SUBTREE, filt, attrs )
        res = self._get_search_results(results)
        
        for group in res:
            if group.has_attribute('memberUid'):
                users_l.append(group.get_attr_values('memberUid'))
                
        fusers = lst.flatten(users_l)
        for memberuid in fusers:
            # When users is a list membership test is O(n).  As keys in a 
            # dictionary, it is O(1).
            if memberuid not in users:
                users[memberuid] = ""
                
        return users
    
        
    def add_group(self, groupname, description=None, gidnumber=None):
        """
        Add a posix group which is an entitlement in RX terms.
        
        args
           groupname - the entitlement name, i.e, rxmgin
           description - Explanatory text
        """
        # Does the group name exist: cn=groupname?
        if self.is_group(groupname):
            raise ldap.ALREADY_EXISTS(groupname)
        
        if not description:
            description = 'Not specified'
        
        if not gidnumber:
            gidnumber = str(self.unique_gidnumber())
        
        add_record = [
            ("gidNumber", [gidnumber]), 
            ('cn', [groupname]),
            ("description", [description]),
            ("objectClass", ['top', 
                             "posixGroup"])]
        
        group_dn = "cn={u},{udn}".format(u=groupname, udn=self.groups_dn)
            
        try:
            self.con.add_s(group_dn, add_record)
        except Exception as e:
            raise e

        if groupname not in self.GROUPS:
            self.GROUPS.append(groupname)
        
        return True
    
    
    def add_user_to_group(self, username, groupname):
        return self._add_remove_user_in_group(username, groupname, _add)
        
        
    def remove_user_from_group(self, username, groupname):
        return self._add_remove_user_in_group(username, groupname, _remove)
        
    
    def _add_remove_user_in_group(self, username, groupname, action):
        """
        Add to or remove user from group.
        
        args
           username - the actual name, not the dn
           groupname - the actual name, not the dn
           action - "add" or "remove"
           
        returns
           True or raises exception
           
        """
        if not self.is_group(groupname):
            raise ldap.NO_SUCH_OBJECT(groupname)

        # This returns a dictionary where the keys are the members of the group
        # and the value is "".  This allows a lookup of O(1) instead of O(n).
        base_users_in_group = self.get_users_in_group(groupname) # dict
        post_users_in_group = base_users_in_group.keys() # groups after operations applied

        # On add, no need to raise exception is user is already a member
        #users_in_group.append(username)
        if action.lower() == _add:
            if username in base_users_in_group:
                return True
            else:
                post_users_in_group.append(username)
        elif action.lower() == _remove:
            if username in base_users_in_group:
                post_users_in_group.remove(username)
        else:
            raise ldap.OPERATIONS_ERROR("Illegal action {a]".format(a=action))

        # If no change in membership, return True
        if frozenset(base_users_in_group.keys()) == frozenset(post_users_in_group):
            return True
        
        # Overwrite entire memberUid list
        mod_attrs = [ (ldap.MOD_REPLACE, _memberUid, post_users_in_group) ]
        group_dn = "cn={g},{dn}".format(g=groupname, dn=self.groups_dn)
        try:
            self.con.modify_s(group_dn, mod_attrs)
        except Exception as e:
            raise ldap.OPERATIONS_ERROR(e)

        return True                     
    
    def delete_user(self, username):
        """ Delete the user from all groups and then delete the user entry. """
        if not self.is_user(username):
            raise ldap.NO_SUCH_OBJECT(username)
        
        user_groups = self.get_user_groups(username)
        
        for group in user_groups:
            try:
                self.remove_user_from_group(username, group)
            except Exception as e:
                raise e
            
        user_dn = "uid={u},{udn}".format(u=username, udn=self.users_dn)
            
        try:
            self.con.delete_s(user_dn)
        except Exception as e:
            raise e
                
        return True
    
    def delete_group(self, groupname):
        """ Delete all the users in group first and then delete the group entry. """
        if not self.is_group(groupname):
            raise ldap.NO_SUCH_OBJECT
        
        group_dn = "cn={u},{udn}".format(u=groupname, udn=self.groups_dn)
            
        try:
            self.con.delete_s(group_dn)
        except Exception as e:
            raise e

        if groupname in self.GROUPS:
            self.GROUPS.remove(groupname)
            
        return True

    
    def modify_password(self, username, password):
        """
        args
           username - the target username
           password - the new password
           
        return
           True if it succeeded, otherwise raises an exception
        """
        if not self.is_user(username):
            raise ldap.NO_SUCH_OBJECT(username)
        
        modlist = [(ldap.MOD_REPLACE, _userPassword, password)]
        dn = user_dn = "uid={u},{udn}".format(u=username, udn=self.users_dn)
        
        try:
            self.con.modify_s(dn, modlist)
        except Exception as e:
            raise e
        
        return True

    
    def modify_homedir(self, username, homedir):
        """
        args
           homedir - the target homedir
           password - the new password
           
        return
           True if it succeeded, otherwis is raises and exception
        """        
        modlist = [(ldap.MOD_REPLACE, _homeDirectory, homedir)]
        dn = user_dn = "uid={u},{udn}".format(u=username, udn=self.users_dn)
        
        try:
            self.con.modify_s(dn, modlist)
        except Exception as e:
            raise e
        
        return True
    
    def modify_description(self, username, description):
        """
        args
           description - the target description
           password - the new password
           
        return
           True if it succeeded, otherwis is raises and exception
        """        
        modlist = [(ldap.MOD_REPLACE, _description, description)]
        dn = user_dn = "uid={u},{udn}".format(u=username, udn=self.users_dn)
        
        try:
            self.con.modify_s(dn, modlist)
        except Exception as e:
            raise e
        
        return True        
  
