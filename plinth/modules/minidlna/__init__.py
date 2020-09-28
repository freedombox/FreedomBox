# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure minidlna.
"""
from django.utils.translation import ugettext_lazy as _

import plinth.app as app_module
from plinth import actions, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups

from . import manifest

version = 2

managed_packages = ['minidlna']

managed_services = ['minidlna']

_description = [
    _('MiniDLNA is a simple media server software, with the aim of being '
      'fully compliant with DLNA/UPnP-AV clients. '
      'The MiniDLNA daemon serves media files '
      '(music, pictures, and video) to clients on a network. '
      'DLNA/UPnP is zero configuration protocol and is compliant '
      'with any device passing the DLNA Certification like portable '
      'media players, Smartphones, Televisions, and gaming systems ('
      'such as PS3 and Xbox 360) or applications such as totem and Kodi.')
]

app = None


class MiniDLNAApp(app_module.App):
    """Freedombox app managing miniDlna"""
    app_id = 'minidlna'

    def __init__(self):
        """Initialize the app components"""
        super().__init__()

        groups = {'minidlna': _('Media streaming server')}

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('MiniDLNA'), icon_filename='minidlna',
                               short_description=_('Simple Media Server'),
                               description=_description,
                               manual_page='MiniDLNA',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu(
            'menu-minidlna',
            name=info.name,
            short_description=info.short_description,
            url_name='minidlna:index',
            parent_url_name='apps',
            icon=info.icon_filename,
        )
        firewall = Firewall('firewall-minidlna', info.name, ports=['minidlna'],
                            is_external=False)
        webserver = Webserver('webserver-minidlna', 'minidlna-freedombox',
                              urls=['http://localhost:8200/'])
        shortcut = frontpage.Shortcut('shortcut-minidlna', info.name,
                                      short_description=info.short_description,
                                      description=info.description,
                                      icon=info.icon_filename,
                                      url='/_minidlna/', login_required=True,
                                      allowed_groups=list(groups))
        daemon = Daemon('daemon-minidlna', managed_services[0])

        backup_restore = BackupRestore('backup-restore-minidlna',
                                       **manifest.backup)
        self.add(backup_restore)

        self.add(menu_item)
        self.add(webserver)
        self.add(firewall)
        self.add(shortcut)
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-minidlna',
                                          groups=groups)
        self.add(users_and_groups)


def setup(helper, old_version=None):
    """Install and configure the package"""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'minidlna', ['setup'])
    if not old_version:
        helper.call('post', app.enable)
