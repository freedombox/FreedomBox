# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Single Sign On services.
"""

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth.package import Packages

version = 1

is_essential = True

depends = ['security', 'apache']

app = None


class SSOApp(app_module.App):
    """FreedomBox app for single sign on."""
    app_id = 'sso'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, depends=depends,
                               name=_('Single Sign On'))
        self.add(info)

        packages = Packages('packages-sso', [
            'libapache2-mod-auth-pubtkt', 'openssl', 'python3-openssl', 'flite'
        ])
        self.add(packages)


def setup(helper, old_version=None):
    """Install the required packages"""
    app.setup(old_version)
    actions.superuser_run('auth-pubtkt', ['create-key-pair'])
