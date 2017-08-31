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
Plinth module for Apache server.
"""

from plinth import actions

version = 1

is_essential = True

managed_packages = ['apache2', 'libapache2-mod-gnutls', 'libapache2-mod-php']


def setup(helper, old_version=False):
    """Configure the module."""
    helper.install(managed_packages)
    actions.superuser_run('apache', ['setup'])
