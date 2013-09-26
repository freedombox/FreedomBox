# Form based authentication for CherryPy. Requires the
# Session tool to be loaded.
#
# Thanks for this code is owed to Arnar Birgisson -at - gmail.com.  It
# is based on code he wrote that was retrieved from
# http://tools.cherrypy.org/wiki/AuthenticationAndAccessRestrictions
# on 1 February 2011.

# TODO: DeprecationWarning: the md5 module is deprecated; use hashlib instead import md5

import cherrypy
import urllib, hashlib
import cfg
import random
import time

cfg.session_key = '_cp_username'

def check_credentials(username, passphrase):
    """Verifies credentials for username and passphrase.
    Returns None on success or a string describing the error on failure"""

    start = time.clock()

    if not username or not passphrase:
        error = "No username or password."
        cfg.log(error)
        return error

    if username in cfg.users:
        u = cfg.users[username]
    else:
        u = None
    # hash the password whether the user exists, to foil timing
    # side-channel attacks
    pass_hash = hashlib.md5(passphrase).hexdigest()

    if u is None or u['passphrase'] != pass_hash:
        error = "Bad user-name or password."
    else:
        error = None

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
                    raise cherrypy.HTTPRedirect("/auth/login?from_page=%s" % get_params)
        else:
            # Send old page as from_page parameter
            raise cherrypy.HTTPRedirect("/auth/login?from_page=%s" % get_params)

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


