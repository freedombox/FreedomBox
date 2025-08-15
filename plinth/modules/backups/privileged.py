# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure backups (with borg) and sshfs."""

import functools
import json
import os
import pathlib
import re
import shutil
import subprocess
import tarfile

from django.utils.translation import gettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import module_loader
from plinth.actions import privileged, secret_str
from plinth.utils import Version

from . import errors

TIMEOUT = 30
BACKUPS_DATA_PATH = pathlib.Path('/var/lib/plinth/backups-data/')
BACKUPS_UPLOAD_PATH = pathlib.Path('/var/lib/freedombox/backups-upload/')
MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'

# known errors that come up when remotely accessing a borg repository
# 'errors' are error strings to look for in the stacktrace.
KNOWN_ERRORS = [
    {
        'errors': ['subprocess.TimeoutExpired'],
        'message':
            _('Connection refused - make sure you provided correct '
              'credentials and the server is running.'),
        'raise_as':
            errors.BorgError,
    },
    {
        'errors': ['Connection refused'],
        'message': _('Connection refused'),
        'raise_as': errors.BorgError,
    },
    {
        'errors': [
            'not a valid repository', 'does not exist', 'FileNotFoundError'
        ],
        'message': _('Repository not found'),
        'raise_as': errors.BorgRepositoryDoesNotExistError,
    },
    {
        'errors': ['passphrase supplied in .* is incorrect'],
        'message': _('Incorrect encryption passphrase'),
        'raise_as': errors.BorgError,
    },
    {
        'errors': ['Connection reset by peer'],
        'message': _('SSH access denied'),
        'raise_as': errors.SshfsError,
    },
    {
        'errors': ['There is already something at'],
        'message':
            _('Repository path is neither empty nor '
              'is an existing backups repository.'),
        'raise_as':
            errors.BorgError,
    },
    {
        'errors': ['A repository already exists at'],
        'message': None,
        'raise_as': errors.BorgRepositoryExists,
    },
    {
        'errors': ['Archive .* already exists'],
        'message':
            _('An archive with given name already exists in the repository.'),
        'raise_as':
            errors.BorgArchiveExists,
    },
    {
        'errors': ['Archive .* not found'],
        'message':
            _('Archive with given name was not found in the repository.'),
        'raise_as':
            errors.BorgArchiveDoesNotExist,
    },
    {
        'errors': ['Failed to create/acquire the lock'],
        'message': _('Backup system is busy with another operation.'),
        'raise_as': errors.BorgBusy,
    },
    {
        'errors': ['No space left on device'],
        'message': _('Not enough space left on the disk or remote location.'),
        'raise_as': errors.BorgNoSpace,
    },
]


class AlreadyMountedError(Exception):
    """Exception raised when mount point is already mounted."""


def reraise_known_errors(privileged_func):
    """Decorator to convert borg raised exceptions to specialized ones."""

    @functools.wraps(privileged_func)
    def wrapper(*args, **kwargs):
        """Run privileged method, catch exceptions and throw new ones."""
        try:
            return privileged_func(*args, **kwargs)
        except Exception as exception:
            _reraise_known_errors(exception)

    return wrapper


def _reraise_known_errors(err):
    """Look whether the caught error is known and reraise it accordingly"""
    stdout = (getattr(err, 'stdout', b'') or b'').decode()
    stderr = (getattr(err, 'stderr', b'') or b'').decode()
    caught_error = str((err, err.args, stdout, stderr))
    for known_error in KNOWN_ERRORS:
        for error in known_error['errors']:
            if re.search(error, caught_error):
                raise known_error['raise_as'](known_error['message'])

    raise err


@reraise_known_errors
@privileged
def mount(mountpoint: str, remote_path: str, ssh_keyfile: str | None = None,
          password: secret_str | None = None,
          user_known_hosts_file: str = '/dev/null'):
    """Mount a remote ssh path via sshfs."""
    try:
        _validate_mountpoint(mountpoint)
    except AlreadyMountedError:
        return

    input_ = None
    # the shell would expand ~/ to the local home directory
    remote_path = remote_path.replace('~/', '').replace('~', '')
    # 'reconnect', 'ServerAliveInternal' and 'ServerAliveCountMax' allow the
    # client (FreedomBox) to keep control of the SSH connection even when the
    # SSH server misbehaves. Without these options, other commands such as
    # 'freedombox-cmd storage usage_info --no-args', 'df', 'freedombox-cmd
    # sshfs is_mounted --no-args', or 'mountpoint' might block indefinitely
    # (even when manually invoked from the command line). This situation has
    # some lateral effects, causing major system instability in the course of
    # ~11 days, and leaving the system in such state that the only solution is
    # a reboot.
    cmd = [
        'sshfs', remote_path, mountpoint, '-o',
        f'UserKnownHostsFile={user_known_hosts_file}', '-o',
        'StrictHostKeyChecking=yes', '-o', 'reconnect', '-o',
        'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3'
    ]
    if ssh_keyfile:
        cmd += ['-o', 'IdentityFile=' + ssh_keyfile]
    else:
        if not password:
            raise ValueError('mount requires either a password or ssh_keyfile')
        cmd += ['-o', 'password_stdin']
        input_ = password.encode()

    action_utils.run(cmd, check=True, timeout=TIMEOUT, input=input_)


@reraise_known_errors
@privileged
def umount(mountpoint: str):
    """Unmount a mountpoint."""
    action_utils.run(['umount', mountpoint], check=True)


def _validate_mountpoint(mountpoint):
    """Check that the folder is empty, and create it if it doesn't exist."""
    if os.path.exists(mountpoint):
        if _is_mounted(mountpoint):
            raise AlreadyMountedError('Mountpoint %s already mounted' %
                                      mountpoint)
        if os.listdir(mountpoint) or not os.path.isdir(mountpoint):
            raise ValueError('Mountpoint %s is not an empty directory' %
                             mountpoint)
    else:
        os.makedirs(mountpoint)


def _is_mounted(mountpoint):
    """Return boolean whether a local directory is a mountpoint."""
    cmd = ['mountpoint', '-q', mountpoint]
    # mountpoint exits with status non-zero if it didn't find a mountpoint
    try:
        action_utils.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


@reraise_known_errors
@privileged
def is_mounted(mount_point: str) -> bool:
    """Return whether a path is already mounted."""
    return _is_mounted(mount_point)


@reraise_known_errors
@privileged
def setup(path: str):
    """Create repository if it does not already exist."""
    try:
        _run(['borg', 'info', path], check=True)
    except subprocess.CalledProcessError:
        parent = os.path.dirname(path)
        if not os.path.exists(parent):
            os.makedirs(parent)

        _init_repository(path, encryption='none')


def _init_repository(path: str, encryption: str,
                     encryption_passphrase: str | None = None):
    """Initialize a local or remote borg repository."""
    if encryption != 'none':
        if not encryption_passphrase:
            raise ValueError('No encryption passphrase provided')

    cmd = ['borg', 'init', '--encryption', encryption, path]
    _run(cmd, encryption_passphrase)


@reraise_known_errors
@privileged
def init(path: str, encryption: str,
         encryption_passphrase: secret_str | None = None):
    """Initialize the borg repository."""
    _init_repository(path, encryption, encryption_passphrase)


@reraise_known_errors
@privileged
def info(path: str, encryption_passphrase: secret_str | None = None) -> dict:
    """Show repository information."""
    process = _run(['borg', 'info', '--json', path], encryption_passphrase,
                   stdout=subprocess.PIPE)
    return json.loads(process.stdout.decode())


@reraise_known_errors
@privileged
def list_repo(path: str,
              encryption_passphrase: secret_str | None = None) -> dict:
    """List repository contents."""
    process = _run(['borg', 'list', '--json', '--format="{comment}"', path],
                   encryption_passphrase, stdout=subprocess.PIPE)
    return json.loads(process.stdout.decode())


@reraise_known_errors
@privileged
def add_uploaded_archive(file_name: str, temporary_file_path: str):
    """Store an archive uploaded by the user."""
    BACKUPS_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
    action_utils.move_uploaded_file(temporary_file_path, BACKUPS_UPLOAD_PATH,
                                    file_name, allow_overwrite=True,
                                    permissions=0o600)


@reraise_known_errors
@privileged
def remove_uploaded_archive(file_path: str):
    """Delete the archive uploaded by the user."""
    resolved_file_path = pathlib.Path(file_path).resolve()
    if (resolved_file_path.is_relative_to(BACKUPS_UPLOAD_PATH)
            and resolved_file_path.is_file()):
        resolved_file_path.unlink()


def _get_borg_version():
    """Return the version of borgbackup."""
    process = _run(['borg', '--version'], stdout=subprocess.PIPE)
    return process.stdout.decode().split()[1]  # Example: "borg 1.1.9"


@reraise_known_errors
@privileged
def create_archive(path: str, paths: list[str], comment: str | None = None,
                   encryption_passphrase: secret_str | None = None):
    """Create archive."""
    existing_paths = filter(os.path.exists, paths)
    command = ['borg', 'create', '--json']
    if comment:
        if Version(_get_borg_version()) < Version('1.1.10'):
            # Undo any placeholder escape sequences in comments as this version
            # of borg does not support placeholders. XXX: Drop this code when
            # support for borg < 1.1.10 is dropped.
            comment = comment.replace('{{', '{').replace('}}', '}')

        command += ['--comment', comment]

    command += [path] + list(existing_paths)
    _run(command, encryption_passphrase)


@reraise_known_errors
@privileged
def delete_archive(path: str, encryption_passphrase: secret_str | None = None):
    """Delete archive."""
    _run(['borg', 'delete', path], encryption_passphrase)


def _extract(archive_path, destination, encryption_passphrase, locations=None):
    """Extract archive contents."""
    prev_dir = os.getcwd()
    borg_call = ['borg', 'extract', archive_path]
    # do not extract any files when we get an empty locations list
    if locations is not None:
        borg_call.extend(locations)

    try:
        os.chdir(os.path.expanduser(destination))
        # TODO: with python 3.7 use subprocess.run with the 'capture_output'
        # argument
        process = _run(borg_call, encryption_passphrase, check=False,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            error = process.stderr.decode()
            # Don't fail on the borg error when no files were matched
            if "never matched" not in error:
                raise subprocess.CalledProcessError(process.returncode,
                                                    process.args)
    finally:
        os.chdir(prev_dir)


@reraise_known_errors
@privileged
def export_tar(path: str, encryption_passphrase: secret_str | None = None):
    """Export archive contents as tar stream on stdout."""
    env = _get_env(encryption_passphrase)
    process = subprocess.Popen(
        ['borg', 'export-tar', path, '-', '--tar-filter=gzip'], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return actions.ProcessBufferedReader(process)


def _read_archive_file(archive, filepath, encryption_passphrase):
    """Read the content of a file inside an archive."""
    borg_call = ['borg', 'extract', archive, filepath, '--stdout']
    return _run(borg_call, encryption_passphrase,
                stdout=subprocess.PIPE).stdout.decode()


@reraise_known_errors
@privileged
def get_archive_apps(
        path: str,
        encryption_passphrase: secret_str | None = None) -> list[str]:
    """Get list of apps included in archive."""
    manifest_folder = os.path.relpath(MANIFESTS_FOLDER, '/')
    borg_call = [
        'borg', 'list', path, manifest_folder, '--format', '{path}{NEWLINE}'
    ]
    try:
        borg_process = _run(borg_call, encryption_passphrase,
                            stdout=subprocess.PIPE)
        manifest_path = borg_process.stdout.decode().strip()
    except subprocess.CalledProcessError:
        raise RuntimeError('Borg exited unsuccessfully')

    manifest = None
    if manifest_path:
        manifest_data = _read_archive_file(path, manifest_path,
                                           encryption_passphrase)
        manifest = json.loads(manifest_data)

    archive_apps = []
    if manifest:
        for app in _get_apps_of_manifest(manifest):
            archive_apps.append(app['name'])

    return archive_apps


def _get_apps_of_manifest(manifest):
    """Get apps of a manifest.

    Supports both dict format as well as list format of plinth <=0.42

    """
    if isinstance(manifest, list):
        apps = manifest
    elif isinstance(manifest, dict) and 'apps' in manifest:
        apps = manifest['apps']
    else:
        raise RuntimeError('Unknown manifest format')

    return apps


@reraise_known_errors
@privileged
def get_exported_archive_apps(path: str) -> list[str]:
    """Get list of apps included in an exported archive file."""
    manifest = None
    with tarfile.open(path) as tar_handle:
        filenames = tar_handle.getnames()
        for name in filenames:
            if 'var/lib/plinth/backups-manifests/' in name \
               and name.endswith('.json'):
                file_handle = tar_handle.extractfile(name)
                if not file_handle:
                    raise RuntimeError(
                        'Unable to extract app manifest from backup file.')

                manifest_data = file_handle.read()
                manifest = json.loads(manifest_data)
                break

    app_names = []
    if manifest:
        for app in _get_apps_of_manifest(manifest):
            app_names.append(app['name'])

    return app_names


@reraise_known_errors
@privileged
def restore_archive(archive_path: str, destination: str,
                    directories: list[str], files: list[str],
                    encryption_passphrase: secret_str | None = None):
    """Restore files from an archive."""
    locations_all = directories + files
    locations_all = [
        os.path.relpath(location, '/') for location in locations_all
    ]
    _extract(archive_path, destination, encryption_passphrase,
             locations=locations_all)


@reraise_known_errors
@privileged
def restore_exported_archive(path: str, directories: list[str],
                             files: list[str]):
    """Restore files from an exported archive."""
    with tarfile.open(path) as tar_handle:
        for member in tar_handle.getmembers():
            path = '/' + member.name
            if path in files:
                tar_handle.extract(member, '/')
            else:
                for directory in directories:
                    if path.startswith(directory):
                        tar_handle.extract(member, '/')
                        break


def _assert_app_id(app_id):
    """Check that app ID is correct."""
    if not re.fullmatch(r'[a-z0-9_]+', app_id):
        raise Exception('Invalid App ID')


@reraise_known_errors
@privileged
def dump_settings(app_id: str, settings: dict[str, int | float | bool | str]):
    """Dump an app's settings to a JSON file."""
    _assert_app_id(app_id)
    BACKUPS_DATA_PATH.mkdir(exist_ok=True)
    settings_path = BACKUPS_DATA_PATH / f'{app_id}-settings.json'
    settings_path.write_text(json.dumps(settings))


@reraise_known_errors
@privileged
def load_settings(app_id: str) -> dict[str, int | float | bool | str]:
    """Load an app's settings from a JSON file."""
    _assert_app_id(app_id)
    settings_path = BACKUPS_DATA_PATH / f'{app_id}-settings.json'
    try:
        return json.loads(settings_path.read_text())
    except FileNotFoundError:
        return {}


@privileged
def delete_before_restore(app_id: str):
    """Delete some paths before restoring an app."""
    module_loader.load_modules()
    app_module.apps_init()
    app = app_module.App.get(app_id)

    from plinth.modules.backups.components import BackupRestore
    components = app.get_components_of_type(BackupRestore)
    for component in components:
        for path in component.delete_before_restore:
            shutil.rmtree(path, ignore_errors=True)


def _get_env(encryption_passphrase: str | None = None):
    """Create encryption and ssh kwargs out of given arguments."""
    env = dict(os.environ, BORG_RELOCATED_REPO_ACCESS_IS_OK='yes',
               BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK='yes',
               LANG='C.UTF-8')
    # Always provide BORG_PASSPHRASE (also if empty) so borg does not get stuck
    # while asking for a passphrase.
    env['BORG_PASSPHRASE'] = encryption_passphrase or ''
    return env


def _run(cmd, encryption_passphrase=None, check=True, **kwargs):
    """Wrap the command with extra encryption passphrase handling."""
    env = _get_env(encryption_passphrase)
    return action_utils.run(cmd, check=check, env=env, **kwargs)
