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
from plinth.actions import privileged, secret_str

CONTAINER_NAME = 'nextcloud-freedombox'
SERVICE_NAME = 'nextcloud-freedombox'
VOLUME_NAME = 'nextcloud-freedombox'
IMAGE_NAME = 'docker.io/library/nextcloud:stable-fpm'

DB_HOST = 'localhost'
DB_NAME = 'nextcloud_fbx'
DB_USER = 'nextcloud_fbx'
GUI_ADMIN = 'nextcloud-admin'
REDIS_DB = 8  # Don't clash with other redis apps

_data_path = pathlib.Path('/var/lib/nextcloud/')

DB_BACKUP_FILE = pathlib.Path(
    '/var/lib/plinth/backups-data/nextcloud-database.sql')


@privileged
def setup():
    """Setup Nextcloud configuration."""
    # Setup redis for caching
    _redis_listen_socket()

    volumes = {
        '/run/mysqld/mysqld.sock': '/run/mysqld/mysqld.sock',
        '/run/redis/redis-server.sock': '/run/redis/redis-server.sock',
        '/run/slapd/ldapi': '/run/slapd/ldapi',
        VOLUME_NAME: '/var/www/html'
    }
    env = {'OVERWRITEWEBROOT': '/nextcloud'}
    binds_to = ['mariadb.service', 'redis-server.service', 'slapd.service']
    action_utils.podman_create(container_name=CONTAINER_NAME,
                               image_name=IMAGE_NAME, volume_name=VOLUME_NAME,
                               volume_path=str(_data_path), volumes=volumes,
                               env=env, binds_to=binds_to)
    action_utils.service_start(CONTAINER_NAME)

    _nextcloud_wait_until_ready()

    # Setup database
    _create_database()
    database_password = _get_database_password()
    if not database_password:
        database_password = _generate_secret_key(16)
        _set_database_privileges(database_password)

    # Setup redis configuration
    _create_redis_config()

    # Run setup wizard
    _nextcloud_setup_wizard(database_password)

    # Setup LDAP configuraiton
    _configure_ldap()


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
def is_enabled() -> bool:
    """Return if the systemd container service is enabled."""
    return action_utils.podman_is_enabled(CONTAINER_NAME)


@privileged
def enable():
    """Enable the systemd container service."""
    action_utils.podman_enable(CONTAINER_NAME)


@privileged
def disable():
    """Disable the systemd container service."""
    action_utils.podman_disable(CONTAINER_NAME)


@privileged
def get_override_domain():
    """Return the domain name that Nextcloud is configured to override with."""
    try:
        domain = _run_occ('config:system:get', 'overwritehost',
                          capture_output=True)
        return domain.stdout.decode().strip()
    except subprocess.CalledProcessError:
        return None


@privileged
def set_override_domain(domain_name: str):
    """Set the domain name that Nextcloud will use to override all domains."""
    protocol = 'https'
    if domain_name.endswith('.onion'):
        protocol = 'http'

    if domain_name:
        _run_occ('config:system:set', 'overwritehost', '--value', domain_name)
        _run_occ('config:system:set', 'overwriteprotocol', '--value', protocol)
        _run_occ('config:system:set', 'overwrite.cli.url', '--value',
                 f'{protocol}://{domain_name}/nextcloud')
    else:
        _run_occ('config:system:delete', 'overwritehost')
        _run_occ('config:system:delete', 'overwriteprotocol')
        _run_occ('config:system:delete', 'overwrite.cli.url')

    # Restart to apply changes immediately
    action_utils.service_restart('nextcloud-freedombox')


@privileged
def set_trusted_domains(domains: list[str]):
    """Set the list of trusted domains."""
    _run_occ('config:system:delete', 'trusted_domains')
    for index, domain in enumerate(domains):
        _run_occ('config:system:set', 'trusted_domains', str(index), '--value',
                 domain)


@privileged
def set_admin_password(password: secret_str):
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

    query = f'CREATE DATABASE IF NOT EXISTS {DB_NAME} ' \
        'CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;'
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


def _nextcloud_wait_until_ready():
    """Wait for Nextcloud container to get ready."""
    # Nextcloud copies sources from /usr/src/nextcloud to /var/www/html inside
    # the container. Nextcloud is served from the latter location. This happens
    # on first run of the container and when upgrade happen.
    start_time = time.time()
    while time.time() < start_time + 300:
        if (_data_path / 'version.php').exists():
            break

        time.sleep(1)

    # Wait while Nextcloud is syncing files, running install or performing an
    # upgrade by trying to obtain an exclusive on its init-sync.lock. Wrap the
    # echo command with the lock so that the lock is immediately released after
    # obtaining. We are unable to obtain the lock for 5 minutes, fail and stop
    # the setup process.
    lock_file = _data_path / 'nextcloud-init-sync.lock'
    subprocess.run(
        ['flock', '--exclusive', '--wait', '300', lock_file, 'echo'],
        check=True)


def _nextcloud_get_status():
    """Return Nextcloud status such installed, in maintenance, etc."""
    output = _run_occ('status', '--output=json', capture_output=True)
    return json.loads(output.stdout)


def _nextcloud_setup_wizard(db_password: str):
    """Run the Nextcloud installation wizard and enable cron jobs."""
    if not _nextcloud_get_status()['installed']:
        admin_password = _generate_secret_key(16)
        _run_occ('maintenance:install', '--database=mysql',
                 '--database-host=localhost:/run/mysqld/mysqld.sock',
                 f'--database-name={DB_NAME}', f'--database-user={DB_USER}',
                 f'--database-pass={db_password}', f'--admin-user={GUI_ADMIN}',
                 f'--admin-pass={admin_password}')

    # For the server to work properly, it's important to configure background
    # jobs correctly. Cron is the recommended setting.
    _run_occ('background:cron')

    # Enable pretty URLs without /index.php in them.
    _run_occ('config:system:set', 'htaccess.RewriteBase', '--value',
             '/nextcloud')
    _run_occ('config:system:set', 'htaccess.IgnoreFrontController',
             '--type=boolean', '--value=true')
    # Update the .htaccess file to contain mod_rewrite rules needed for pretty
    # URLs. This is automatically re-run by scripts when upgrading to next
    # version.
    _run_occ('maintenance:update:htaccess')


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


@privileged
def uninstall():
    """Uninstall Nextcloud"""
    _drop_database()
    action_utils.podman_uninstall(container_name=CONTAINER_NAME,
                                  volume_name=VOLUME_NAME,
                                  image_name=IMAGE_NAME,
                                  volume_path=str(_data_path))


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

    _set_database_privileges(_get_database_password())

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


def _get_database_password():
    """Return the database password from config.php or '' if not set.

    OCC cannot run unless Nextcloud can already connect to the database.
    """
    code = 'if (file_exists("/var/www/html/config/config.php")) {' \
        'include_once("/var/www/html/config/config.php");' \
        'print($CONFIG["dbpassword"] ?? ""); }'
    return _run_in_container('php', '-r', code,
                             capture_output=True).stdout.decode().strip()


def _create_redis_config():
    """Create a php file for Redis configuration."""
    config_file = _data_path / 'config/freedombox.config.php'
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
