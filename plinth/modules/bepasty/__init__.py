# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for bepasty.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.firewall.components import Firewall

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_packages = ['bepasty', 'uwsgi', 'uwsgi-plugin-python3']

managed_services = ['uwsgi']

_description = [
    _('bepasty is a web application that allows large files to be uploaded '
      'and shared. Text and code snippets can also be pasted and shared. '
      'Text, image, audio, video and PDF documents can be previewed in the '
      'browser. Shared files can be set to expire after a time period.'),
    _('bepasty does not use usernames for login. It only uses passwords. For '
      'each password, a set of permissions can be selected. Once you have '
      'created a password, you can share it with the users who should have the'
      ' associated permissions.'),
    _('You can also create multiple passwords with the same set of privileges,'
      ' and distribute them to different people or groups. This will allow '
      'you to later revoke access for a single person or group, by removing '
      'their password from the list.'),
]

app = None

PERMISSIONS = {
    'read': _('Read a file, if a web link to the file is available'),
    'create': _('Create or upload files'),
    'list': _('List all files and their web links'),
    'delete': _('Delete files'),
    'admin': _('Administer files: lock/unlock files'),
}

DEFAULT_PERMISSIONS = {
    '': _('None, password is always required'),
    'read': _('Read a file, if a web link to the file is available'),
    'read list': _('List and read all files'),
}


class BepastyApp(app_module.App):
    """FreedomBox app for bepasty."""

    app_id = 'bepasty'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(self.app_id, version, name=_('bepasty'),
                               icon_filename='bepasty',
                               short_description=_('File & Snippet Sharing'),
                               description=_description, manual_page='bepasty',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-bepasty', info.name,
                              info.short_description, info.icon_filename,
                              'bepasty:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-bepasty', info.name,
                                      info.short_description,
                                      info.icon_filename, '/bepasty',
                                      clients=clients)
        self.add(shortcut)

        firewall = Firewall('firewall-bepasty', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        uwsgi = Uwsgi('uwsgi-bepasty', 'bepasty-freedombox')
        self.add(uwsgi)

        webserver = Webserver('webserver-bepasty', 'bepasty-freedombox',
                              urls=['https://{host}/bepasty/'])
        self.add(webserver)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'bepasty',
                ['setup', '--domain-name', 'freedombox.local'])
    helper.call('post', app.enable)
    if old_version == 1 and not get_configuration().get('DEFAULT_PERMISSIONS'):
        # Upgrade to a better default only if user hasn't changed the value.
        set_default_permissions('read')


def get_configuration():
    """Get a full configuration including passwords and defaults."""
    output = actions.superuser_run('bepasty', ['get-configuration'])
    return json.loads(output)


def add_password(permissions, comment=None):
    """Generate a password with given permissions."""
    command = ['add-password', '--permissions'] + permissions
    if comment:
        command += ['--comment', comment]

    actions.superuser_run('bepasty', command)


def remove_password(password):
    """Remove a password and its permissions."""
    actions.superuser_run('bepasty', ['remove-password'],
                          input=password.encode())


def set_default_permissions(permissions):
    """Set default permissions."""
    perm = permissions.split()
    actions.superuser_run('bepasty', ['set-default', '--permissions'] + perm)
