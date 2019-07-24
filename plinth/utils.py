#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Miscellaneous utility methods.
"""

import gzip
import importlib
import os
import random
import re
import string
from distutils.version import LooseVersion

import ruamel.yaml
from django.utils.functional import lazy

Version = LooseVersion  # Abstraction over distutils.version.LooseVersion


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
    string = str(string)
    return string.format(*args, **kwargs)


format_lazy = lazy(_format_lazy, str)


def non_admin_view(func):
    """Decorator to mark a view as accessible by non-admin users."""
    setattr(func, 'IS_NON_ADMIN', True)
    return func


def is_user_admin(request, cached=False):
    """Return whether user is an administrator."""
    if not request.user.is_authenticated:
        return False

    if 'cache_user_is_admin' in request.session and cached:
        return request.session['cache_user_is_admin']

    user_is_admin = request.user.groups.filter(name='admin').exists()
    request.session['cache_user_is_admin'] = user_is_admin
    return user_is_admin


def get_domain_names():
    """Return the domain name(s)"""
    from plinth.modules import names

    domain_names = []

    for domain_type, domains in names.domains.items():
        if domain_type == 'hiddenservice':
            continue
        for domain in domains:
            domain_names.append((domain, domain))

    return domain_names


class YAMLFile(object):
    """A context management class for updating YAML files"""

    def __init__(self, yaml_file):
        """Return a context object for the YAML file.

        Parameters:
        yaml_file - the YAML file to update.
        updating the YAML file.
        """
        self.yaml_file = yaml_file
        self.conf = None

    def __enter__(self):
        with open(self.yaml_file, 'r') as intro_conf:
            if not self.is_file_empty():
                self.conf = ruamel.yaml.round_trip_load(intro_conf)
            else:
                self.conf = {}

            return self.conf

    def __exit__(self, type_, value, traceback):
        if not traceback:
            with open(self.yaml_file, 'w') as intro_conf:
                ruamel.yaml.round_trip_dump(self.conf, intro_conf)

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
        line.rstrip() for line in open(file_name) if re.search(pattern, line)
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


def is_axes_old():
    """Return true if using django-axes version strictly less than 5.0.0.

    XXX: Remove this method and allow code that uses it after django-axes >=
    5.0.0 becomes available in Debian stable.

    """
    import axes
    return LooseVersion(axes.get_version()) < LooseVersion('5.0')
