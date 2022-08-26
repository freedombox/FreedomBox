# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Single Sign On services."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth.package import Packages

from . import privileged


class SSOApp(app_module.App):
    """FreedomBox app for single sign on."""

    app_id = 'sso'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               depends=['security',
                                        'apache'], name=_('Single Sign On'))
        self.add(info)

        packages = Packages('packages-sso', [
            'libapache2-mod-auth-pubtkt', 'openssl', 'python3-openssl', 'flite'
        ])
        self.add(packages)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.create_key_pair()
