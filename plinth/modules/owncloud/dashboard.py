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

from plinth import actions
from plinth.modules import dashboard

from .owncloud import get_status


def enable():
    actions.superuser_run('owncloud-setup', ['enable'], async=True)


def disable():
    actions.superuser_run('owncloud-setup', ['noenable'], async=True)


def is_enabled():
    return get_status()['enabled']


# We do not know the hostname of this freedombox when registering the app,
# so we build the final URL in the custom template
dashboard.register_app(name='owncloud', enable=enable, disable=disable,
                       is_enabled=is_enabled, url='/owncloud',
                       template='dashboard_owncloud.inc',
                       description='Cloud services running on your Freedombox')
