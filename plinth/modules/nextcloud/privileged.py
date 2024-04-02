# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Nextcloud."""

import json
import pathlib
import random
import re
import shutil
import string
import subprocess
import time

import augeas

from plinth import action_utils
from plinth.actions import privileged

NETWORK_NAME = 'nextcloud-fbx'
BRIDGE_IP = '172.16.16.1'
CONTAINER_IP = '172.16.16.2'
CONTAINER_NAME = 'nextcloud-freedombox'
VOLUME_NAME = 'nextcloud-volume-freedombox'
IMAGE_NAME = 'docker.io/library/nextcloud:stable-apache'

DB_HOST = 'localhost'
DB_NAME = 'nextcloud_fbx'
DB_USER = 'nextcloud_fbx'
GUI_ADMIN = 'nextcloud-admin'

_volume_path = pathlib.Path(
    '/var/lib/containers/storage/volumes/') / VOLUME_NAME
_systemd_location = pathlib.Path('/etc/systemd/system/')
_cron_service_file = _systemd_location / 'nextcloud-cron-freedombox.service'
_cron_timer_file = _systemd_location / 'nextcloud-cron-freedombox.timer'

DB_BACKUP_FILE = pathlib.Path(
    '/var/lib/plinth/backups-data/nextcloud-database.sql')


@privileged
def setup():
    """Setup Nextcloud configuration."""
    database_password = _generate_secret_key(16)
    administrator_password = _generate_secret_key(16)

    # Setup database
    _create_database()
    _set_database_privileges(database_password)

    # Setup redis for caching
    _redis_listen_socket()
    _set_redis_password(_generate_secret_key(16))
    action_utils.service_restart('redis-server')

    action_utils.podman_run(
        network_name=NETWORK_NAME, subnet='172.16.16.0/24',
        bridge_ip=BRIDGE_IP, host_port='8181', container_port='80',
        container_ip=CONTAINER_IP, container_name=CONTAINER_NAME,
        image_name=IMAGE_NAME, extra_run_options=[
            '--volume=/run/mysqld/mysqld.sock:/run/mysqld/mysqld.sock',
            '--volume=/run/redis/redis-server.sock:'
            '/run/redis/redis-server.sock',
            f'--volume={VOLUME_NAME}:/var/www/html',
            f'--env=TRUSTED_PROXIES={BRIDGE_IP}',
            '--env=OVERWRITEWEBROOT=/nextcloud'
        ])
    _configure_firewall(action='add', interface_name=NETWORK_NAME)

    # OCC isn't immediately available after the container is spun up.
    # Wait until CAN_INSTALL file is available.
    timeout = 300
    while timeout > 0:
        if (_volume_path / '_data/config/CAN_INSTALL').exists():
            break

        timeout = timeout - 1
        time.sleep(1)

    _nextcloud_setup_wizard(database_password, administrator_password)
    _create_redis_config(_get_redis_password())

    _configure_ldap()

    _configure_systemd()


def _run_occ(*args, capture_output: bool = False,
             check: bool = True) -> subprocess.CompletedProcess:
    """Run the Nextcloud occ command inside the container."""
    occ = [
        'podman', 'exec', '--user', 'www-data', CONTAINER_NAME, 'php', 'occ'
    ] + list(args)
    return subprocess.run(occ, capture_output=capture_output, check=check)


@privileged
def get_domain():
    """Return domain name set in Nextcloud."""
    try:
        domain = _run_occ('config:system:get', 'overwritehost',
                          capture_output=True)
        return domain.stdout.decode().strip()
    except subprocess.CalledProcessError:
        return None


@privileged
def set_domain(domain_name: str):
    """Set Nextcloud domain name."""
    protocol = 'https'
    if domain_name.endswith('.onion'):
        protocol = 'http'

    if domain_name:
        _run_occ('config:system:set', 'overwritehost', '--value', domain_name)

        _run_occ('config:system:set', 'overwrite.cli.url', '--value',
                 f'{protocol}://{domain_name}/nextcloud')

        _run_occ('config:system:set', 'overwriteprotocol', '--value', protocol)

        # Restart to apply changes immediately
        action_utils.service_restart('nextcloud-freedombox')


@privileged
def set_admin_password(password: str):
    """Set password for owncloud-admin"""
    subprocess.run([
        'podman', 'exec', '--user', 'www-data', f'--env=OC_PASS={password}',
        '-it', CONTAINER_NAME, 'sh', '-c',
        ("/var/www/html/occ "
         f"user:resetpassword --password-from-env {GUI_ADMIN}")
    ], check=True)


@privileged
def get_default_phone_region():
    """"Get the value of default_phone_region."""
    try:
        default_phone_region = _run_occ('config:system:get',
                                        'default_phone_region',
                                        capture_output=True)
        return default_phone_region.stdout.decode().strip()
    except subprocess.CalledProcessError:
        return None


@privileged
def set_default_phone_region(region: str):
    """"Set the value of default_phone_region."""
    _run_occ('config:system:set', 'default_phone_region', '--value', region)


def _configure_firewall(action, interface_name):
    subprocess.run([
        'firewall-cmd', '--permanent', '--zone=trusted',
        f'--{action}-interface={interface_name}'
    ], check=True)
    action_utils.service_restart('firewalld')


def _database_query(query: str):
    """Run a database query."""
    subprocess.run(['mysql'], input=query.encode(), check=True)


def _create_database():
    """Create an empty MySQL database for Nextcloud."""
    # SQL injection is avoided due to known input.
    _db_file_path = pathlib.Path('/var/lib/mysql/nextcloud_fbx')
    if _db_file_path.exists():
        return

    query = f'''CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;
'''
    _database_query(query)


def _set_database_privileges(db_password: str):
    """Create user, set password and provide permissions on the database."""
    queries = [
        f"CREATE USER IF NOT EXISTS '{DB_USER}'@'localhost';",
        f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'localhost';",
        f"ALTER USER '{DB_USER}'@'localhost' IDENTIFIED BY '{db_password}';",
    ]
    for query in queries:
        _database_query(query)


def _nextcloud_get_status():
    """Return Nextcloud status such installed, in maintenance, etc."""
    output = _run_occ('status', '--output=json', capture_output=True)
    return json.loads(output.stdout)


def _nextcloud_setup_wizard(db_password, admin_password):
    """Run the Nextcloud installation wizard and enable cron jobs."""
    if not _nextcloud_get_status()['installed']:
        _run_occ('maintenance:install', '--database=mysql',
                 '--database-host=localhost:/run/mysqld/mysqld.sock',
                 f'--database-name={DB_NAME}', f'--database-user={DB_USER}',
                 f'--database-pass={db_password}', f'--admin-user={GUI_ADMIN}',
                 f'--admin-pass={admin_password}')

    # For the server to work properly, it's important to configure background
    # jobs correctly. Cron is the recommended setting.
    _run_occ('background:cron')


def _configure_ldap():
    _run_occ('app:enable', 'user_ldap')

    # Check if LDAP has already been configured. This is necessary because
    # if the setup proccess is rerun when updating the FredomBox app another
    # redundant LDAP config would be created.
    output = _run_occ('ldap:test-config', 's01', capture_output=True,
                      check=False)
    if 'Invalid configID' in output.stdout.decode():
        _run_occ('ldap:create-empty-config')

    ldap_settings = {
        'ldapBase': 'dc=thisbox',
        'ldapBaseGroups': 'dc=thisbox',
        'ldapBaseUsers': 'dc=thisbox',
        'ldapConfigurationActive': '1',
        'ldapGroupDisplayName': 'cn',
        'ldapGroupFilter': '(&(|(objectclass=posixGroup)))',
        'ldapGroupFilterMode': '0',
        'ldapGroupFilterObjectclass': 'posixGroup',
        'ldapGroupMemberAssocAttr': 'memberUid',
        'ldapHost': BRIDGE_IP,
        'ldapLoginFilter': '(&(|(objectclass=posixAccount))(uid=%uid))',
        'ldapLoginFilterEmail': '0',
        'ldapLoginFilterMode': '0',
        'ldapLoginFilterUsername': '1',
        'ldapNestedGroups': '0',
        'ldapPort': '389',
        'ldapTLS': '0',
        'ldapUserDisplayName': 'cn',
        'ldapUserFilter': '(|(objectclass=posixAccount))',
        'ldapUserFilterMode': '0',
        'ldapUserFilterObjectclass': 'account',
        'ldapUuidGroupAttribute': 'auto',
        'ldapUuidUserAttribute': 'auto',
        'turnOffCertCheck': '0',
        'turnOnPasswordChange': '0',
        'useMemberOfToDetectMembership': '0'
    }

    for key, value in ldap_settings.items():
        _run_occ('ldap:set-config', 's01', key, value)


def _configure_systemd():
    """Create systemd units files for container and cron jobs."""
    # Create service and timer for running periodic php jobs.
    nextcloud_cron_service_content = '''
[Unit]
Description=Nextcloud cron.php job

[Service]
ExecCondition=/usr/bin/podman exec --user www-data nextcloud-freedombox php occ status -e
ExecStart=/usr/bin/podman exec --user www-data nextcloud-freedombox php /var/www/html/cron.php
KillMode=process
'''  # noqa: E501
    nextcloud_cron_timer_content = '''[Unit]
Description=Run Nextcloud cron.php every 5 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Unit=nextcloud-cron-freedombox.service

[Install]
WantedBy=timers.target
'''
    _cron_service_file.write_text(nextcloud_cron_service_content)
    _cron_timer_file.write_text(nextcloud_cron_timer_content)

    action_utils.service_daemon_reload()


@privileged
def uninstall():
    """Uninstall Nextcloud"""
    _drop_database()
    _configure_firewall(action='remove', interface_name=NETWORK_NAME)
    action_utils.podman_uninstall(container_name=CONTAINER_NAME,
                                  network_name=NETWORK_NAME,
                                  volume_name=VOLUME_NAME,
                                  image_name=IMAGE_NAME)
    for path in [_cron_service_file, _cron_timer_file]:
        path.unlink(missing_ok=True)


def _drop_database():
    """Drop the database that was created during install."""
    with action_utils.service_ensure_running('mysql'):
        query = f'''DROP DATABASE IF EXISTS {DB_NAME};
    DROP USER IF EXISTS '{DB_USER}'@'localhost';'''
        _database_query(query)


def _generate_secret_key(length=64, chars=None):
    """Generate a new random secret key for use with Nextcloud."""
    chars = chars or (string.ascii_letters + string.digits)
    rand = random.SystemRandom()
    return ''.join(rand.choice(chars) for _ in range(length))


def _set_maintenance_mode(on: bool):
    """Turn maintenance mode on or off."""
    _run_occ('maintenance:mode', '--on' if on else '--off')


@privileged
def dump_database():
    """Dump database to file."""
    _set_maintenance_mode(True)
    DB_BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with action_utils.service_ensure_running('mysql'):
        with DB_BACKUP_FILE.open('w', encoding='utf-8') as file_handle:
            subprocess.run([
                'mysqldump', '--add-drop-database', '--add-drop-table',
                '--add-drop-trigger', '--single-transaction',
                '--default-character-set=utf8mb4', '--user', 'root',
                '--databases', DB_NAME
            ], stdout=file_handle, check=True)
    _set_maintenance_mode(False)


@privileged
def restore_database():
    """Restore database from file."""
    with action_utils.service_ensure_running('mysql'):
        with DB_BACKUP_FILE.open('r', encoding='utf-8') as file_handle:
            subprocess.run(['mysql', '--user', 'root'], stdin=file_handle,
                           check=True)

        _set_database_privileges(_get_dbpassword())

    action_utils.service_restart('redis-server')
    _set_maintenance_mode(False)

    # Attempts to update UUIDs of user and group entries. By default,
    # the command attempts to update UUIDs that have been invalidated by
    # a migration step.
    _run_occ('ldap:update-uuid')

    # Update the systems data-fingerprint after a backup is restored
    _run_occ('maintenance:data-fingerprint')


def _get_dbpassword():
    """Return the database password from config.php.

    OCC cannot run unless Nextcloud can already connect to the database.
    """
    config_file = _volume_path / '_data/config/config.php'
    with open(config_file, 'r', encoding='utf-8') as config:
        config_contents = config.read()

    pattern = r"'{}'\s*=>\s*'([^']*)'".format(re.escape('dbpassword'))
    match = re.search(pattern, config_contents)

    return match.group(1)


def _create_redis_config(password):
    """Create a php file for Redis configuration."""
    config_file = _volume_path / '_data/config/freedombox.config.php'
    file_content = f'''<?php
$CONFIG = [
'filelocking.enabled' => true,
'memcache.locking' => '\\\\OC\\\\Memcache\\\\Redis',
'memcache.distributed' => '\\\\OC\\\\Memcache\\\\Redis',
'redis' => [
    'host' => '/run/redis/redis-server.sock',
    'password' => '{password}',
    ],
];
'''
    config_file.write_text(file_content)
    shutil.chown(config_file, 'www-data', 'www-data')


def _load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    redis_config = '/etc/redis/redis.conf'
    aug.transform('Spacevars', redis_config)
    aug.set('/augeas/context', '/files' + redis_config)
    aug.load()
    return aug


def _redis_listen_socket():
    """Configure Redis to listen on a UNIX socket."""
    aug = _load_augeas()
    value = '/etc/redis/conf.d/*.conf'
    found = any((aug.get(match_) == value for match_ in aug.match('include')))
    if not found:
        aug.set('include[last() + 1]', value)

    aug.save()


def _set_redis_password(password: str):
    if _get_redis_password() is None:
        aug = _load_augeas()
        aug.set('requirepass', password)
        aug.save()


def _get_redis_password() -> str:
    aug = _load_augeas()
    return aug.get('requirepass')
