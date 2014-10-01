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
from .firewall import get_enabled_status


def enable():
    return actions.superuser_run('firewall', ['set-status', 'enable'])


def disable():
    return actions.superuser_run('firewall', ['set-status', 'disable'])


dashboard.register_app(name='firewall', is_enabled=get_enabled_status,
                       enable=enable, disable=disable,
                       description='Firewall for your Freedombox')
