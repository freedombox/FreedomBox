# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for Zoph server."""

import configparser
import os
import re
import subprocess

from plinth import action_utils
from plinth.actions import privileged

APACHE_CONF = '/etc/apache2/conf-available/zoph.conf'
DB_BACKUP_FILE = '/var/lib/plinth/backups-data/zoph-database.sql'


@privileged
def pre_install():
    """Preseed debconf values before packages are installed."""
    action_utils.debconf_set_selections([
        'zoph zoph/dbconfig-install boolean true',
        'zoph zoph/mysql/admin-user string root'
    ])


@privileged
def get_configuration() -> dict[str, str]:
    """Return the current configuration."""
    configuration = {}
    process = subprocess.run(['zoph', '--dump-config'], stdout=subprocess.PIPE,
                             check=True)
    for line in process.stdout.decode().splitlines():
        name, value = line.partition(':')[::2]
        configuration[name.strip()] = value[1:]

    return configuration


def _zoph_configure(key, value):
    """Set a configure value in Zoph."""
    subprocess.run(['zoph', '--config', key, value], check=True)


@privileged
def setup():
    """Setup Zoph configuration.

    May be called when app is disabled.
    """
    with action_utils.service_ensure_running('mysql'):
        _zoph_configure('import.enable', 'true')
        _zoph_configure('import.upload', 'true')
        _zoph_configure('import.rotate', 'true')
        _zoph_configure('path.unzip', 'unzip')
        _zoph_configure('path.untar', 'tar xvf')
        _zoph_configure('path.ungz', 'gunzip')

        # Maps using OpenStreetMap is enabled by default.
        _zoph_configure('maps.provider', 'osm')


def _get_db_name():
    """Return the name of the database configured by dbconfig."""
    config = configparser.ConfigParser()
    with open('/etc/zoph.ini', 'r', encoding='utf-8') as file_handle:
        config.read_file(file_handle)

    return config['zoph']['db_name'].strip('"')


@privileged
def set_configuration(enable_osm: bool | None = None,
                      admin_user: str | None = None):
    """Setup Zoph Apache configuration."""
    _zoph_configure('interface.user.remote', 'true')

    # Note that using OpenSteetmap as a mapping provider is a very nice
    # feature, but some people may regard its use as a privacy issue
    if enable_osm is not None:
        value = 'osm' if enable_osm else ''
        _zoph_configure('maps.provider', value)

    if admin_user:
        # Edit the database to rename the admin user to FreedomBox admin user.
        if not re.match(r'^[\w.@][\w.@-]+\Z', admin_user, flags=re.ASCII):
            # Check to avoid SQL injection
            raise ValueError('Invalid username')

        query = f"UPDATE zoph_users SET user_name='{admin_user}' \
                 WHERE user_name='admin';"

        subprocess.run(['mysql', _get_db_name()], input=query.encode(),
                       check=True)


@privileged
def is_configured() -> bool | None:
    """Return whether zoph app is configured."""
    process = subprocess.run(['zoph', '--get-config', 'interface.user.remote'],
                             stdout=subprocess.PIPE, check=True)
    return process.stdout.decode().strip() == 'true'


@privileged
def dump_database():
    """Dump database to file."""
    db_name = _get_db_name()
    os.makedirs(os.path.dirname(DB_BACKUP_FILE), exist_ok=True)
    with open(DB_BACKUP_FILE, 'w', encoding='utf-8') as db_backup_file:
        subprocess.run(['mysqldump', db_name], stdout=db_backup_file,
                       check=True)


@privileged
def restore_database():
    """Restore database from file."""
    db_name = _get_db_name()
    subprocess.run(['mysqladmin', '--force', 'drop', db_name], check=False)
    subprocess.run(['mysqladmin', 'create', db_name], check=True)
    with open(DB_BACKUP_FILE, 'r', encoding='utf-8') as db_restore_file:
        subprocess.run(['mysql', db_name], stdin=db_restore_file, check=True)
