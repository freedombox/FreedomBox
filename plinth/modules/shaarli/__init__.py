# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Shaarli.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from . import manifest

version = 1

managed_packages = ['shaarli']

_description = [
    _('Shaarli allows you to save and share bookmarks.'),
    _('Note that Shaarli only supports a single user account, which you will '
      'need to setup on the initial visit.'),
]

app = None


class ShaarliApp(app_module.App):
    """FreedomBox app for Shaarli."""

    app_id = 'shaarli'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Shaarli'), icon_filename='shaarli',
                               short_description=_('Bookmarks'),
                               description=_description, manual_page='Shaarli',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-shaarli', info.name,
                              info.short_description, info.icon_filename,
                              'shaarli:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-shaarli', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/shaarli',
                                      clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-shaarli', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-shaarli', 'shaarli')
        self.add(webserver)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
