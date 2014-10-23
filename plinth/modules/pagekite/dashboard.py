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
    pass


def disable():
    pass


def is_enabled():
    return True


# We do not know the hostname of this freedombox when registering the app,
# so we build the final URL in the custom template
description = 'Allows accessing your FreedomBox from the internet'
dashboard.register_app(name='PageKite', enable=enable, disable=disable,
                       is_enabled=is_enabled, description=description,
                       synchronous=True)


def get_kite_name():
    output = actions.superuser_run('pagekite-configure', ['get-kite'])
    return {'name': output.split()[0]}


dashboard.register_statusline(name="kitename",
                              template="dashboard_kitename.inc",
                              get_data=get_kite_name,
                              order=10)
