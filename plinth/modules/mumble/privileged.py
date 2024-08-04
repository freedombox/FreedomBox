# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configure Mumble server.
"""

import pathlib
import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged, secret_str

CONFIG_FILE = '/etc/mumble-server.ini'
DATA_DIR = '/var/lib/mumble-server'


@privileged
def setup():
    """Setup Mumble server."""
    aug = _load_augeas()
    aug.set('.anon/sslCert', DATA_DIR + '/fullchain.pem')
    aug.set('.anon/sslKey', DATA_DIR + '/privkey.pem')
    aug.save()


@privileged
def set_super_user_password(password: secret_str):
    """Set the superuser password with murmurd command."""
    subprocess.run(['murmurd', '-readsupw'], input=password.encode(),
                   stdout=subprocess.DEVNULL, check=False)


@privileged
def get_domain() -> str | None:
    """Return domain name set in mumble or empty string."""
    domain_file = pathlib.Path('/var/lib/mumble-server/domain-freedombox')
    try:
        return domain_file.read_text(encoding='utf-8')
    except FileNotFoundError:
        return None


@privileged
def set_domain(domain_name: str | None):
    """Write a file containing domain name."""
    if domain_name:
        domain_file = pathlib.Path('/var/lib/mumble-server/domain-freedombox')
        domain_file.write_text(domain_name, encoding='utf-8')


@privileged
def change_join_password(join_password: secret_str):
    """Change to password that is required to join the server"""
    aug = _load_augeas()
    aug.set('.anon/serverpassword', join_password)
    aug.save()
    action_utils.service_try_restart('mumble-server')


@privileged
def change_root_channel_name(root_channel_name: str):
    """Change the name of the Root channel."""
    aug = _load_augeas()
    aug.set('.anon/registerName', root_channel_name)
    aug.save()
    action_utils.service_try_restart('mumble-server')


@privileged
def get_root_channel_name() -> str | None:
    """Return the currently configured Root channel name."""
    aug = _load_augeas()
    name = aug.get('.anon/registerName')
    return name or None


def _load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Php', CONFIG_FILE)
    aug.set('/augeas/context', '/files' + CONFIG_FILE)
    aug.load()

    return aug
