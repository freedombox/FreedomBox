# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for monkeysphere.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.modules.users.components import UsersAndGroups

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

managed_packages = ['monkeysphere']

_description = [
    _('With Monkeysphere, an OpenPGP key can be generated for each configured '
      'domain serving SSH. The OpenPGP public key can then be uploaded to the '
      'OpenPGP keyservers. Users connecting to this machine through SSH can '
      'verify that they are connecting to the correct host.  For users to '
      'trust the key, at least one person (usually the machine owner) must '
      'sign the key using the regular OpenPGP key signing process.  See the '
      '<a href="http://web.monkeysphere.info/getting-started-ssh/"> '
      'Monkeysphere SSH documentation</a> for more details.'),
    _('Monkeysphere can also generate an OpenPGP key for each Secure Web '
      'Server (HTTPS) certificate installed on this machine. The OpenPGP '
      'public key can then be uploaded to the OpenPGP keyservers. Users '
      'accessing the web server through HTTPS can verify that they are '
      'connecting to the correct host. To validate the certificate, the user '
      'will need to install some software that is available on the '
      '<a href="https://web.monkeysphere.info/download/"> Monkeysphere '
      'website</a>.')
]

app = None


class MonkeysphereApp(app_module.App):
    """FreedomBox app for Monkeysphere."""

    app_id = 'monkeysphere'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Monkeysphere'), icon='fa-certificate',
                               description=_description,
                               manual_page='Monkeysphere')
        self.add(info)

        menu_item = menu.Menu('menu-monkeysphere', info.name, None, info.icon,
                              'monkeysphere:index', parent_url_name='system',
                              advanced=True)
        self.add(menu_item)

        users_and_groups = UsersAndGroups('users-and-groups-monkeysphere',
                                          reserved_usernames=['monkeysphere'])
        self.add(users_and_groups)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
