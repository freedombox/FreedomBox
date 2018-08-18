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

from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.modules.backups.backups import validate as validate_backup
from plinth.clients import validate
from plinth.utils import format_lazy

clients = validate([{
    'name':
        _('Gobby'),
    'description':
        _('Gobby is a collaborative text editor'),
    'usage':
        format_lazy(
            _('Start Gobby and select "Connect to Server" and '
              'enter your {box_name}\'s domain name.'),
            box_name=_(cfg.box_name)),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://github.com/gobby/gobby/wiki/Download'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://github.com/gobby/gobby/wiki/Download'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'gobby'
    }]
}])

backup = validate_backup({
    'config': {
        'directories': [],
        'files': [],
    },
    'data': {
        'directories': ['/var/lib/infinoted/'],
        'files': [],
    },
    'secrets': {
        'directories': [],
        'files': [
            '/etc/infinoted/infinoted-cert.pem',
            '/etc/infinoted/infinoted-key.pem'
        ],
    },
    'services': ['infinoted']
})
