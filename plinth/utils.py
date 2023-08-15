# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Miscellaneous utility methods.
"""

import gzip
import importlib
import os
import random
import re
import string

import markupsafe
import ruamel.yaml
from django.utils.functional import lazy

from plinth.version import Version  # noqa


def import_from_gi(library, version):
    """Import and return a GObject introspection library."""
    try:
        import gi as package
        package_name = 'gi'
    except ImportError:
        import pgi as package
        package_name = 'pgi'

    package.require_version(library, version)

    return importlib.import_module(package_name + '.repository.' + library)


def _format_lazy(string, *args, **kwargs):
    """Lazily format a lazy string."""
    allow_markup = kwargs.pop('allow_markup', False)
    string = str(string)
    string = string.format(*args, **kwargs)
    if allow_markup:
        string = markupsafe.Markup(string)

    return string


format_lazy = lazy(_format_lazy, str)


def non_admin_view(func):
    """Decorator to mark a view as accessible by non-admin users."""
    setattr(func, 'IS_NON_ADMIN', True)
    return func


def user_group_view(func, group_name):
    """Decorator to mark a view as accessible by admin or group users."""
    setattr(func, 'GROUP_NAME', group_name)
    return func


def is_valid_user_name(user_name):
    """Check if the given username is valid.

    Note: Debian is VERY flexible with user names.
    """
    if 32 < len(user_name):
        return False

    if user_name.startswith('-'):
        return False

    for forbidden in (' \n\t/\\:'):
        if forbidden in user_name:
            return False

    return True


def is_user_admin(request, cached=False):
    """Return whether user is an administrator."""
    if not request.user.is_authenticated:
        return False

    if 'cache_user_is_admin' in request.session and cached:
        return request.session['cache_user_is_admin']

    user_is_admin = request.user.groups.filter(name='admin').exists()
    request.session['cache_user_is_admin'] = user_is_admin
    return user_is_admin


class YAMLFile:
    """A context management class for updating YAML files"""

    def __init__(self, yaml_file):
        """Return a context object for the YAML file.

        Parameters:
        yaml_file - the YAML file to update.
        updating the YAML file.
        """
        self.yaml_file = yaml_file
        self.conf = None

        self.yaml = ruamel.yaml.YAML()
        self.yaml.preserve_quotes = True

    def __enter__(self):
        with open(self.yaml_file, 'r', encoding='utf-8') as intro_conf:
            if not self.is_file_empty():
                self.conf = self.yaml.load(intro_conf)
            else:
                self.conf = {}

            return self.conf

    def __exit__(self, type_, value, traceback):
        if not traceback:
            with open(self.yaml_file, 'w', encoding='utf-8') as intro_conf:
                self.yaml.dump(self.conf, intro_conf)

    def is_file_empty(self):
        return os.stat(self.yaml_file).st_size == 0


def random_string(size=8):
    """Generate a random alphanumeric string."""
    chars = (random.SystemRandom().choice(string.ascii_letters)
             for _ in range(size))
    return ''.join(chars)


def generate_password(size=32):
    """Generate a random password using ascii alphabet and digits."""
    chars = (random.SystemRandom().choice(string.ascii_letters + string.digits)
             for _ in range(size))
    return ''.join(chars)


def grep(pattern, file_name):
    """Return lines of a file matching a pattern."""
    return [
        line.rstrip() for line in open(file_name, encoding='utf-8')
        if re.search(pattern, line)
    ]


def gunzip(gzip_file, output_file):
    """Utility to unzip a given gzip file and write it to an output file

    gzip_file: string path to a gzip file
    output_file: string path to the output file
    mode: an octal number to specify file permissions
    """
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, mode=0o755)

    with gzip.open(gzip_file, 'rb') as file_handle:
        contents = file_handle.read()

    def opener(path, flags):
        return os.open(path, flags, mode=0o644)

    with open(output_file, 'wb', opener=opener) as file_handle:
        file_handle.write(contents)


def is_non_empty_file(file_path):
    return os.path.isfile(file_path) and os.path.getsize(file_path) > 0


def is_authenticated_user(username, password):
    """Return true if the user authentication succeeds."""
    import pam  # Minimize dependencies for running tests
    pam_authenticator = pam.pam()
    return bool(pam_authenticator.authenticate(username, password))
