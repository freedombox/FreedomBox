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


def enable():
    return actions.superuser_run('tor', ['start'])


def disable():
    return actions.superuser_run('tor', ['stop'])


def is_running():
    return actions.superuser_run("tor", ["is-running"]).strip() == "yes"


dashboard.register_app(name='tor', is_enabled=is_running,
                       enable=enable, disable=disable, synchronous=True,
                       description='Tor anonymization service')
