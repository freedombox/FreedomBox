# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for bepasty."""

import collections
import json
import pathlib
import secrets
import shutil
import string

import augeas

from plinth import action_utils
from plinth.actions import privileged, secret_str
from plinth.modules import bepasty

CONF_FILE = pathlib.Path('/etc/bepasty-freedombox.conf')
DATA_DIR = '/var/lib/private/bepasty'
PASSWORD_LENGTH = 20
SERVICE_NAME = 'uwsgi-app@bepasty-freedombox.service'


def _augeas_load():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Simplevars/lens', 'Simplevars.lns')
    aug.set('/augeas/load/Simplevars/incl[last() + 1]', str(CONF_FILE))
    aug.load()
    return aug


def _key_path(key):
    """Return the augeas path for the key."""
    return '/files' + str(CONF_FILE) + '/' + key


def conf_file_read():
    """Read and return the configuration."""
    aug = _augeas_load()
    conf = collections.OrderedDict()
    for path in aug.match(_key_path('*')):
        key = path.rsplit('/', 1)[-1]
        if key[0] != '#':
            conf[key] = json.loads(aug.get(path))

    return conf


def conf_file_write(conf):
    """Write configuration to the file."""
    aug = _augeas_load()
    for key, value in conf.items():
        if not key.startswith('#'):
            value = json.dumps(value)

        aug.set(_key_path(key), value)

    aug.save()


@privileged
def setup(domain_name: str):
    """Post installation actions for bepasty."""
    # Create configuration file if needed.
    if not CONF_FILE.is_file():
        passwords = [_generate_password() for _ in range(3)]
        conf = {
            '#comment':
                'This file is managed by FreedomBox. Only a small subset of '
                'the original configuration format is supported. Each line '
                'should be in KEY = VALUE format. VALUE must be a JSON '
                'encoded string.',
            'SITENAME': domain_name,
            'STORAGE_FILESYSTEM_DIRECTORY': '/var/lib/bepasty',
            'SECRET_KEY': secrets.token_hex(64),
            'PERMISSIONS': {
                passwords[0]: 'admin,list,create,read,delete',
                passwords[1]: 'list,create,read,delete',
                passwords[2]: 'list,read',
            },
            'PERMISSION_COMMENTS': {
                passwords[0]: 'admin',
                passwords[1]: 'editor',
                passwords[2]: 'viewer',
            },
            'DEFAULT_PERMISSIONS': 'read',
        }
        conf_file_write(conf)
        CONF_FILE.chmod(0o640)

    # Migrate from old bepasty:bepasty ownership to root:root
    shutil.chown(CONF_FILE, user='root', group='root')
    action_utils.run(['deluser', 'bepasty'], check=False)
    action_utils.run(['delgroup', 'bepasty'], check=False)


@privileged
def get_configuration() -> dict[str, object]:
    """Get default permissions, passwords, permissions and comments."""
    return conf_file_read()


@privileged
def add_password(permissions: list[str], comment: str | None = None):
    """Generate a password with given permissions."""
    conf = conf_file_read()
    permissions = _format_permissions(permissions)
    password = _generate_password()
    conf['PERMISSIONS'][password] = permissions
    if comment:
        conf['PERMISSION_COMMENTS'][password] = comment

    conf_file_write(conf)
    # Service is started again by socket.
    action_utils.service_stop(SERVICE_NAME)


@privileged
def remove_password(password: secret_str):
    """Remove a password and its permissions."""
    conf = conf_file_read()
    if password in conf['PERMISSIONS']:
        del conf['PERMISSIONS'][password]

    if password in conf['PERMISSION_COMMENTS']:
        del conf['PERMISSION_COMMENTS'][password]
    conf_file_write(conf)
    action_utils.service_stop(SERVICE_NAME)


@privileged
def set_default(permissions: list[str]):
    """Set default permissions."""
    conf = {'DEFAULT_PERMISSIONS': _format_permissions(permissions)}
    conf_file_write(conf)
    action_utils.service_stop(SERVICE_NAME)


def _format_permissions(permissions=None):
    """Format permissions as comma-separated."""
    return ','.join(set(bepasty.PERMISSIONS.keys()).intersection(
        permissions)) if permissions else ''


def _generate_password():
    """Generate a random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(PASSWORD_LENGTH))


@privileged
def uninstall():
    """Remove bepasty user, group and data."""
    shutil.rmtree(DATA_DIR, ignore_errors=True)
    CONF_FILE.unlink(missing_ok=True)
