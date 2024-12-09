# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Single Sign On services."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth.config import DropinConfigs
from plinth.package import Packages

from . import privileged


class SSOApp(app_module.App):
    """FreedomBox app for single sign on."""

    app_id = 'sso'

    _version = 3

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               depends=['security',
                                        'apache'], name=_('Single Sign On'))
        self.add(info)

        packages = Packages(
            'packages-sso',
            ['libapache2-mod-auth-pubtkt', 'python3-cryptography', 'flite'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-sso', [
            '/etc/apache2/includes/freedombox-single-sign-on.conf',
        ])
        self.add(dropin_configs)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.create_key_pair()
