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

version = 1

managed_packages = ['bepasty', 'uwsgi', 'uwsgi-plugin-python3']

managed_services = ['uwsgi']

description = [
    _('bepasty is a web application that allows all types of files to be '
      'uploaded and shared.'),
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
    'read': _('Read files (using their web address)'),
    'create': _('Create or upload files'),
    'list': _('List all files'),
    'delete': _('Delete files'),
    'admin': _('Admin (lock/unlock files)'),
}


class BepastyApp(app_module.App):
    """FreedomBox app for bepasty."""

    app_id = 'bepasty'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(self.app_id, version, name=_('bepasty'),
                               icon_filename='bepasty',
                               short_description=_('File Sharing'),
                               description=description, manual_page='bepasty',
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

        webserver = Webserver('webserver-bepasty', 'bepasty-freedombox')
        self.add(webserver)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'bepasty',
                ['setup', '--domain-name', 'freedombox.local'])
    helper.call('post', app.enable)


def list_passwords():
    """Get a list of passwords, their permissions and comments"""
    output = actions.superuser_run('bepasty', ['list-passwords'])
    return json.loads(output)


def add_password(permissions=None, comment=None):
    """Generate a password with given permissions"""
    command = ['add-password']
    if permissions:
        command += ['--permissions'] + permissions

    if comment:
        command += ['--comment', comment]

    actions.superuser_run('bepasty', command)


def remove_password(password):
    """Remove a password and its permissions"""
    actions.superuser_run('bepasty',
                          ['remove-password', '--password', password])
