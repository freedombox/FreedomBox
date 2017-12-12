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

from plinth.clients import store_url, validate

clients = validate([{
    'name':
        _('DAVDroid'),
    'usage':
        _('Enter the URL of the Radicale server (e.g. '
          'http://localhost:5232) and your user name. DAVdroid will '
          'show all existing calendars and address books and you can '
          'create new.'),
    'platforms': [{
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
        _('Evolution'),
    'description':
        _('Evolution is a personal information management '
          'application that provides integrated mail, '
          'calendaring and address book functionality.'),
    'usage':
        _('In Evolution add a new calendar and address book '
          'respectively with WebDAV. Enter the URL of the Radicale '
          'server (e.g. http://localhost:5232) and your user name. '
          'Clicking on the search button will list the existing '
          'calendars and address books.'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'evolution'
    }]
}])
