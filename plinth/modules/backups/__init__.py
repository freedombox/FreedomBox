# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to manage backup archives.
"""

import json
import logging
import os
import pathlib
import re

import paramiko
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import actions
from plinth import app as app_module
from plinth import cfg, glib, menu
from plinth.package import Packages

from . import api

logger = logging.getLogger(__name__)

_description = [
    _('Backups allows creating and managing backup archives.'),
]

MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'
# session variable name that stores when a backup file should be deleted
SESSION_PATH_VARIABLE = 'fbx-backups-upload-path'


class BackupsApp(app_module.App):
    """FreedomBox app for backup and restore."""

    app_id = 'backups'

    _version = 3

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, is_essential=True,
            depends=['storage'], name=_('Backups'), icon='fa-files-o',
            description=_description, manual_page='Backups',
            donation_url='https://www.borgbackup.org/support/fund.html')
        self.add(info)

        menu_item = menu.Menu('menu-backups', info.name, None, info.icon,
                              'backups:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-backups', ['borgbackup', 'sshfs'])
        self.add(packages)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        # Check every hour (every 3 minutes in debug mode) to perform scheduled
        # backups.
        interval = 180 if cfg.develop else 3600
        glib.schedule(interval, backup_by_schedule)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        from . import repository
        actions.superuser_run(
            'backups', ['setup', '--path', repository.RootBorgRepository.PATH])
        self.enable()

        # First time setup or upgrading from older versions.
        if old_version <= 2:
            _show_schedule_setup_notification()


def _backup_handler(packet, encryption_passphrase=None):
    """Performs backup operation on packet."""
    if not os.path.exists(MANIFESTS_FOLDER):
        os.makedirs(MANIFESTS_FOLDER)

    manifest_path = os.path.join(MANIFESTS_FOLDER,
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
    arguments = ['create-archive', '--path', packet.path]
    if packet.archive_comment:
        arguments += ['--comment', packet.archive_comment]

    arguments += ['--paths'] + paths
    input_data = ''
    if encryption_passphrase:
        input_data = json.dumps(
            {'encryption_passphrase': encryption_passphrase})

    actions.superuser_run('backups', arguments, input=input_data.encode())


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


def get_exported_archive_apps(path):
    """Get list of apps included in exported archive file."""
    arguments = ['get-exported-archive-apps', '--path', path]
    output = actions.superuser_run('backups', arguments)
    return output.splitlines()


def _restore_exported_archive_handler(packet, encryption_passphrase=None):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups',
                          ['restore-exported-archive', '--path', packet.path],
                          input=locations_data.encode())


def restore_archive_handler(packet, encryption_passphrase=None):
    """Perform restore operation on packet."""
    locations = {
        'directories': packet.directories,
        'files': packet.files,
        'encryption_passphrase': encryption_passphrase
    }
    locations_data = json.dumps(locations)
    arguments = [
        'restore-archive', '--path', packet.path, '--destination', '/'
    ]
    actions.superuser_run('backups', arguments, input=locations_data.encode())


def restore_from_upload(path, app_ids=None):
    """Restore files from an uploaded .tar.gz backup file"""
    api.restore_apps(_restore_exported_archive_handler, app_ids=app_ids,
                     create_subvolume=False, backup_file=path)


def get_known_hosts_path():
    """Return the path to the known hosts file."""
    return pathlib.Path(cfg.data_dir) / '.ssh' / 'known_hosts'


def is_ssh_hostkey_verified(hostname):
    """Check whether SSH Hostkey has already been verified.

    hostname: Domain name or IP address of the host

    """
    known_hosts_path = get_known_hosts_path()
    if not known_hosts_path.exists():
        return False

    known_hosts = paramiko.hostkeys.HostKeys(str(known_hosts_path))
    host_keys = known_hosts.lookup(hostname)
    return host_keys is not None


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
