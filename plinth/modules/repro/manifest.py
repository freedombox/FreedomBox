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

from plinth.modules.backups.backups import validate as validate_backup
from plinth.clients import store_url, validate

_jitsi_package_id = 'org.jitsi.meet'
_csipsimple_package_id = 'com.csipsimple'

_jitsi_download_url = 'https://download.jitsi.org/jitsi/'

clients = validate([{
    'name':
        _('Jitsi Meet'),
    'description':
        _('Jitsi is a set of open-source projects that allows '
          'you to easily build and deploy secure '
          'videoconferencing solutions. At the heart of Jitsi '
          'are Jitsi Videobridge and Jitsi Meet, which let you '
          'have conferences on the internet, while other '
          'projects in the community enable other features '
          'such as audio, dial-in, recording, '
          'and simulcasting.'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _jitsi_package_id)
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://itunes.apple.com/in/app/jitsi-meet/id1165103905'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _jitsi_download_url
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'jitsi'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _jitsi_download_url
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _jitsi_download_url
    }]
}, {
    'name':
        _('CSipSimple'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _csipsimple_package_id)
    }]
}])

backup = validate_backup({
    'config': {
        'directories': [],
        'files': ['/etc/repro/repro.config', '/etc/repro/users.txt'],
    },
    'data': {
        'directories': ['/var/lib/repro/'],
        'files': [],
    },
    'secrets': {
        'directories': ['/etc/repro/ssl/'],
        'files': ['/etc/repro/dh2048.pem'],
    },
    'services': ['repro']
})
