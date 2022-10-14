# SPDX-License-Identifier: AGPL-3.0-or-later
"""
API for performing backup and restore.

Backups can be full disk backups or backup of individual applications.

TODO:
- Implement snapshots by calling to snapshots module.
- Handles errors during backup and service start/stop.
- Implement unit tests.
"""

import logging

from plinth import action_utils
from plinth import app as app_module
from plinth import setup
from plinth.modules.apache import privileged as apache_privileged
from plinth.privileged import service as service_privileged

from .components import BackupRestore

logger = logging.getLogger(__name__)


class BackupError:
    """Represent an backup/restore operation error."""

    def __init__(self, error_type, component, hook=None):
        """Initialize the error object."""
        self.error_type = error_type
        self.component = component
        self.hook = hook

    def __eq__(self, other_error):
        """Compare to error objects."""
        return (self.error_type == other_error.error_type
                and self.component == other_error.component
                and self.hook == other_error.hook)


class Packet:
    """Information passed to a handlers for backup/restore operations."""

    def __init__(self, operation, scope, root, components=None, path=None,
                 archive_comment=None):
        """Initialize the packet.

        operation is either 'backup' or 'restore.

        scope is either 'full' for full backups/restores or 'apps' for
        application specific operations.

        manifests are used to build file/directory lists if scope is 'apps'.
        All paths populated are relative to the 'root' path. The root path
        itself must not be stored in the backup.

        path is the full path of an (possibly exported) archive.
        TODO: create two variables out of it as it's distinct information.

        """
        self.operation = operation
        self.scope = scope
        self.root = root
        self.components = components
        self.path = path
        self.archive_comment = archive_comment
        self.errors = []

        self.directories = []
        self.files = []
        if scope == 'apps':
            self._process_manifests()

    def _process_manifests(self):
        """Look at manifests and fill up the list of directories/files."""
        for component in self.components:
            for section in ['config', 'data', 'secrets']:
                section = getattr(component, section)
                self.directories += section.get('directories', [])
                self.files += section.get('files', [])


def backup_full(backup_handler, path=None):
    """Backup the entire system."""
    if not _is_snapshot_available():
        raise Exception('Full backup is not supported without snapshots.')

    snapshot = _take_snapshot()
    backup_root = snapshot['mount_path']

    packet = Packet('backup', 'full', backup_root, path)
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


def backup_apps(backup_handler, path, app_ids=None, encryption_passphrase=None,
                archive_comment=None):
    """Backup data belonging to a set of applications."""
    if not app_ids:
        components = get_all_components_for_backup()
    else:
        components = get_components_in_order(app_ids)

    if _is_snapshot_available():
        snapshot = _take_snapshot()
        backup_root = snapshot['mount_path']
        snapshotted = True
    else:
        _lockdown_apps(components, lockdown=True)
        original_state = _shutdown_services(components)
        backup_root = '/'
        snapshotted = False

    packet = Packet('backup', 'apps', backup_root, components, path,
                    archive_comment)
    _run_operation(backup_handler, packet,
                   encryption_passphrase=encryption_passphrase)

    if snapshotted:
        _delete_snapshot(snapshot)
    else:
        _restore_services(original_state)
        _lockdown_apps(components, lockdown=False)


def restore_apps(restore_handler, app_ids=None, create_subvolume=True,
                 backup_file=None, encryption_passphrase=None):
    """Restore data belonging to a set of applications."""
    if not app_ids:
        components = get_all_components_for_backup()
    else:
        components = get_components_in_order(app_ids)

    _install_apps_before_restore(components)

    if _is_snapshot_available() and create_subvolume:
        subvolume = _create_subvolume(empty=False)
        restore_root = subvolume['mount_path']
    else:
        _lockdown_apps(components, lockdown=True)
        original_state = _shutdown_services(components)
        restore_root = '/'
        subvolume = False

    packet = Packet('restore', 'apps', restore_root, components, backup_file)
    _run_operation(restore_handler, packet,
                   encryption_passphrase=encryption_passphrase)

    if subvolume:
        _switch_to_subvolume(subvolume)
    else:
        _restore_services(original_state)
        _lockdown_apps(components, lockdown=False)


def _install_apps_before_restore(components):
    """Install/upgrade apps needed before restoring a backup.

    Upgrading apps to latest version before backups reduces the chance of newer
    data getting backed up into older version of the app.

    """
    apps_to_setup = []
    for component in components:
        if component.app.get_setup_state() in (
                app_module.App.SetupState.NEEDS_SETUP,
                app_module.App.SetupState.NEEDS_UPDATE):
            apps_to_setup.append(component.app.app_id)

    setup.run_setup_on_apps(apps_to_setup)


def _get_backup_restore_component(app):
    """Return the backup/restore component of the app."""
    for component in app.components.values():
        if isinstance(component, BackupRestore):
            return component

    raise TypeError


def get_all_components_for_backup():
    """Return a list of all components that can be backed up."""
    components = []

    for app_ in app_module.App.list():
        try:
            if not app_.needs_setup():
                components.append(_get_backup_restore_component(app_))
        except TypeError:  # Application not available for backup/restore
            pass

    return components


def get_components_in_order(app_ids):
    """Return a list of backup components in order of app dependencies."""
    components = []
    for app_ in app_module.App.list():
        if app_.app_id in app_ids:
            components.append(_get_backup_restore_component(app_))

    return components


def _lockdown_apps(components, lockdown):
    """Mark apps as in/out of lockdown mode and disable all user interaction.

    This is a flag in the app module. It will enforced by a middleware that
    will intercept all interaction and show a lockdown message.

    """
    for component in components:
        component.app.locked = lockdown


def _is_snapshot_available():
    """Return whether it is possible to take filesystem snapshots."""


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
    """Handle starting and stopping of system services for backup."""

    def __init__(self, backup_app, service):
        """Initialize the object."""
        super().__init__(backup_app, service)
        self.was_running = None

    def stop(self):
        """Stop the service."""
        self.was_running = action_utils.service_is_running(self.service)
        if self.was_running:
            service_privileged.stop(self.service)

    def restart(self):
        """Restart the service if it was earlier running."""
        if self.was_running:
            service_privileged.start(self.service)


class ApacheServiceHandler(ServiceHandler):
    """Handle starting and stopping of Apache services for backup."""

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
            apache_privileged.disable(self.web_name, self.kind)

    def restart(self):
        """Restart the service if it was earlier running."""
        if self.was_enabled:
            apache_privileged.enable(self.web_name, self.kind)


def _shutdown_services(components):
    """Shutdown all services specified by backup manifests.

    - Services are shutdown in the reverse order of the components listing.

    Return the current state of the services so they can be restored
    accurately.

    """
    state = []
    for component in components:
        for service in component.services:
            state.append(ServiceHandler.create(component, service))

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
    for component in packet.components:
        try:
            getattr(component, hook)(packet)
        except Exception as exception:
            logger.exception(
                'Error running backup/restore hook for app %s: %s',
                component.app.app_id, exception)
            packet.errors.append(BackupError('hook', component, hook=hook))


def _run_operation(handler, packet, encryption_passphrase=None):
    """Run handler and pre/post hooks for backup/restore operations."""
    _run_hooks(packet.operation + '_pre', packet)
    handler(packet, encryption_passphrase=encryption_passphrase)
    _run_hooks(packet.operation + '_post', packet)
