# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Tiny Tiny RSS."""

import os
import subprocess

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
    action_utils.debconf_set_selections([
        'tt-rss tt-rss/database-type string pgsql',
        'tt-rss tt-rss/purge boolean true',
        'tt-rss tt-rss/dbconfig-remove boolean true',
        'tt-rss tt-rss/dbconfig-reinstall boolean true'
    ])


@privileged
def get_domain() -> str | None:
    """Get the domain set for Tiny Tiny RSS."""
    aug = load_augeas()

    from urllib.parse import urlparse
    for match in aug.match('/files' + CONFIG_FILE + '/define'):
        if aug.get(match) == 'SELF_URL_PATH':
            url = aug.get(match + '/value').strip("'")
            return urlparse(url).netloc

    return None


@privileged
def set_domain(domain_name: str | None):
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


def _get_database_config():
    """Return the database configuration."""
    aug = load_augeas()

    def _get_value(variable_name):
        """Return the value of a variable from database configuration file."""
        return aug.get('/files' + DATABASE_FILE + '/$' + variable_name) \
            .strip("'\"")

    return {
        'user': _get_value('dbuser'),
        'password': _get_value('dbpass'),
        'database': _get_value('dbname'),
        'host': _get_value('dbserver')
    }


@privileged
def enable_api_access():
    """Enable API access so that tt-rss can be accessed through mobile app."""
    import psycopg2  # Only available post installation

    config = _get_database_config()

    connection = psycopg2.connect(database=config['database'],
                                  user=config['user'],
                                  password=config['password'],
                                  host=config['host'])
    cursor = connection.cursor()

    cursor.execute("UPDATE ttrss_prefs SET def_value=true "
                   "WHERE pref_name='ENABLE_API_ACCESS';")

    connection.commit()
    connection.close()


@privileged
def dump_database():
    """Dump database to file."""
    config = _get_database_config()
    os.makedirs(os.path.dirname(DB_BACKUP_FILE), exist_ok=True)
    with open(DB_BACKUP_FILE, 'w', encoding='utf-8') as db_backup_file:
        process = _run_as_postgres(['pg_dumpall', '--roles-only'],
                                   stdout=subprocess.PIPE)
        db_backup_file.write(f'DROP ROLE IF EXISTS {config["user"]};\n')
        for line in process.stdout.decode().splitlines():
            if config['user'] in line:
                db_backup_file.write(line + '\n')

    with open(DB_BACKUP_FILE, 'a', encoding='utf-8') as db_backup_file:
        _run_as_postgres([
            'pg_dump', '--create', '--clean', '--if-exists', config['database']
        ], stdout=db_backup_file)


@privileged
def restore_database():
    """Restore database from file."""
    config = _get_database_config()

    # This is needed for old backups only. New backups include 'DROP DATABASE
    # IF EXISTS' and 'CREATE DATABASE' statements.
    _run_as_postgres(['dropdb', config['database']])
    _run_as_postgres(['createdb', config['database']])

    with open(DB_BACKUP_FILE, 'r', encoding='utf-8') as db_restore_file:
        _run_as_postgres(['psql', '--dbname', config['database']],
                         stdin=db_restore_file)


def _run_as_postgres(command, stdin=None, stdout=None):
    """Run a command as postgres user."""
    command = ['sudo', '--user', 'postgres'] + command
    return subprocess.run(command, stdin=stdin, stdout=stdout, check=True)


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
