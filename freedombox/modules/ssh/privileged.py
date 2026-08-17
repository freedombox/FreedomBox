# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for SSH server."""

import grp
import os
import pathlib
import pwd
import shutil
import stat

import augeas

from plinth import action_utils, utils
from plinth.actions import privileged, secret_str

config_file = pathlib.Path('/etc/ssh/sshd_config.d/freedombox.conf')


def _validate_user(username, password, must_be_admin=True):
    """Validate a user."""
    if must_be_admin:
        try:
            admins = grp.getgrnam('admin').gr_mem
        except KeyError:
            admins = []

        if username not in admins:
            msg = f'"{username}" is not authorized to perform this action'
            raise PermissionError(msg)

    if not utils.is_authenticated_user(username, password):
        raise PermissionError('Invalid credentials')


def _managed_user(username):
    """Raise an error if the user is root."""
    if pwd.getpwnam(username).pw_gid == 0:
        raise ValueError(f'User {username} is not managed by FreedomBox')

    return username


@privileged
def setup():
    """Setup Open SSH server.

    Regenerates deleted SSH keys. This is necessary when FreedomBox image is
    being used. During the image building process the SSH keys are removed and
    start OpenSSH server fails without the keys.

    If the keys already exist, do nothing. This is necessary when a user
    installs FreedomBox using an apt package. SSH keys exist and running
    reconfigure on the openssh-server package does not regenerate them.
    """
    action_utils.dpkg_reconfigure('openssh-server', {})


@privileged
def restrict_users(should_restrict: bool):
    """Restrict SSH logins to groups root, sudo, admin and freedombox-ssh."""
    if not should_restrict:
        config_file.unlink(missing_ok=True)
    else:
        config_file.write_text('AllowGroups root sudo admin freedombox-ssh\n',
                               encoding='utf-8')

    action_utils.service_reload('sshd')


def are_users_restricted() -> bool:
    """Return whether only restricted groups of users are allowed."""
    return config_file.exists()


def get_user_homedir(username):
    """Return the home dir of a user by looking up in password database."""
    try:
        return pwd.getpwnam(username).pw_dir
    except KeyError:
        raise ValueError('Username not found')


@privileged
def get_keys(user: str) -> str:
    """Get SSH authorized keys."""
    path = os.path.join(get_user_homedir(user), '.ssh', 'authorized_keys')
    try:
        with open(path, 'r', encoding='utf-8') as file_handle:
            return file_handle.read()
    except FileNotFoundError:
        return ''


@privileged
def set_keys(user: str, keys: str, auth_user: str, auth_password: secret_str):
    """Set SSH authorized keys."""
    must_be_admin = user != auth_user
    _validate_user(auth_user, auth_password, must_be_admin=must_be_admin)

    ssh_folder = os.path.join(get_user_homedir(user), '.ssh')
    key_file_path = os.path.join(ssh_folder, 'authorized_keys')

    action_utils.run(['mkhomedir_helper', user], check=True)

    if not os.path.exists(ssh_folder):
        os.makedirs(ssh_folder)
        shutil.chown(ssh_folder, user, 'users')

    with open(key_file_path, 'w', encoding='utf-8') as file_handle:
        file_handle.write(keys)

    shutil.chown(key_file_path, user, 'users')
    os.chmod(key_file_path, stat.S_IRUSR | stat.S_IWUSR)


def _load_augeas():
    """Initialize augeas for this app's configuration file."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Sshd/lens', 'Sshd.lns')
    aug.set('/augeas/load/Sshd/incl[last() + 1]', '/etc/ssh/sshd_config')
    aug.load()

    return aug


@privileged
def is_password_authentication_enabled() -> bool:
    """Retrieve value of password authentication from sshd configuration."""
    aug = _load_augeas()
    field_path = '/files/etc/ssh/sshd_config/PasswordAuthentication'
    get_value = aug.get(field_path)
    return (get_value or 'yes') == 'yes'


@privileged
def set_password_authentication(enable: bool):
    """Set value of password authentication in sshd configuration."""
    value = 'yes' if enable else 'no'
    aug = _load_augeas()
    aug.set('/files/etc/ssh/sshd_config/PasswordAuthentication', value)
    aug.save()
