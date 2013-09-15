"""filedict.py
a Persistent Dictionary in Python
 
Author: Erez Shinan
Date  : 31-May-2009
"""

try:
    import simplejson as json ## jlv replaced pickle with json
except ImportError:
    import json
 
import UserDict
##import cPickle as pickle
 
import sqlite3
 
class DefaultArg:
    pass
 
class Solutions:
    Sqlite3 = 0
 
class FileDict(UserDict.DictMixin):
    "A dictionary that stores its data persistantly in a file"
 
    def __init__(self, solution=Solutions.Sqlite3, **options):
        assert solution == Solutions.Sqlite3
        try:
            self.__conn = options.pop('connection')
        except KeyError:
            filename = options.pop('filename')
            self.__conn = sqlite3.connect(filename)
 
        self.__tablename = options.pop('table', 'dict')
 
        self._nocommit = False
 
        assert not options, "Unrecognized options: %s" % options
 
        self.__conn.execute('create table if not exists %s (id integer primary key, hash integer, key blob, value blob);'%self.__tablename)
        self.__conn.execute('create index if not exists %s_index ON %s(hash);' % (self.__tablename, self.__tablename))
        self.__conn.commit()
 
    def _commit(self):
        if self._nocommit:
            return
 
        self.__conn.commit()
 
    def __pack(self, value):
        return sqlite3.Binary(json.dumps(value))
        ##return sqlite3.Binary(pickle.dumps(value, -1))
    def __unpack(self, value):
        return json.loads(str(value))
        ##return pickle.loads(str(value))
 
    def __get_id(self, key):
        cursor = self.__conn.execute('select key,id from %s where hash=?;'%self.__tablename, (hash(key),))
        for k,id in cursor:
            if self.__unpack(k) == key:
                return id
 
        raise KeyError(key)
 
    def __getitem__(self, key):
        cursor = self.__conn.execute('select key,value from %s where hash=?;'%self.__tablename, (hash(key),))
        for k,v in cursor:
            if self.__unpack(k) == key:
                return self.__unpack(v)
 
        raise KeyError(key)
 
    def __setitem(self, key, value):
        value_pickle = self.__pack(value)
 
        try:
            id = self.__get_id(key)
            cursor = self.__conn.execute('update %s set value=? where id=?;'%self.__tablename, (value_pickle, id) )
        except KeyError:
            key_pickle = self.__pack(key)
            cursor = self.__conn.execute('insert into %s (hash, key, value) values (?, ?, ?);'
                    %self.__tablename, (hash(key), key_pickle, value_pickle) )
 
        assert cursor.rowcount == 1
 
    def __setitem__(self, key, value):
        self.__setitem(key, value)
        self._commit()
 
    def __delitem__(self, key):
        id = self.__get_id(key)
        cursor = self.__conn.execute('delete from %s where id=?;'%self.__tablename, (id,))
        if cursor.rowcount <= 0:
            raise KeyError(key)
 
        self._commit()
 
    def update(self, d):
        for k,v in d.iteritems():
            self.__setitem(k, v)
        self._commit()
 
    def __iter__(self):
        return (self.__unpack(x[0]) for x in self.__conn.execute('select key from %s;'%self.__tablename) )
    def keys(self):
        return iter(self)
    def values(self):
        return (self.__unpack(x[0]) for x in self.__conn.execute('select value from %s;'%self.__tablename) )
    def items(self):
        return (map(self.__unpack, x) for x in self.__conn.execute('select key,value from %s;'%self.__tablename) )
    def iterkeys(self):
        return self.keys()
    def itervalues(self):
        return self.values()
    def iteritems(self):
        return self.items()
 
    def __contains__(self, key):
        try:
            self.__get_id(key)
            return True
        except KeyError:
            return False
 
    def __len__(self):
        return self.__conn.execute('select count(*) from %s;' % self.__tablename).fetchone()[0]
 
    def __del__(self):
        try:
            self.__conn
        except AttributeError:
            pass
        else:
            self.__conn.commit()
 
    @property
    def batch(self):
        return self._Batch(self)
 
    class _Batch:
        def __init__(self, d):
            self.__d = d
 
        def __enter__(self):
            self.__old_nocommit = self.__d._nocommit
            self.__d._nocommit = True
            return self.__d
 
        def __exit__(self, type, value, traceback):
            self.__d._nocommit = self.__old_nocommit
            self.__d._commit()
            return True
