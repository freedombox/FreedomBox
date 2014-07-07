import cfg
from model import User
from plugin_mount import UserStoreModule
from withsqlite.withsqlite import sqlite_db


class UserStore(UserStoreModule, sqlite_db):
    def __init__(self):
        super(UserStore, self).__init__()

        self.db_file = cfg.user_db
        sqlite_db.__init__(self, self.db_file, autocommit=True, check_same_thread=False)
        self.__enter__()

    def close(self):
        self.__exit__(None,None,None)

    def current(self, request=None, name=False):
        """Return current user, if there is one, else None.
        If name = True, return the username instead of the user."""
        if not request:
            return None

        try:
            username = request.session[cfg.session_key]
        except KeyError:
            return None

        if name:
            return username

        return self.get(username)

    def expert(self, username=None, request=None):
        """Return whether the current or provided user is an expert"""
        if not username:
            if not request:
                return False

            username = self.current(request=request, name=True)

        groups = self.attr(username, 'groups')

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
