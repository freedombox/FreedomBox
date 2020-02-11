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

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module

version = 1

is_essential = True

depends = ['security', 'apache']

managed_packages = [
    'libapache2-mod-auth-pubtkt',
    'openssl',
    'python3-openssl',
    'flite',
]


class SSOApp(app_module.App):
    """FreedomBox app for single sign on."""
    app_id = 'sso'

    def __init__(self):
        """Create components for the app."""
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, depends=depends,
                               name=_('Single Sign On'))
        self.add(info)


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    actions.superuser_run('auth-pubtkt', ['create-key-pair'])
