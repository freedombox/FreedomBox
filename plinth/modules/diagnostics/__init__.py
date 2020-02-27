# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for system diagnostics.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import daemon, menu
from plinth.modules.apache.components import diagnose_url_on_all

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

_description = [
    _('The system diagnostic test will run a number of checks on your '
      'system to confirm that applications and services are working as '
      'expected.')
]

app = None


class DiagnosticsApp(app_module.App):
    """FreedomBox app for diagnostics."""

    app_id = 'diagnostics'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential,
                               name=_('Diagnostics'), icon='fa-heartbeat',
                               description=_description,
                               manual_page='Diagnostics')
        self.add(info)

        menu_item = menu.Menu('menu-diagnostics', info.name, None, info.icon,
                              'diagnostics:index', parent_url_name='system')
        self.add(menu_item)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(daemon.diagnose_port_listening(8000, 'tcp4'))
        results.extend(
            diagnose_url_on_all('http://{host}/plinth/',
                                check_certificate=False))

        return results


def init():
    """Initialize the module"""
    global app
    app = DiagnosticsApp()
    app.set_enabled(True)
