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

from plinth.clients import store_url, validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name':
        _('DAVx5'),
    'usage':
        _('Enter the URL of the Radicale server (e.g. '
          'https://<your.freedombox.address>) and your user name. DAVx5 will '
          'show all existing calendars and address books and you can '
          'create new.'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'at.bitfire.davdroid'),
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'at.bitfire.davdroid'),
    }]
}, {
    'name':
        _('GNOME Calendar'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'gnome-calendar'
    }]
}, {
    'name':
        _('Mozilla Thunderbird'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'thunderbird'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://www.mozilla.org/thunderbird/'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://www.mozilla.org/thunderbird/'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://www.mozilla.org/thunderbird/'
    }]
}, {
    'name':
        _('Evolution'),
    'description':
        _('Evolution is a personal information management '
          'application that provides integrated mail, '
          'calendaring and address book functionality.'),
    'usage':
        _('In Evolution add a new calendar and address book '
          'respectively with WebDAV. Enter the URL of the Radicale '
          'server (e.g. https://<your.freedombox.address>) and your user name. '
          'Clicking on the search button will list the existing '
          'calendars and address books.'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'evolution'
    }]
}, {
    'name':
        _('Radicale'),
    'platforms': [{
        'type': 'web',
        'url': '/radicale/'
    }]
}])

backup = validate_backup({
    'data': {
        'directories': ['/var/lib/radicale/']
    },
    'services': ['radicale']
})
