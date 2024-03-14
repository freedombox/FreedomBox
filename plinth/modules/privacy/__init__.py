# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to the Privacy app."""

from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import menu
from plinth.config import DropinConfigs
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages

from . import manifest, privileged

_description = [_('Manage system-wide privacy settings.')]


class PrivacyApp(app_module.App):
    """FreedomBox app for Privacy."""

    app_id = 'privacy'

    _version = 2

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Privacy'),
                               icon='fa-eye-slash', description=_description,
                               manual_page=None)
        self.add(info)

        menu_item = menu.Menu('menu-privacy', info.name,
                              info.short_description, info.icon,
                              'privacy:index', parent_url_name='system:data',
                              order=10)
        self.add(menu_item)

        packages = Packages('packages-privacy', ['popularity-contest', 'gpg'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-privacy', [
            '/etc/dpkg/origins/freedombox',
        ])
        self.add(dropin_configs)

        backup_restore = BackupRestore('backup-restore-privacy',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if old_version == 0:
            privileged.set_configuration(enable_popcon=True)
            _show_privacy_notification()


def _show_privacy_notification():
    """Show a notification asking user to review privacy settings."""
    from plinth.notification import Notification
    message = gettext_noop(
        'Please update privacy settings to match your preferences.')
    data = {
        'app_name': 'translate:' + gettext_noop('Privacy'),
        'app_icon': 'fa-eye-slash'
    }
    title = gettext_noop('Review privacy setting')
    actions_ = [{
        'type': 'link',
        'class': 'primary',
        'text': gettext_noop('Go to {app_name}'),
        'url': 'privacy:index'
    }, {
        'type': 'dismiss'
    }]
    Notification.update_or_create(id='privacy-review', app_id='privacy',
                                  severity='info', title=title,
                                  message=message, actions=actions_, data=data,
                                  group='admin')
