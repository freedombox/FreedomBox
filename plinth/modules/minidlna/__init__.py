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
"""
FreedomBox app to configure minidlna.
"""
from django.utils.translation import ugettext_lazy as _

from plinth import actions
import plinth.app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.action_utils import diagnose_url

from .manifest import backup, clients  # noqa

version = 1

name = 'minidlna'

icon_name = name

managed_packages = ['minidlna']

managed_services = ['minidlna']

short_description = _('Simple Media Server')

description = [
    _('MiniDLNA is a simple media server software, with the aim of being '
      'fully compliant with DLNA/UPnP-AV clients. '
      'The MiniDNLA daemon serves media files '
      '(music, pictures, and video) to clients on a network. '
      'DNLA/UPnP is zero configuration protocol and is compliant '
      'with any device passing the DLNA Certification like portable '
      'media players, Smartphones, Televisions, and gaming systems ('
      'such as PS3 and Xbox 360) or applications such as totem and Kodi.')
]

clients = clients

group = ('minidlna', _('Media streaming server'))

app = None


class MiniDLNAApp(app_module.App):
    """Freedombox app managing miniDlna"""
    app_id = 'minidlna'

    def __init__(self):
        """Initialize the app components"""
        super().__init__()
        menu_item = menu.Menu(
            'menu-minidlna',
            name=name,
            short_description=short_description,
            url_name='minidlna:index',
            parent_url_name='apps',
            icon=icon_name,
        )
        firewall = Firewall('firewall-minidlna', name, ports=['minidlna'],
                            is_external=False)
        webserver = Webserver('webserver-minidlna', 'minidlna-plinth')
        shortcut = frontpage.Shortcut(
            'shortcut-minidlna',
            name,
            short_description=short_description,
            description=description,
            icon=icon_name,
            url='/_minidlna/',
            login_required=True,
        )
        daemon = Daemon('daemon-minidlna', managed_services[0])

        self.add(menu_item)
        self.add(webserver)
        self.add(firewall)
        self.add(shortcut)
        self.add(daemon)


def init():
    global app
    app = MiniDLNAApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the package"""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'minidlna', ['setup'])
    helper.call('post', app.enable)


def diagnose():
    """Check if the http page listening on 8200 is accessible"""
    results = []
    results.append(diagnose_url('http://localhost:8200/'))

    return results
