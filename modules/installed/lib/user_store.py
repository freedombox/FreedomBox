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
        self.data_dir = cfg.users_dir
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
        self.commit()

    def get_all(self):
        return self.items()

    def set(self,username=None,user=None):
        sqlite_db.__setitem__(self,username, user)

class UserStoreOld():
#class UserStore(UserStoreModule):
    """The user storage is on disk.  Rather than slurp the entire
    thing, we read from the disk as needed.  Writes are immediate,
    though.

    TODO: file locking"""
    def __init__(self):
        self.data_dir = cfg.users_dir
        self.users = {}
    def sanitize(username):
        """Return username with nonalphanumeric/underscore chars
        removed. 

        TODO: allow international chars in usernames."""
        pass
    def attr(self, key, username):
        """Return field from username's record.  If key does not
        exist, don't raise attribute error, just return None.

        User defaults to current.  If no current user and none
        specified, return none."""
        try:
            return self.get(username)[key]
        except AttributeError:
            return None

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
        """Return True if user username is an expert, else False.

        If username is None, use the current user.  If no such user exists, return False."""
        user = self.get(username)
        if not user:
            return False
        return 'expert' in user['groups']

    def get(self, username=None, reload=False):
        """Returns a user instance with the user's info or else None if the user couldn't be found.

        If reload is true, reload from disk, regardless of dict's contents

        If username is None, try current user.  If no current user, return None.

        TODO: implement user_store.get reload"""

        if not username:
            username = self.current(name=True)

        try:
            return self.users[username]
        except KeyError:
            try:
                IF = open(os.path.join(self.data_dir, username), "r")
            except IOError:
                return None
            data = IF.read()
            IF.close()

            # We cache the result, and since we assume a system with
            # relatively few users and small user data files, we never
            # expire those results.  If we revisit that assumption, we
            # might need some cache expiry.
            self.users[username] = User(json.loads(data))

            return self.users[username]
    def exists(self, username):
        """Return True if username exists, else False."""
        return username in self.users or os.path.exists(os.path.join(cfg.users_dir, username))
    def get_all(self):
        "Returns a list of all the user objects"
        usernames = os.listdir(self.data_dir)
        for name in usernames:
            self.get(name)
        return self.users
    def set(self, user):
        """Set the user data, both in memory and as needed in storage."""
        OF = open(os.path.join(self.data_dir, user['username']), 'w')
        OF.write(json.dumps(user))
        OF.close()
    def remove(self, user):
        """Delete the user from storage and RAM.  User can be a user instance or a username."""
        try:
            name = user['name']
        except TypeError:
            if isinstance(user, basestring):
                name = user
            else:
                raise TypeError
        os.unlink(os.path.join(cfg.users_dir, name))
        try:
            del self.users[name]
        except KeyError:
            pass
        cfg.log.info("%s deleted %s" % (cherrypy.session.get(cfg.session_key), name))
