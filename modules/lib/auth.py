# Form based authentication for CherryPy. Requires the
# Session tool to be loaded.
#
# Thanks for this code is owed to Arnar Birgisson -at - gmail.com.  It
# is based on code he wrote that was retrieved from
# http://tools.cherrypy.org/wiki/AuthenticationAndAccessRestrictions
# on 1 February 2011.

import cherrypy
import urllib
from passlib.hash import bcrypt
from passlib.exc import PasswordSizeError
import cfg
import random
from model import User

cfg.session_key = '_cp_username'

def add_user(username, passphrase, name='', email='', expert=False):
    """Add a new user with specified username and passphrase.
    """
    error = None
    if not username: error = "Must specify a username!"
    if not passphrase: error = "Must specify a passphrase!"

    if error is None:
        if username in map(lambda x: x[0], cfg.users.get_all()):
            error = "User already exists!"
        else:
            try:
                pass_hash = bcrypt.encrypt(passphrase)
            except PasswordSizeError:
                error = "Password is too long."

    if error is None:
        di = {
            'username':username,
            'name':name,
            'email':email,
            'expert':'on' if expert else 'off',
            'groups':['expert'] if expert else [],
            'passphrase':pass_hash,
            'salt':pass_hash[7:29], # for bcrypt
        }
        new_user = User(di)
        cfg.users.set(username,new_user)

    if error:
        cfg.log(error)
    return error

def check_credentials(username, passphrase):
    """Verifies credentials for username and passphrase.

    Returns None on success or a string describing the error on failure.

    Handles passwords up to 4096 bytes:

    >>> len("A" * 4096)
    4096
    >>> len(u"u|2603" * 682)
    4092

    """
    if not username or not passphrase:
        error = "No username or password."
        cfg.log(error)
        return error

    bad_authentication = "Bad username or password."
    hashed_password = None

    if username not in cfg.users or 'passphrase' not in cfg.users[username]:
        cfg.log(bad_authentication)
        return bad_authentication

    hashed_password = cfg.users[username]['passphrase']

    try:
        # time-dependent comparison when non-ASCII characters are used.
        if not bcrypt.verify(passphrase, hashed_password):
            error = bad_authentication
        else:
            error = None
    except PasswordSizeError:
        error = bad_authentication

    if error:
        cfg.log(error)
    return error

def check_auth(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a
    list of conditions that the user must fulfill"""
    conditions = cherrypy.request.config.get('auth.require', None)
    # format GET params
    get_params = urllib.quote(cherrypy.request.request_line.split()[1])
    if conditions is not None:
        username = cherrypy.session.get(cfg.session_key)
        if username:
            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    # Send old page as from_page parameter
                    raise cherrypy.HTTPRedirect(cfg.server_dir + "/auth/login?from_page=%s" % get_params)
        else:
            # Send old page as from_page parameter
            raise cherrypy.HTTPRedirect(cfg.server_dir + "/auth/login?from_page=%s" % get_params)

cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)

def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current username as cherrypy.request.login
#
# Define those at will however suits the application.

def member_of(groupname):
    def check():
        # replace with actual check if <username> is in <groupname>
        return cherrypy.request.login == 'joe' and groupname == 'admin'
    return check

def name_is(reqd_username):
    return lambda: reqd_username == cherrypy.request.login

# These might be handy

def any_of(*conditions):
    """Returns True if any of the conditions match"""
    def check():
        for c in conditions:
            if c():
                return True
        return False
    return check

# By default all conditions are required, but this might still be
# needed if you want to use it inside of an any_of(...) condition
def all_of(*conditions):
    """Returns True if all of the conditions match"""
    def check():
        for c in conditions:
            if not c():
                return False
        return True
    return check


