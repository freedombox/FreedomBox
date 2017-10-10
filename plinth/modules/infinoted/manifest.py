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

from django.utils.translation import ugettext_lazy as _

from plinth.utils import format_lazy
from plinth import cfg

clients = [
    {
        'name': _('Gobby'),
        'description': _('Gobby is a collaborative text editor'),
        'usage': format_lazy(_('start Gobby and select "Connect to Server" and '
                               'enter your {box_name}\'s domain name.'),
                             box_name=_(cfg.box_name)),
        'platforms': [
            {
                'type': 'download',
                'os': 'Windows',
                'url': 'http://releases.0x539.de/gobby/gobby-stable.exe'
            },
            {
                'type': 'apt',
                'os': 'Debian',
                'package_name': 'gobby-infinote'
            }
        ]
    }
]
