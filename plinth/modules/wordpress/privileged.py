# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for WordPress."""

import os
import pathlib
import random
import shutil
import string
import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged

_public_access_file = pathlib.Path('/etc/wordpress/is_public')
_config_file_path = pathlib.Path('/etc/wordpress/config-default.php')
_static_config_file_path = pathlib.Path('/etc/wordpress/freedombox-static.php')
_db_file_path = pathlib.Path('/etc/wordpress/database.php')
_db_backup_file = pathlib.Path(
    '/var/lib/plinth/backups-data/wordpress-database.sql')
DB_HOST = 'localhost'
DB_NAME = 'wordpress_fbx'
DB_USER = 'wordpress_fbx'


@privileged
def setup():
    """Create initial configuration and database for WordPress."""
    if _db_file_path.exists() or _config_file_path.exists():
        if _config_file_path.exists():
            _upgrade_config_file()

        return

    db_password = _generate_secret_key(16)

    _create_config_file(DB_HOST, DB_NAME, DB_USER, db_password)
    _create_database(DB_NAME)
    _set_privileges(DB_HOST, DB_NAME, DB_USER, db_password)


def _create_config_file(db_host, db_name, db_user, db_password):
    """Create a PHP configuration file included by WordPress."""
    secret_keys = [_generate_secret_key() for _ in range(8)]

    config_contents = f'''<?php
# Created by FreedomBox
include_once('{_static_config_file_path}');
include_once('{_db_file_path}');
define('DB_NAME', $dbname);
define('DB_USER', $dbuser);
define('DB_PASSWORD', $dbpass);
define('DB_HOST', $dbserver);

define('AUTH_KEY', '{secret_keys[0]}');
define('SECURE_AUTH_KEY', '{secret_keys[1]}');
define('LOGGED_IN_KEY', '{secret_keys[2]}');
define('NONCE_KEY', '{secret_keys[3]}');
define('AUTH_SALT', '{secret_keys[4]}');
define('SECURE_AUTH_SALT', '{secret_keys[5]}');
define('LOGGED_IN_SALT', '{secret_keys[6]}');
define('NONCE_SALT', '{secret_keys[7]}');

define('WP_CONTENT_DIR', '/var/lib/wordpress/wp-content');

define('DISABLE_WP_CRON', true);
'''
    _config_file_path.write_text(config_contents, encoding='utf-8')

    db_contents = f'''<?php
# Created by FreedomBox
$dbuser='{db_user}';
$dbpass='{db_password}';
$dbname='{db_name}';
$dbserver='{db_host}';
'''
    old_umask = os.umask(0o037)
    try:
        _db_file_path.write_text(db_contents, encoding='utf-8')
    finally:
        os.umask(old_umask)

    shutil.chown(_db_file_path, group='www-data')


def _create_database(db_name):
    """Create an empty MySQL database for WordPress."""
    # Wordpress' install.php creates the tables.
    # SQL injection is avoided due to known input.
    query = f'''CREATE DATABASE {db_name};'''
    subprocess.run(['mysql', '--user', 'root'], input=query.encode(),
                   check=True)


def _set_privileges(db_host, db_name, db_user, db_password):
    """Create user, set password and provide permissions on the database."""
    # SQL injection is avoided due to known input.
    query = f'''GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,ALTER
  ON {db_name}.*
  TO {db_user}@{db_host}
  IDENTIFIED BY '{db_password}';
FLUSH PRIVILEGES;
'''
    subprocess.run(['mysql', '--user', 'root'], input=query.encode(),
                   check=True)


def _generate_secret_key(length=64, chars=None):
    """Generate a new random secret key for use with WordPress."""
    chars = chars or (string.ascii_letters + string.digits +
                      '!@#$%^&*()-_ []{}<>~`+=,.:/?|')
    rand = random.SystemRandom()
    return ''.join(rand.choice(chars) for _ in range(length))


def _upgrade_config_file():
    """Upgrade existing config file to add changes."""
    include_line = f"include_once('{_static_config_file_path}');"
    lines = _config_file_path.read_text(encoding='utf-8').splitlines()
    if include_line not in lines:
        lines.insert(2, include_line)  # Insert on 3rd line
        _config_file_path.write_text('\n'.join(lines), encoding='utf-8')


@privileged
def set_public(enable: bool):
    """Allow/disallow public access."""
    if enable:
        _public_access_file.touch()
    else:
        _public_access_file.unlink(missing_ok=True)

    action_utils.service_reload('apache2')


def is_public() -> bool:
    """Return whether public access is enabled."""
    return _public_access_file.exists()


@privileged
def dump_database():
    """Dump database to file."""
    _db_backup_file.parent.mkdir(parents=True, exist_ok=True)
    with _db_backup_file.open('w', encoding='utf-8') as file_handle:
        subprocess.run([
            'mysqldump', '--add-drop-database', '--add-drop-table',
            '--add-drop-trigger', '--user', 'root', '--databases', DB_NAME
        ], stdout=file_handle, check=True)


@privileged
def restore_database():
    """Restore database from file."""
    with _db_backup_file.open('r', encoding='utf-8') as file_handle:
        subprocess.run(['mysql', '--user', 'root'], stdin=file_handle,
                       check=True)

    _set_privileges(DB_HOST, DB_NAME, DB_USER, _read_db_password())


def _read_db_password():
    """Return the password stored in the DB configuration file."""
    aug = _load_augeas()
    return aug.get('./$dbpass').strip('\'"')


def _load_augeas():
    """Initialize augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Phpvars', str(_db_file_path))
    aug.set('/augeas/context', '/files' + str(_db_file_path))
    aug.load()

    return aug


@privileged
def uninstall():
    """Remove config files and drop database."""
    _drop_database()
    for file_ in [_public_access_file, _config_file_path, _db_file_path]:
        file_.unlink(missing_ok=True)


def _drop_database():
    """Drop the mysql database that was created during install."""
    query = f'''DROP DATABASE {DB_NAME};'''
    subprocess.run(['mysql', '--user', 'root'], input=query.encode(),
                   check=True)
