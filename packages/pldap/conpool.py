""" Connection pool of configured ldap connections. """
import con
import Queue

class Pool():
    self._connection_queue = Queue.queue()
    self._state = RUN
    
    def __init__(self, connections=4,
                 server,
                 admin_dn, admin_password, 
                 root_dn, groups_dn, users_dn,
                 default_homedir, default_gid='710')

    self._pool = []
    if connections is None:
        try:
            connections = cpu_count()
        except NotImplementedError:
            connections = 1
            
    self._setup_queue()
    
    
    def _setup_queue(self):
        for i in range(connections):
            connection = con.ConfiguredConnection(server,
                                              admin_dn,
                                              admin_pwd,  
                                              root_dn,
                                              groups_dn,
                                              users_dn,
                                              homedir)
            po = PoolObject(connection, str(i), True)
            self._pool.append(po)
            self._connection_queue.put(po)
    
            
    def get_connection(self):
        """ Return a connection object if available, else None. 
        """
        try:
            po = self.self._connection_queue.get()
        except Queue.Empty:
            return None
    
        return c
         
    
    def release_connection(self,):
        """ Release a connection back into the pool."""
        
        
    @classmethod            
    def _terminate_pool(self):
        """ unbind every connection in pool. """
        pass
    
    
class PoolObject():
    def __init__(self, connection, name, available):
        self.connection = connection
        self.name = name
        self.available = available

        if not isinstance(self.connection, con.ConfiguredConnection):
            raise TypeError('connection must be of type ConfiguredConnection')
        
        if not isinstance(self.available, bool):
            raise TypeError('state must be a bool')
        
        
        
        
        