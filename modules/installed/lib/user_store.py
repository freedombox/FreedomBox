import os
try:
    import simplejson as json
except ImportError:
    import json
import cherrypy
import cfg
from model import User
from plugin_mount import UserStoreModule
from withsqlite.withsqlite import sqlite_db

class UserStore(UserStoreModule, sqlite_db):
    def __init__(self):
        self.db_file = cfg.user_db
        sqlite_db.__init__(self, self.db_file, autocommit=True, check_same_thread=False)
        self.__enter__()

    def close(self):
        self.__exit__(None,None,None)

    def current(self, name=False):
        """Return current user, if there is one, else None.
        If name = True, return the username instead of the user."""
        try:
            username = cherrypy.session.get(cfg.session_key)
            if name:
                return username
            else:
                return self.get(username)
        except AttributeError:
            return None
        
    def expert(self, username=None):
        if not username:
            username = self.current(name=True)
        groups = self.attr(username,"groups")
        if not groups:
            return False
        return 'expert' in groups        

    def attr(self, username=None, field=None):
        return self.get(username)[field]

    def get(self,username=None):
        return User(sqlite_db.get(self,username))

    def exists(self, username=None):
        try:
            user = self.get(username)
            if not user:
                return False
            elif user["username"]=='':
                return False
            return True
        except TypeError:
            return False

    def remove(self,username=None):
        self.__delitem__(username)

    def get_all(self):
        return self.items()

    def set(self,username=None,user=None):
        sqlite_db.__setitem__(self,username, user)
