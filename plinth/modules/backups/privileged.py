# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure backups and sshfs."""

import os
import subprocess

from plinth.actions import privileged

TIMEOUT = 30


class AlreadyMountedError(Exception):
    """Exception raised when mount point is already mounted."""


@privileged
def mount(mountpoint: str, remote_path: str, ssh_keyfile: str = None,
          password: str = None, user_known_hosts_file: str = '/dev/null'):
    """Mount a remote ssh path via sshfs."""
    try:
        _validate_mountpoint(mountpoint)
    except AlreadyMountedError:
        return

    kwargs = {}
    # the shell would expand ~/ to the local home directory
    remote_path = remote_path.replace('~/', '').replace('~', '')
    # 'reconnect', 'ServerAliveInternal' and 'ServerAliveCountMax' allow the
    # client (FreedomBox) to keep control of the SSH connection even when the
    # SSH server misbehaves. Without these options, other commands such as
    # '/usr/share/plinth/actions/storage usage-info', 'df',
    # '/usr/share/plinth/actions/sshfs is-mounted', or 'mountpoint' might block
    # indefinitely (even when manually invoked from the command line). This
    # situation has some lateral effects, causing major system instability in
    # the course of ~11 days, and leaving the system in such state that the
    # only solution is a reboot.
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
        kwargs['input'] = password.encode()

    subprocess.run(cmd, check=True, timeout=TIMEOUT, **kwargs)


@privileged
def subcommand_umount(mountpoint: str):
    """Unmount a mountpoint."""
    subprocess.run(['umount', mountpoint], check=True)


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
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


@privileged
def is_mounted(arguments) -> bool:
    """Print whether a path is already mounted."""
    return _is_mounted(arguments.mountpoint)
