# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for SSH server."""

import grp
import pathlib
import pwd
import shutil
import stat

import augeas

from freedombox import action_utils, utils
from freedombox.actions import privileged, secret_str

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


def _get_user_homedir(username: str) -> pathlib.Path:
    """Return the home dir of a user by looking up in password database."""
    try:
        return pathlib.Path(pwd.getpwnam(username).pw_dir)
    except KeyError:
        raise ValueError('Username not found')


@privileged
def get_keys(user: str) -> str:
    """Get SSH authorized keys."""
    path = _get_user_homedir(user) / '.ssh' / 'authorized_keys'
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ''


@privileged
def set_keys(user: str, keys: str, auth_user: str, auth_password: secret_str):
    """Set SSH authorized keys."""
    must_be_admin = user != auth_user
    _validate_user(auth_user, auth_password, must_be_admin=must_be_admin)

    ssh_folder = _get_user_homedir(user) / '.ssh'
    key_file_path = ssh_folder / 'authorized_keys'

    action_utils.run(['mkhomedir_helper', user], check=True)

    if not ssh_folder.exists():
        ssh_folder.mkdir()
        shutil.chown(ssh_folder, user, 'users')

    key_file_path.write_text(keys, encoding='utf-8')
    shutil.chown(key_file_path, user, 'users')
    key_file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)


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
