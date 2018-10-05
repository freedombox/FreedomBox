#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
API for performing backup and restore.

Backups can be full disk backups or backup of individual applications.

TODO:
- Implement snapshots by calling to snapshots module.
- Handles errors during backup and service start/stop.
- Implement unit tests.
"""

import logging

from plinth import actions, action_utils, module_loader

logger = logging.getLogger(__name__)


def validate(backup):
    """Validate the backup' information schema."""
    assert isinstance(backup, dict)

    if 'config' in backup:
        assert isinstance(backup['config'], dict)
        _validate_directories_and_files(backup['config'])

    if 'data' in backup:
        assert isinstance(backup['data'], dict)
        _validate_directories_and_files(backup['data'])

    if 'secrets' in backup:
        assert isinstance(backup['secrets'], dict)
        _validate_directories_and_files(backup['secrets'])

    if 'services' in backup:
        assert isinstance(backup['services'], list)
        for service in backup['services']:
            assert isinstance(service, (str, dict))
            if isinstance(service, dict):
                _validate_service(service)

    return backup


def _validate_directories_and_files(section):
    """Validate directories and files keys in a section."""
    if 'directories' in section:
        assert isinstance(section['directories'], list)
        for directory in section['directories']:
            assert isinstance(directory, str)

    if 'files' in section:
        assert isinstance(section['files'], list)
        for file_path in section['files']:
            assert isinstance(file_path, str)


def _validate_service(service):
    """Validate a service manifest provided as a dictionary."""
    assert isinstance(service['name'], str)
    assert isinstance(service['type'], str)
    assert service['type'] in ('apache', 'uwsgi', 'system')
    if service['type'] == 'apache':
        assert service['kind'] in ('config', 'site', 'module')


class BackupError:
    """Represent an backup/restore operation error."""
    def __init__(self, error_type, app, hook=None):
        """Initialize the error object."""
        self.error_type = error_type
        self.app = app
        self.hook = hook

    def __eq__(self, other_error):
        """Compare to error objects."""
        return (self.error_type == other_error.error_type and
                self.app == other_error.app and
                self.hook == other_error.hook)


class Packet:
    """Information passed to a handlers for backup/restore operations."""

    def __init__(self, operation, scope, root, apps=None, label=None):
        """Initialize the packet.

        operation is either 'backup' or 'restore.

        scope is either 'full' for full backups/restores or 'apps' for
        application specific operations.

        manifests are used to build file/directory lists if scope is 'apps'.
        All paths populated are relative to the 'root' path. The root path
        itself must not be stored in the backup.

        """
        self.operation = operation
        self.scope = scope
        self.root = root
        self.apps = apps
        # TODO: label is an archive path -- rename
        self.label = label
        self.errors = []

        self.directories = []
        self.files = []
        if scope == 'apps':
            self._process_manifests()

    def _process_manifests(self):
        """Look at manifests and fill up the list of directories/files."""
        for app in self.apps:
            for section in ['config', 'data', 'secrets']:
                self.directories += app.manifest.get(section, {}).get(
                    'directories', [])
                self.files += app.manifest.get(section, {}).get('files', [])


def backup_full(backup_handler, label=None):
    """Backup the entire system."""
    if not _is_snapshot_available():
        raise Exception('Full backup is not supported without snapshots.')

    snapshot = _take_snapshot()
    backup_root = snapshot['mount_path']

    packet = Packet('backup', 'full', backup_root, label)
    _run_operation(backup_handler, packet)

    _delete_snapshot(snapshot)


def restore_full(restore_handler):
    """Restore the entire system."""
    if not _is_snapshot_available():
        raise Exception('Full restore is not supported without snapshots.')

    subvolume = _create_subvolume(empty=True)
    restore_root = subvolume['mount_path']

    packet = Packet('restore', 'full', restore_root)
    _run_operation(restore_handler, packet)
    _switch_to_subvolume(subvolume)


def backup_apps(backup_handler, app_names=None, label=None):
    """Backup data belonging to a set of applications."""
    if not app_names:
        apps = get_all_apps_for_backup()
    else:
        apps = _get_apps_in_order(app_names)

    if _is_snapshot_available():
        snapshot = _take_snapshot()
        backup_root = snapshot['mount_path']
        snapshotted = True
    else:
        _lockdown_apps(apps, lockdown=True)
        original_state = _shutdown_services(apps)
        backup_root = '/'
        snapshotted = False

    packet = Packet('backup', 'apps', backup_root, apps, label)
    _run_operation(backup_handler, packet)

    if snapshotted:
        _delete_snapshot(snapshot)
    else:
        _restore_services(original_state)
        _lockdown_apps(apps, lockdown=False)


def restore_apps(restore_handler, app_names=None, create_subvolume=True,
                 backup_file=None):
    """Restore data belonging to a set of applications."""
    if not app_names:
        apps = get_all_apps_for_backup()
    else:
        apps = _get_apps_in_order(app_names)

    if _is_snapshot_available() and create_subvolume:
        subvolume = _create_subvolume(empty=False)
        restore_root = subvolume['mount_path']
        subvolume = True
    else:
        _lockdown_apps(apps, lockdown=True)
        original_state = _shutdown_services(apps)
        restore_root = '/'
        subvolume = False

    packet = Packet('restore', 'apps', restore_root, apps, backup_file)
    _run_operation(restore_handler, packet)

    if subvolume:
        _switch_to_subvolume(subvolume)
    else:
        _restore_services(original_state)
        _lockdown_apps(apps, lockdown=False)


class BackupApp:
    """A application that can be backed up and its manifest."""

    def __init__(self, name, app):
        """Initialize object and load manfiest."""
        self.name = name
        self.app = app

        # Not installed
        if app.setup_helper.get_state() == 'needs-setup':
            raise TypeError

        # Has no backup related meta data
        try:
            self.manifest = app.backup
        except AttributeError:
            raise TypeError

        self.has_data = bool(app.backup)

    def __eq__(self, other_app):
        """Check if this app is same as another."""
        return self.name == other_app.name and \
            self.app == other_app.app and \
            self.manifest == other_app.manifest and \
            self.has_data == other_app.has_data

    def run_hook(self, hook, packet):
        """Run a hook inside an application."""
        if not hasattr(self.app, hook):
            return

        try:
            getattr(self.app, hook)(packet)
        except Exception as exception:
            logger.exception(
                'Error running backup/restore hook for app %s: %s', self.name,
                exception)
            packet.errors.append(BackupError('hook', self.app, hook=hook))


def get_all_apps_for_backup():
    """Return a list of all applications that can be backed up."""
    apps = []
    for module_name, module in module_loader.loaded_modules.items():
        try:
            apps.append(BackupApp(module_name, module))
        except TypeError:  # Application not available for backup/restore
            pass

    return apps


def _get_apps_in_order(app_names):
    """Return a list of app modules in order of dependency."""
    apps = []
    for module_name, module in module_loader.loaded_modules.items():
        if module_name in app_names:
            apps.append(BackupApp(module_name, module))

    return apps


def _lockdown_apps(apps, lockdown):
    """Mark apps as in/out of lockdown mode and disable all user interaction.

    This is a flag in the app module. It will enforced by a middleware that
    will intercept all interaction and show a lockdown message.

    """
    for app in apps:
        app.app.locked = lockdown

    # XXX: Lockdown the application UI by implementing a middleware


def _is_snapshot_available():
    """Return whether it is possible to take filesystem snapshots."""
    pass


def _take_snapshot():
    """Take a snapshot of the entire filesystem.

    - Snapshot must be read-only.
    - Mount the snapshot and make it available for backup.

    Return information dictionary about snapshot including 'mount_path', the
    mount point of the snapshot and any other information necessary to delete
    the snapshot later.

    """
    raise NotImplementedError


def _create_subvolume(empty=True):
    """Create a new subvolume for restore files to.

    - If empty is true, create an empty subvolume. Otherwise, create a
    read-write snapshot of the current root.
    - Mount the subvolume read/write and make it available for restore.

    Return information dictionary about subvolume created including
    'mount_path', the mount point of the subvolume and any other information
    necessary to switch to this subvolume later.

    """
    raise NotImplementedError


def _delete_snapshot(snapshot):
    """Delete a snapshot given information captured when snapshot was taken."""
    raise NotImplementedError


def _switch_to_subvolume(subvolume):
    """Make the provided subvolume the default subvolume to mount."""
    raise NotImplementedError


class ServiceHandler:
    """Abstraction to help with service shutdown/restart."""

    @staticmethod
    def create(backup_app, service):
        service_type = 'system'
        if isinstance(service, dict):
            service_type = service['type']

        service_map = {
            'system': SystemServiceHandler,
            'apache': ApacheServiceHandler,
        }
        assert service_type in service_map
        return service_map[service_type](backup_app, service)

    def __init__(self, backup_app, service):
        """Initialize the object."""
        self.backup_app = backup_app
        self.service = service

    def stop(self):
        """Stop the service."""
        raise NotImplementedError

    def restart(self):
        """Stop the service."""
        raise NotImplementedError

    def __eq__(self, other_handler):
        """Compare that two handlers are the same."""
        return self.backup_app == other_handler.backup_app and \
            self.service == other_handler.service


class SystemServiceHandler(ServiceHandler):
    """Handle starting and stoping of system services for backup."""

    def __init__(self, backup_app, service):
        """Initialize the object."""
        super().__init__(backup_app, service)
        self.was_running = None

    def stop(self):
        """Stop the service."""
        self.was_running = action_utils.service_is_running(self.service)
        if self.was_running:
            actions.superuser_run('service', ['stop', self.service])

    def restart(self):
        """Restart the service if it was earlier running."""
        if self.was_running:
            actions.superuser_run('service', ['start', self.service])


class ApacheServiceHandler(ServiceHandler):
    """Handle starting and stoping of Apache services for backup."""

    def __init__(self, backup_app, service):
        """Initialize the object."""
        super().__init__(backup_app, service)
        self.was_enabled = None
        self.web_name = service['name']
        self.kind = service['kind']

    def stop(self):
        """Stop the service."""
        self.was_enabled = action_utils.webserver_is_enabled(
            self.web_name, kind=self.kind)
        if self.was_enabled:
            actions.superuser_run(
                'apache',
                ['disable', '--name', self.web_name, '--kind', self.kind])

    def restart(self):
        """Restart the service if it was earlier running."""
        if self.was_enabled:
            actions.superuser_run(
                'apache',
                ['enable', '--name', self.web_name, '--kind', self.kind])


def _shutdown_services(apps):
    """Shutdown all services specified by manifests.

    - Services are shutdown in the reverse order of the apps listing.

    Return the current state of the services so they can be restored
    accurately.
    """
    state = []
    for app in apps:
        for service in app.manifest.get('services', []):
            state.append(ServiceHandler.create(app, service))

    for service in reversed(state):
        service.stop()

    return state


def _restore_services(original_state):
    """Re-run services to restore them to their initial state.

    Maintain exact order of services so dependencies are satisfied.
    """
    for service_handler in original_state:
        service_handler.restart()


def _run_hooks(hook, packet):
    """Run pre/post operation hooks in applications.

    Using the manifest mechanism, applications will convey to the backups
    framework how they needs to be backed up. Using this declarative approach
    reduces the burden of implementation on behalf of the applications.
    However, not all backup necessities may be satisfied in this manner no
    matter how feature rich the framework. So, applications should have the
    ability to customize the backup/restore processes suiting to their needs.

    For this, each application may optionally implement methods (hooks) that
    will be called during the backup or restore process. If these methods are
    named appropriately, the backups API will automatically call the methods
    and there is no need to register the methods.

    The following hooks are currently available for implementation:

    - backup_pre(packet):
      Called before the backup process starts for the application.
    - backup_post(packet):
      Called after the backup process has completed for the application.
    - restore_pre(packet):
      Called before the restore process starts for the application.
    - restore_post(packet):
      Called after the restore process has completed for the application.

    """
    logger.info('Running %s hooks', hook)
    for app in packet.apps:
        app.run_hook(hook, packet)


def _run_operation(handler, packet):
    """Run handler and pre/post hooks for backup/restore operations."""
    _run_hooks(packet.operation + '_pre', packet)
    handler(packet)
    _run_hooks(packet.operation + '_post', packet)
