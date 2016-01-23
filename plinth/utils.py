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
Miscelleneous utility method.
"""

import importlib
from django.utils.functional import lazy


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
