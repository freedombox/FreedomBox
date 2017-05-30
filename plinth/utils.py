#
# This file is part of Plinth.
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

import importlib
import os
import ruamel.yaml
from django.utils.functional import lazy
from plinth.modules import names


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
    """Decorator to mark a view as accesible by non-admin users."""
    setattr(func, 'IS_NON_ADMIN', True)
    return func


def is_user_admin(request, cached=False):
    """Return whether user is an administrator."""
    if not request.user.is_authenticated():
        return False

    if 'cache_user_is_admin' in request.session and cached:
        return request.session['cache_user_is_admin']

    user_is_admin = request.user.groups.filter(name='admin').exists()
    request.session['cache_user_is_admin'] = user_is_admin
    return user_is_admin


def get_domain_names():
    """Return the domain name(s)"""
    domain_names = []

    for domain_type, domains in names.domains.items():
        if domain_type == 'hiddenservice':
            continue
        for domain in domains:
            domain_names.append((domain, domain))

    return domain_names


class YAMLFile(object):
    """A context management class for updating YAML files"""
    def __init__(self, yaml_file, post_exit=None):
        """Return a context object for the YAML file.

        Parameters:
        yaml_file - the YAML file to update.
        post_exit - a function that will be called after updating the YAML file.
        """
        self.yaml_file = yaml_file
        self.post_exit = post_exit
        self.conf = None

    def __enter__(self):
        with open(self.yaml_file, 'r') as intro_conf:
            if not self.is_file_empty():
                self.conf = ruamel.yaml.round_trip_load(intro_conf)
            else:
                self.conf = {}

            return self.conf

    def __exit__(self, typ, value, traceback):
        with open(self.yaml_file, 'w') as intro_conf:
            ruamel.yaml.round_trip_dump(self.conf, intro_conf)

        if self.post_exit:
            self.post_exit()

    def is_file_empty(self):
        return os.stat(self.yaml_file).st_size == 0
