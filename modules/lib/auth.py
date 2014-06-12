from django.http.response import HttpResponseRedirect
import functools
from passlib.hash import bcrypt
from passlib.exc import PasswordSizeError

import cfg
from model import User

cfg.session_key = '_username'


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


# XXX: Only required until we start using Django authentication system properly
def login_required(func):
    """A decorator to ensure that user is logged in before accessing a view"""
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        """Check that user is logged in"""
        if not request.session.get(cfg.session_key, None):
            return HttpResponseRedirect(
                cfg.server_dir + "/auth/login?from_page=%s" % request.path)

        return func(request, *args, **kwargs)

    return wrapper
