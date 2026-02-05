# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to manage backup archives."""

import contextlib
import json
import logging
import os
import re
import subprocess
from pathlib import Path

from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import cfg, glib, menu
from plinth.package import Packages

from . import api, errors, manifest, privileged

logger = logging.getLogger(__name__)

_description = [
    _('Backups allows creating and managing backup archives.'),
]

# session variable name that stores when a backup file should be deleted
SESSION_PATH_VARIABLE = 'fbx-backups-upload-path'


class BackupsApp(app_module.App):
    """FreedomBox app for backup and restore."""

    app_id = 'backups'

    _version = 4

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, is_essential=True,
            depends=['storage'], name=_('Backups'), icon='fa-files-o',
            description=_description, manual_page='Backups',
            donation_url='https://www.borgbackup.org/support/fund.html',
            tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-backups', info.name, info.icon, info.tags,
                              'backups:index', parent_url_name='system:data',
                              order=20)
        self.add(menu_item)

        packages = Packages('packages-backups',
                            ['borgbackup', 'sshfs', 'sshpass'])
        self.add(packages)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        # Check every hour to perform scheduled backups
        glib.schedule(3600, backup_by_schedule)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        from . import repository
        privileged.setup(repository.RootBorgRepository.PATH)
        self.enable()

        # First time setup or upgrading from older versions.
        if old_version <= 2:
            _show_schedule_setup_notification()


def _backup_handler(packet, encryption_passphrase=None):
    """Perform backup operation on packet."""
    if not os.path.exists(privileged.MANIFESTS_FOLDER):
        os.makedirs(privileged.MANIFESTS_FOLDER)

    manifest_path = os.path.join(privileged.MANIFESTS_FOLDER,
                                 get_valid_filename(packet.path) + '.json')
    manifests = {
        'apps': [{
            'name': component.app.app_id,
            'version': component.app.info.version,
            'backup': component.manifest
        } for component in packet.components]
    }
    with open(manifest_path, 'w', encoding='utf-8') as manifest_file:
        json.dump(manifests, manifest_file)

    paths = packet.directories + packet.files
    paths.append(manifest_path)

    privileged.create_archive(packet.path, paths,
                              comment=packet.archive_comment,
                              encryption_passphrase=encryption_passphrase)


def backup_by_schedule(data):
    """Check if backups need to be taken and run the operation."""
    from . import repository as repository_module
    for repository in repository_module.get_repositories():
        try:
            repository.schedule.run_schedule()
            _show_schedule_error_notification(repository, is_error=False)
        except Exception as exception:
            logger.exception('Error running scheduled backup: %s', exception)
            _show_schedule_error_notification(repository, is_error=True,
                                              exception=exception)


def _restore_exported_archive_handler(packet, encryption_passphrase=None):
    """Perform restore operation on packet."""
    privileged.restore_exported_archive(packet.path, packet.directories,
                                        packet.files)


def restore_archive_handler(packet, encryption_passphrase=None):
    """Perform restore operation on packet."""
    privileged.restore_archive(packet.path, '/', packet.directories,
                               packet.files, encryption_passphrase)


def restore_from_upload(path, app_ids=None):
    """Restore files from an uploaded .tar.gz backup file"""
    api.restore_apps(_restore_exported_archive_handler, app_ids=app_ids,
                     create_subvolume=False, backup_file=path)


def get_known_hosts_path() -> Path:
    """Return the path to the known hosts file."""
    return Path(cfg.data_dir) / '.ssh' / 'known_hosts'


def get_ssh_client_auth_key_paths() -> tuple[Path, Path]:
    """Return the paths to the SSH client public key and private key."""
    key_path = Path(cfg.data_dir) / '.ssh' / 'id_ed25519'
    pubkey_path = key_path.with_suffix('.pub')
    return pubkey_path, key_path


def generate_ssh_client_auth_key():
    """Generate SSH client authentication keypair, if needed."""
    _, key_path = get_ssh_client_auth_key_paths()
    if not key_path.exists():
        logger.info('Generating SSH client key %s for FreedomBox service',
                    key_path)
        subprocess.run(
            ['ssh-keygen', '-t', 'ed25519', '-N', '', '-f',
             str(key_path)], stdout=subprocess.DEVNULL, check=True)
    else:
        logger.info('SSH client key %s for FreedomBox service already exists',
                    key_path)


def get_ssh_client_public_key() -> str:
    """Get SSH client public key for FreedomBox service."""
    pubkey_path, _ = get_ssh_client_auth_key_paths()
    with pubkey_path.open('r') as pubkey_file:
        pubkey = pubkey_file.read()

    return pubkey


def copy_ssh_client_public_key(pubkey_path: str, hostname: str, username: str,
                               password: str):
    """Copy the SSH client public key to the remote server.

    Returns whether the copy was successful, and any error message.
    """
    pubkey_path, _ = get_ssh_client_auth_key_paths()
    env = os.environ.copy()
    env['SSHPASS'] = str(password)
    with raise_ssh_error():
        try:
            subprocess.run([
                'sshpass', '-e', 'ssh-copy-id', '-i',
                str(pubkey_path), f'{username}@{hostname}'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                           env=env)
            logger.info("Copied SSH client public key to remote host's "
                        "authorized keys.")
        except subprocess.CalledProcessError as exception:
            logger.warning('Failed to copy SSH client public key: %s',
                           exception.stderr)
            raise


@contextlib.contextmanager
def raise_ssh_error() -> None:
    """Convert subprocess error to SshError."""
    try:
        yield
    except subprocess.CalledProcessError as exception:
        raise errors.SshError(exception.returncode, exception.cmd,
                              exception.output, exception.stderr)


def is_ssh_hostkey_verified(hostname):
    """Check whether SSH Hostkey has already been verified.

    hostname: Domain name or IP address of the host

    """
    known_hosts_path = get_known_hosts_path()
    if not known_hosts_path.exists():
        return False

    try:
        subprocess.run(
            ['ssh-keygen', '-F', hostname, '-f',
             str(known_hosts_path)], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def split_path(path):
    """Splits the given path into username, hostname, directory.

    Network interface information is kept in the hostname if provided.
    e.g. fe80::2078:6c26:498a:1fa5%wlp1s0

    """
    return re.findall(r'^(.*)@([^/]*):(.*)$', path)[0]


def _show_schedule_setup_notification():
    """Show a notification hinting to setup a remote backup schedule."""
    from plinth.notification import Notification
    message = gettext_noop(
        'Enable an automatic backup schedule for data safety. Prefer an '
        'encrypted remote backup location or an extra attached disk.')
    data = {
        'app_name': 'translate:' + gettext_noop('Backups'),
        'app_icon': 'fa-files-o'
    }
    title = gettext_noop('Enable a Backup Schedule')
    actions_ = [{
        'type': 'link',
        'class': 'primary',
        'text': gettext_noop('Go to {app_name}'),
        'url': 'backups:index'
    }, {
        'type': 'dismiss'
    }]
    Notification.update_or_create(id='backups-remote-schedule',
                                  app_id='backups', severity='info',
                                  title=title, message=message,
                                  actions=actions_, data=data, group='admin')


def on_schedule_save(repository):
    """Dismiss notification. Called when repository's schedule is updated."""
    if not repository.schedule.enabled:
        return

    from plinth.notification import Notification
    try:
        note = Notification.get('backups-remote-schedule')
        note.dismiss()
    except KeyError:
        pass


def _show_schedule_error_notification(repository, is_error, exception=None):
    """Show or hide a notification related scheduled backup operation."""
    from plinth.notification import Notification
    id_ = 'backups-schedule-error-' + repository.uuid
    try:
        note = Notification.get(id_)
        error_count = note.data['error_count']
    except KeyError:
        error_count = 0

    message = gettext_noop(
        'A scheduled backup failed. Past {error_count} attempts for backup '
        'did not succeed. The latest error is: {error_message}')
    data = {
        'app_name': 'translate:' + gettext_noop('Backups'),
        'app_icon': 'fa-files-o',
        'error_count': error_count + 1 if is_error else 0,
        'error_message': str(exception)
    }
    title = gettext_noop('Error During Backup')
    actions_ = [{
        'type': 'link',
        'class': 'primary',
        'text': gettext_noop('Go to {app_name}'),
        'url': 'backups:index'
    }, {
        'type': 'dismiss'
    }]
    note = Notification.update_or_create(id=id_, app_id='backups',
                                         severity='error', title=title,
                                         message=message, actions=actions_,
                                         data=data, group='admin')
    note.dismiss(should_dismiss=not is_error)
