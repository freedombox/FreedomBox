# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Nextcloud."""

import os
import pathlib
import random
import re
import string
import subprocess
import time

from plinth import action_utils
from plinth.actions import privileged

NETWORK_NAME = 'nextcloud-fbx'
BRIDGE_IP = '172.16.16.1'
CONTAINER_IP = '172.16.16.2'
CONTAINER_NAME = 'nextcloud-fbx'
VOLUME_NAME = 'nextcloud-volume-fbx'
IMAGE_NAME = 'docker.io/library/nextcloud:stable-apache'

DB_HOST = 'localhost'
DB_NAME = 'nextcloud_fbx'
DB_USER = 'nextcloud_fbx'
GUI_ADMIN = 'nextcloud-admin'
SOCKET_CONFIG_FILE = pathlib.Path('/etc/mysql/mariadb.conf.d/'
                                  '99-freedombox.cnf')
SYSTEMD_LOCATION = '/etc/systemd/system/'
NEXTCLOUD_CONTAINER_SYSTEMD_FILE = pathlib.Path(
    f'{SYSTEMD_LOCATION}{CONTAINER_NAME}.service')
NEXTCLOUD_CRON_SERVICE_FILE = pathlib.Path(
    f'{SYSTEMD_LOCATION}nextcloud-cron-fbx.service')
NEXTCLOUD_CRON_TIMER_FILE = pathlib.Path(
    f'{SYSTEMD_LOCATION}nextcloud-cron-fbx.timer')

DB_BACKUP_FILE = pathlib.Path(
    '/var/lib/plinth/backups-data/nextcloud-database.sql')


@privileged
def setup():
    """Setup Nextcloud configuration."""
    database_password = _generate_secret_key(16)
    administrator_password = _generate_secret_key(16)
    _configure_db_socket()
    _configure_firewall(action='add', interface_name=NETWORK_NAME)
    _create_database(database_password)
    action_utils.podman_run(
        network_name=NETWORK_NAME, subnet='172.16.16.0/24',
        bridge_ip=BRIDGE_IP, host_port='8181', container_port='80',
        container_ip=CONTAINER_IP, volume_name=VOLUME_NAME,
        container_name=CONTAINER_NAME, image_name=IMAGE_NAME,
        extra_run_options=[
            '--env=TRUSTED_PROXIES={BRIDGE_IP}',
            '--env=OVERWRITEWEBROOT=/nextcloud'
        ])
    # OCC isn't immediately available after the container is spun up.
    # Wait until CAN_INSTALL file is available.
    timeout = 300
    while timeout > 0:
        if os.path.exists('/var/lib/containers/storage/volumes/'
                          'nextcloud-volume-fbx/_data/config/CAN_INSTALL'):
            break
        timeout = timeout - 1
        time.sleep(1)

    _nextcloud_setup_wizard(database_password, administrator_password)
    # Check if LDAP has already been configured. This is necessary because
    # if the setup proccess is rerun when updating the FredomBox app another
    # redundant LDAP config would be created.
    is_ldap_configured = _run_occ('ldap:test-config', 's01',
                                  capture_output=True)
    if is_ldap_configured != ('The configuration is valid and the connection '
                              'could be established!'):
        _configure_ldap()

    _configure_systemd()


def _run_occ(*args, capture_output: bool = False):
    """Run the Nextcloud occ command inside the container."""
    occ = [
        'podman', 'exec', '--user', 'www-data', CONTAINER_NAME, 'php', 'occ'
    ] + list(args)
    return subprocess.run(occ, capture_output=capture_output, check=False)


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
        action_utils.service_restart('nextcloud-fbx')


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


def _configure_db_socket():
    file_content = f'''## This file is automatically generated by FreedomBox
## Enable database to create a socket for podman's bridge network
[mysqld]
bind-address            = {BRIDGE_IP}
'''
    SOCKET_CONFIG_FILE.write_text(file_content, encoding='utf-8')
    action_utils.service_restart('mariadb')


def _create_database(db_password):
    """Create an empty MySQL database for Nextcloud."""
    # SQL injection is avoided due to known input.
    _db_file_path = pathlib.Path('/var/lib/mysql/nextcloud_fbx')
    if _db_file_path.exists():
        return

    query = f'''CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;
'''
    subprocess.run(['mysql', '--user', 'root'], input=query.encode(),
                   check=True)
    _set_db_privileges(db_password)


def _set_db_privileges(db_password):
    """Create user, set password and provide permissions on the database."""
    query = f'''GRANT ALL PRIVILEGES ON {DB_NAME}.* TO
  '{DB_USER}'@'{CONTAINER_IP}'
  IDENTIFIED BY'{db_password}';
FLUSH PRIVILEGES;
'''
    subprocess.run(['mysql', '--user', 'root'], input=query.encode(),
                   check=True)


def _nextcloud_setup_wizard(db_password, admin_password):
    admin_data_dir = pathlib.Path(
        '/var/lib/containers/storage/volumes/nextcloud-volume-fbx/'
        f'_data/data/{GUI_ADMIN}')
    if not admin_data_dir.exists():
        _run_occ('maintenance:install', '--database=mysql',
                 f'--database-name={DB_NAME}', f'--database-host={BRIDGE_IP}',
                 '--database-port=3306', f'--database-user={DB_USER}',
                 f'--database-pass={db_password}', f'--admin-user={GUI_ADMIN}',
                 f'--admin-pass={admin_password}')
    # For the server to work properly, it's important to configure background
    # jobs correctly. Cron is the recommended setting.
    _run_occ('background:cron')


def _configure_ldap():
    _run_occ('app:enable', 'user_ldap')
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
    systemd_content = subprocess.run(
        ['podman', 'generate', 'systemd', '--new', CONTAINER_NAME],
        capture_output=True, check=True).stdout.decode()
    # Create service and timer for running periodic php jobs.
    NEXTCLOUD_CONTAINER_SYSTEMD_FILE.write_text(systemd_content,
                                                encoding='utf-8')
    nextcloud_cron_service_content = '''
[Unit]
Description=Nextcloud cron.php job

[Service]
ExecCondition=/usr/bin/podman exec --user www-data nextcloud-fbx php occ status -e
ExecStart=/usr/bin/podman exec --user www-data nextcloud-fbx php /var/www/html/cron.php
KillMode=process
'''  # noqa: E501
    nextcloud_cron_timer_content = '''[Unit]
Description=Run Nextcloud cron.php every 5 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Unit=nextcloud-cron-fbx.service

[Install]
WantedBy=timers.target
'''
    NEXTCLOUD_CRON_SERVICE_FILE.write_text(nextcloud_cron_service_content)
    NEXTCLOUD_CRON_TIMER_FILE.write_text(nextcloud_cron_timer_content)
    action_utils.service_daemon_reload()


@privileged
def uninstall():
    """Uninstall Nextcloud"""
    _drop_database()
    _remove_db_socket()
    _configure_firewall(action='remove', interface_name=NETWORK_NAME)
    action_utils.podman_uninstall(container_name=CONTAINER_NAME,
                                  network_name=NETWORK_NAME,
                                  volume_name=VOLUME_NAME,
                                  image_name=IMAGE_NAME)
    files = [NEXTCLOUD_CRON_SERVICE_FILE, NEXTCLOUD_CRON_TIMER_FILE]
    for file in files:
        file.unlink(missing_ok=True)


def _remove_db_socket():
    SOCKET_CONFIG_FILE.unlink(missing_ok=True)
    action_utils.service_restart('mariadb')


def _drop_database():
    """Drop the mysql database that was created during install."""
    with action_utils.service_ensure_running('mysql'):
        query = f'''DROP DATABASE {DB_NAME};
    DROP User '{DB_USER}'@'{CONTAINER_IP}';'''
        subprocess.run(['mysql', '--user', 'root'], input=query.encode(),
                       check=True)


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

        _set_db_privileges(_get_dbpassword())

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
    config_file = ('/var/lib/containers/storage/volumes/nextcloud-volume-fbx'
                   '/_data/config/config.php')
    with open(config_file, 'r', encoding='utf-8') as config:
        config_contents = config.read()

    pattern = r"'{}'\s*=>\s*'([^']*)'".format(re.escape('dbpassword'))
    match = re.search(pattern, config_contents)

    return match.group(1)
