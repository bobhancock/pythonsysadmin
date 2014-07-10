"""
SQLlite interface for URLs to be downloaded

Table structure
TBD
"""
import pdb
import os
from datetime import datetime

from pysqlite2 import dbapi2 as sqlite

class RetrievalList():
    def __init__(self, filename, tablename):
        self.file_name = filename + '.sqlite' # the physical disk file = database name
        self.table_name = tablename	# table name
        self.conn = None
        self.cursor = None

    def connect(self):
        """ Connect to sqlite table. """
        try:
            self.conn = sqlite.connect(self.file_name)
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise e

    def disconnect(self):
        try:
            self.conn.close()
        except Exception as e:
            rt = e
            raise e

    def create_table(self):
        """ Create a sqlite table. """
        try:
            sql_tuple = (self.table_name, )
            table_create_str = """create table %s (url text, descriptin text,
            username text, password text)""" % self.table_name
            self.cursor.execute(table_create_str)

            unique_index_str = """create unique index url on %s 
            (url)""" % self.table_name
            self.cursor.execute(unique_index_str)
        except Exception as e:
            raise e

    def insert_row(self, url, description, username='', password=''):
        """ Add row to database. """
        try:
            # use tuple to prevent SQL injection attack '''
            sql_tuple =  (url, description, username, password)
            insert_str = "insert into %s values (?,?,?,?)" % self.table_name

            self.cursor.execute(insert_str , sql_tuple)
            self.conn.commit()
        except Exception as e:
            raise e
    
    def delete_row(self, key):
        pass
    
    def max_records():
        """ Return number of records in table. """
        pass
    
    def retrieve_range(start, end):
        """ Retrieva a range of records with a scan. """
        pass
    
    