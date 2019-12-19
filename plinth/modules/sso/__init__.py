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
FreedomBox app to configure Single Sign On services.
"""

from plinth import actions
from django.utils.translation import ugettext_lazy as _

version = 1

is_essential = True

depends = ['security', 'apache']

name = _('Single Sign On')

managed_packages = [
    'libapache2-mod-auth-pubtkt',
    'openssl',
    'python3-openssl',
    'flite',
]


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    actions.superuser_run('auth-pubtkt', ['create-key-pair'])
