# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Nextcloud."""

import contextlib
import json
import pathlib
import secrets
import shutil
import string
import subprocess
import time

import augeas

from plinth import action_utils
from plinth.actions import privileged

CONTAINER_NAME = 'nextcloud-freedombox'
SERVICE_NAME = 'nextcloud-freedombox'
VOLUME_NAME = 'nextcloud-volume-freedombox'
IMAGE_NAME = 'docker.io/library/nextcloud:stable-apache'

DB_HOST = 'localhost'
DB_NAME = 'nextcloud_fbx'
DB_USER = 'nextcloud_fbx'
GUI_ADMIN = 'nextcloud-admin'
REDIS_DB = 8  # Don't clash with other redis apps

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

    volumes = {
        '/run/mysqld/mysqld.sock': '/run/mysqld/mysqld.sock',
        '/run/redis/redis-server.sock': '/run/redis/redis-server.sock',
        '/run/slapd/ldapi': '/run/slapd/ldapi',
        VOLUME_NAME: '/var/www/html'
    }
    env = {'TRUSTED_PROXIES': '127.0.0.1', 'OVERWRITEWEBROOT': '/nextcloud'}
    action_utils.podman_create(container_name=CONTAINER_NAME,
                               image_name=IMAGE_NAME, volumes=volumes, env=env)
    action_utils.service_start(CONTAINER_NAME)

    # OCC isn't immediately available after the container is spun up.
    # Wait until CAN_INSTALL file is available.
    timeout = 300
    while timeout > 0:
        if (_volume_path / '_data/config/CAN_INSTALL').exists():
            break

        timeout = timeout - 1
        time.sleep(1)

    _nextcloud_setup_wizard(database_password, administrator_password)
    _create_redis_config()

    _configure_ldap()

    _configure_systemd()


def _run_in_container(
        *args, capture_output: bool = False, check: bool = True,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run a command inside the container."""
    env_args = [f'--env={key}={value}' for key, value in (env or {}).items()]
    command = ['podman', 'exec', '--user', 'www-data'
               ] + env_args + [CONTAINER_NAME] + list(args)
    return subprocess.run(command, capture_output=capture_output, check=check)


def _run_occ(*args, **kwargs) -> subprocess.CompletedProcess:
    """Run the Nextcloud occ command inside the container."""
    return _run_in_container('/var/www/html/occ', *args, **kwargs)


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
    _run_occ('user:resetpassword', '--password-from-env', GUI_ADMIN,
             env={'OC_PASS': password})


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
        'ldapHost': 'ldapi:///',
        'ldapLoginFilter': '(&(|(objectclass=posixAccount))(uid=%uid))',
        'ldapLoginFilterEmail': '0',
        'ldapLoginFilterMode': '0',
        'ldapLoginFilterUsername': '1',
        'ldapNestedGroups': '0',
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
    doc = 'https://docs.nextcloud.com/server/stable/admin_manual/' \
        'configuration_server/background_jobs_configuration.html#systemd'
    nextcloud_cron_service_content = f'''
[Unit]
Description=Nextcloud cron.php job
Documentation={doc}

[Service]
ExecCondition=/usr/bin/podman exec --user www-data {CONTAINER_NAME} /var/www/html/occ status -e
ExecStart=/usr/bin/podman exec --user www-data {CONTAINER_NAME} php -f /var/www/html/cron.php
KillMode=process
'''  # noqa: E501
    nextcloud_cron_timer_content = '''[Unit]
Description=Run Nextcloud cron.php every 5 minutes
Documentation={doc}

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
    action_utils.podman_uninstall(container_name=CONTAINER_NAME,
                                  volume_name=VOLUME_NAME,
                                  image_name=IMAGE_NAME)
    for path in [_cron_service_file, _cron_timer_file]:
        path.unlink(missing_ok=True)


def _drop_database():
    """Drop the database that was created during install."""
    with action_utils.service_ensure_running('mysql'):
        _database_query(f'DROP DATABASE IF EXISTS {DB_NAME};')
        _database_query(f"DROP USER IF EXISTS '{DB_USER}'@'localhost';")


def _generate_secret_key(length=64, chars=None):
    """Generate a new random secret key for use with Nextcloud."""
    chars = chars or (string.ascii_letters + string.digits)
    return ''.join(secrets.choice(chars) for _ in range(length))


def _set_maintenance_mode(on: bool):
    """Turn maintenance mode on or off."""
    _run_occ('maintenance:mode', '--on' if on else '--off')


@contextlib.contextmanager
def _maintenance_mode():
    """Context to set maintenance mode temporarily."""
    try:
        _set_maintenance_mode(True)
        yield
    finally:
        _set_maintenance_mode(False)


@privileged
def dump_database():
    """Dump database to file."""
    DB_BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _maintenance_mode():
        with DB_BACKUP_FILE.open('w', encoding='utf-8') as file_handle:
            subprocess.run([
                'mysqldump', '--add-drop-database', '--add-drop-table',
                '--add-drop-trigger', '--single-transaction',
                '--default-character-set=utf8mb4', '--user', 'root',
                '--databases', DB_NAME
            ], stdout=file_handle, check=True)


@privileged
def restore_database():
    """Restore database from file."""
    with DB_BACKUP_FILE.open('r', encoding='utf-8') as file_handle:
        subprocess.run(['mysql', '--user', 'root'], stdin=file_handle,
                       check=True)

    subprocess.run(['redis-cli', '-n',
                    str(REDIS_DB), 'FLUSHDB', 'SYNC'], check=False)

    _set_database_privileges(_get_dbpassword())

    # After updating the configuration, a restart seems to be required for the
    # new DB password be used.
    action_utils.service_try_restart(SERVICE_NAME)

    _set_maintenance_mode(False)

    # Attempts to update UUIDs of user and group entries. By default, the
    # command attempts to update UUIDs that have been invalidated by a
    # migration step.
    _run_occ('ldap:update-uuid')

    # Update the systems data-fingerprint after a backup is restored.
    _run_occ('maintenance:data-fingerprint')


def _get_dbpassword():
    """Return the database password from config.php.

    OCC cannot run unless Nextcloud can already connect to the database.
    """
    code = 'include_once("/var/www/html/config/config.php");' \
        'print($CONFIG["dbpassword"]);'
    return _run_in_container('php', '-r', code,
                             capture_output=True).stdout.decode().strip()


def _create_redis_config():
    """Create a php file for Redis configuration."""
    config_file = _volume_path / '_data/config/freedombox.config.php'
    file_content = fr'''<?php
$CONFIG = [
'memcache.distributed' => '\OC\Memcache\Redis',
'memcache.locking' => '\OC\Memcache\Redis',
'redis' => ['host' => '/run/redis/redis-server.sock', 'dbindex' => {REDIS_DB}],
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
        action_utils.service_restart('redis-server')
