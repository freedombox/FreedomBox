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

import collections

from plinth import actions, action_utils, module_loader


def validate(backup):
    """Validate the backup' information schema."""
    assert isinstance(backup, dict)

    assert 'config' in backup
    assert isinstance(backup['config'], dict)
    _validate_directories_and_files(backup['config'])

    assert 'data' in backup
    assert isinstance(backup['data'], dict)
    _validate_directories_and_files(backup['data'])

    assert 'secrets' in backup
    assert isinstance(backup['secrets'], dict)
    _validate_directories_and_files(backup['secrets'])

    assert 'services' in backup
    assert isinstance(backup['services'], list)

    return backup


def _validate_directories_and_files(df):
    """Validate directories and files structure."""
    assert 'directories' in df
    assert isinstance(df['directories'], list)
    assert 'files' in df
    assert isinstance(df['files'], list)


class Packet:
    """Information passed to a handlers for backup/restore operations."""

    def __init__(self, operation, scope, root, manifests=None, label=None):
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
        self.manifests = manifests
        self.label = label

        self.directories = []
        self.files = []
        if scope == 'apps':
            self._process_manifests()

    def _process_manifests(self):
        """Look at manifests and fill up the list of directories/files."""
        for manifest in self.manifests:
            backup = manifest[2]
            for x in ['config', 'data', 'secrets']:
                self.directories += backup[x]['directories']
                self.files += backup[x]['files']


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
        apps = _list_of_all_apps_for_backup()
    else:
        apps = _get_apps_in_order(app_names)

    manifests = _get_manifests(apps)

    if _is_snapshot_available():
        snapshot = _take_snapshot()
        backup_root = snapshot['mount_path']
        snapshotted = True
    else:
        _lockdown_apps(apps, lockdown=True)
        original_state = _shutdown_services(manifests)
        backup_root = '/'
        snapshotted = False

    packet = Packet('backup', 'apps', backup_root, manifests, label)
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
        apps = _list_of_all_apps_for_backup()
    else:
        apps = _get_apps_in_order(app_names)

    manifests = _get_manifests(apps)

    if _is_snapshot_available() and create_subvolume:
        subvolume = _create_subvolume(empty=False)
        restore_root = subvolume['mount_path']
        subvolume = True
    else:
        _lockdown_apps(apps, lockdown=True)
        original_state = _shutdown_services(manifests)
        restore_root = '/'
        subvolume = False

    packet = Packet('restore', 'apps', restore_root, manifests, backup_file)
    _run_operation(restore_handler, packet)

    if subvolume:
        _switch_to_subvolume(subvolume)
    else:
        _restore_services(original_state)
        _lockdown_apps(apps, lockdown=False)


def _list_of_all_apps_for_backup():
    """Return a list of all applications that can be backed up."""
    apps = []
    for module_name, module in module_loader.loaded_modules.items():
        # Not installed
        if module.setup_helper.get_state() == 'needs-setup':
            continue

        # Has no backup related meta data
        if not hasattr(module, 'backup'):
            continue

        apps.append((module_name, module))

    return apps


def _get_apps_in_order(app_names):
    """Return a list of app modules in order of dependency."""
    apps = []
    for module_name, module in module_loader.loaded_modules.items():
        if module_name in app_names:
            apps.append((module_name, module))

    return apps


def _get_manifests(apps):
    """Return a dictionary of apps' backup manifest data.

    Maintain the application order in returned data.
    """
    manifests = []
    for app_name, app in apps:
        try:
            manifests.append((app_name, app, app.backup))
        except AttributeError:
            pass

    return manifests


def _lockdown_apps(apps, lockdown):
    """Mark apps as in/out of lockdown mode and disable all user interaction.

    This is a flag in the app module. It will enforced by a middleware that
    will intercept all interaction and show a lockdown message.

    """
    for _, app in apps:
        app.locked = lockdown

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


def _shutdown_services(manifests):
    """Shutdown all services specified by manifests.

    - Services are shutdown in the reverse order of the apps listing.

    Return the current state of the services so they can be restored
    accurately.
    """
    state = collections.OrderedDict()
    for app_name, app, manifest in manifests:
        for service in manifest.get('services', []):
            if service not in state:
                state[service] = {'app_name': app_name, 'app': app}

    for service in state:
        state[service]['was_running'] = action_utils.service_is_running(
            service)

    for service in reversed(state):
        if state[service]['was_running']:
            actions.superuser_run('service', ['stop', service])

    return state


def _restore_services(original_state):
    """Re-run services to restore them to their initial state.

    Maintain exact order of services so dependencies are satisfied.
    """
    for service in original_state:
        if original_state[service]['was_running']:
            actions.superuser_run('service', ['start', service])


def _run_operation(handler, packet):
    """Run handler and pre/post hooks for backup/restore operations."""
    handler(packet)
