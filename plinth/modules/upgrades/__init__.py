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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app for upgrades.
"""

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

import plinth
from plinth import actions
from plinth import app as app_module
from plinth import menu

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

managed_packages = ['unattended-upgrades']

_description = [
    _('Check for and apply the latest software and security updates.')
]

app = None


class UpgradesApp(app_module.App):
    """FreedomBox app for software upgrades."""

    app_id = 'upgrades'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, name=_('Update'),
                               icon='fa-refresh', description=_description,
                               manual_page='Upgrades')
        self.add(info)

        menu_item = menu.Menu('menu-upgrades', info.name, None, info.icon,
                              'upgrades:index', parent_url_name='system')
        self.add(menu_item)

        self._show_new_release_notification()

    def _show_new_release_notification(self):
        """When upgraded to new release, show a notification."""
        from plinth.notification import Notification
        try:
            note = Notification.get('upgrades-new-release')
            if note.data['version'] == plinth.__version__:
                # User already has notification for update to this version. It
                # may be dismissed or not yet dismissed
                return

            # User currently has a notification for an older version, update.
            dismiss = False
        except KeyError:
            # Don't show notification for the first version user runs, create
            # but don't show it.
            dismiss = True

        data = {
            'version': plinth.__version__,
            'app_name': 'Update',
            'app_icon': 'fa-refresh'
        }
        title = ugettext_noop('FreedomBox Updated')
        note = Notification.update_or_create(
            id='upgrades-new-release', app_id='upgrades', severity='info',
            title=title, body_template='upgrades-new-release.html', data=data,
            group='admin')
        note.dismiss(should_dismiss=dismiss)


def init():
    """Initialize the module."""
    global app
    app = UpgradesApp()
    app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'upgrades', ['enable-auto'])


def is_enabled():
    """Return whether the module is enabled."""
    output = actions.run('upgrades', ['check-auto'])
    return 'True' in output.split()


def enable():
    """Enable the module."""
    actions.superuser_run('upgrades', ['enable-auto'])


def disable():
    """Disable the module."""
    actions.superuser_run('upgrades', ['disable-auto'])
