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

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

CONFIG_FILE = '/etc/gitweb-freedombox.conf'
GIT_REPO_PATH = '/var/lib/git'

clients = validate([
    {
        'name': _('Gitweb'),
        'platforms': [{
            'type': 'web',
            'url': '/gitweb/'
        }]
    },
    {
        'name':
            _('Git'),
        'platforms': [{
            'type': 'download',
            'os': 'gnu-linux',
            'url': 'https://git-scm.com/download/linux'
        }, {
            'type': 'download',
            'os': 'macos',
            'url': 'https://git-scm.com/download/mac'
        }, {
            'type': 'download',
            'os': 'windows',
            'url': 'https://git-scm.com/download/mac'
        }]
    },
])

backup = validate_backup({
    'config': {
        'files': [CONFIG_FILE]
    },
    'data': {
        'directories': [GIT_REPO_PATH]
    }
})
