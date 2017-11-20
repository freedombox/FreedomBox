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

from plinth.templatetags.plinth_extras import Desktop_OS, Mobile_OS, Store
from plinth.utils import play_store_url

jitsi_package_id = 'org.jitsi.meet'
csipsimple_package_id = 'com.csipsimple'

jitsi_download_url = 'https://download.jitsi.org/jitsi/'

clients = [{
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
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': play_store_url(jitsi_package_id)
    }, {
        'type': 'store',
        'os': Mobile_OS.IOS.value,
        'store_name': Store.APP_STORE.value,
        'url': 'https://itunes.apple.com/in/app/jitsi-meet/id1165103905'
    }, {
        'type': 'download',
        'os': Desktop_OS.GNU_LINUX.value,
        'url': jitsi_download_url
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'jitsi'
    }, {
        'type': 'download',
        'os': Desktop_OS.MAC_OS.value,
        'url': jitsi_download_url
    }, {
        'type': 'download',
        'os': Desktop_OS.WINDOWS.value,
        'url': jitsi_download_url
    }]
}, {
    'name':
        _('CSipSimple'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': play_store_url(csipsimple_package_id)
    }]
}]
