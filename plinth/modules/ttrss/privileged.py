# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Tiny Tiny RSS."""

import os
import subprocess
from typing import Optional

import augeas

from plinth import action_utils
from plinth.actions import privileged

CONFIG_FILE = '/etc/tt-rss/config.php'
DEFAULT_FILE = '/etc/default/tt-rss'
DATABASE_FILE = '/etc/tt-rss/database.php'
DB_BACKUP_FILE = '/var/lib/plinth/backups-data/ttrss-database.sql'


@privileged
def pre_setup():
    """Preseed debconf values before packages are installed."""
    action_utils.debconf_set_selections(
        ['tt-rss tt-rss/database-type string pgsql'])


@privileged
def get_domain() -> Optional[str]:
    """Get the domain set for Tiny Tiny RSS."""
    aug = load_augeas()

    from urllib.parse import urlparse
    for match in aug.match('/files' + CONFIG_FILE + '/define'):
        if aug.get(match) == 'SELF_URL_PATH':
            url = aug.get(match + '/value').strip("'")
            return urlparse(url).netloc

    return None


@privileged
def set_domain(domain_name: Optional[str]):
    """Set the domain to be used by Tiny Tiny RSS."""
    if not domain_name:
        return

    url = f"'https://{domain_name}/tt-rss/'"
    aug = load_augeas()

    for match in aug.match('/files' + CONFIG_FILE + '/define'):
        if aug.get(match) == 'SELF_URL_PATH':
            aug.set(match + '/value', url)

    aug.save()


@privileged
def setup():
    """Setup Tiny Tiny RSS configuration."""
    aug = load_augeas()

    aug.set('/files' + DEFAULT_FILE + '/DISABLED', '0')

    skip_self_url_path_exists = False

    for match in aug.match('/files' + CONFIG_FILE + '/define'):
        if aug.get(match) == 'PLUGINS':
            aug.set(match + '/value', "'auth_remote, note'")
        elif aug.get(match) == '_SKIP_SELF_URL_PATH_CHECKS':
            skip_self_url_path_exists = True
            aug.set(match + '/value', 'true')

    if not skip_self_url_path_exists:
        aug.set('/files' + CONFIG_FILE + '/define[last() + 1]',
                '_SKIP_SELF_URL_PATH_CHECKS')
        aug.set('/files' + CONFIG_FILE + '/define[last()]/value', 'true')

    aug.save()

    if action_utils.service_is_enabled('tt-rss'):
        action_utils.service_restart('tt-rss')


@privileged
def enable_api_access():
    """Enable API access so that tt-rss can be accessed through mobile app."""
    import psycopg2  # Only available post installation

    aug = load_augeas()

    def get_value(variable_name):
        """Return the value of a variable from database configuration file."""
        return aug.get('/files' + DATABASE_FILE + '/$' + variable_name) \
            .strip("'\"")

    user = get_value('dbuser')
    password = get_value('dbpass')
    database = get_value('dbname')
    host = get_value('dbserver')

    connection = psycopg2.connect(database=database, user=user,
                                  password=password, host=host)
    cursor = connection.cursor()

    cursor.execute("UPDATE ttrss_prefs SET def_value=true "
                   "WHERE pref_name='ENABLE_API_ACCESS';")

    connection.commit()
    connection.close()


@privileged
def dump_database():
    """Dump database to file."""
    os.makedirs(os.path.dirname(DB_BACKUP_FILE), exist_ok=True)
    with open(DB_BACKUP_FILE, 'w', encoding='utf-8') as db_backup_file:
        _run_as_postgres(['pg_dump', 'ttrss'], stdout=db_backup_file)


@privileged
def restore_database():
    """Restore database from file."""
    _run_as_postgres(['dropdb', 'ttrss'])
    _run_as_postgres(['createdb', 'ttrss'])
    with open(DB_BACKUP_FILE, 'r', encoding='utf-8') as db_restore_file:
        _run_as_postgres(['psql', '--dbname', 'ttrss'], stdin=db_restore_file)


def _run_as_postgres(command, stdin=None, stdout=None):
    """Run a command as postgres user."""
    command = ['sudo', '--user', 'postgres'] + command
    subprocess.run(command, stdin=stdin, stdout=stdout, check=True)


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', DEFAULT_FILE)
    aug.set('/augeas/load/Phpvars/lens', 'Phpvars.lns')
    aug.set('/augeas/load/Phpvars/incl[last() + 1]', CONFIG_FILE)
    aug.set('/augeas/load/Phpvars/incl[last() + 1]', DATABASE_FILE)
    aug.load()
    return aug