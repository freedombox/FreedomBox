# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for Coturn daemon."""

import pathlib
import random
import shutil
import string

import augeas

from plinth import action_utils
from plinth.actions import privileged

CONFIG_FILE = pathlib.Path('/etc/coturn/freedombox.conf')


def _key_path(key):
    """Return the augeas path for a key."""
    return '/files' + str(CONFIG_FILE) + '/' + key


@privileged
def setup():
    """Setup Coturn server."""
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.touch(0o640)
        shutil.chown(CONFIG_FILE, group='turnserver')

    action_utils.service_daemon_reload()

    aug = augeas_load()

    # XXX: Should we set external-ip
    aug.set(_key_path('min-port'), '49152')
    aug.set(_key_path('max-port'), '50175')
    aug.set(_key_path('use-auth-secret'), 'true')
    if not aug.get(_key_path('static-auth-secret')):
        secret = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(64))
        aug.set(_key_path('static-auth-secret'), secret)

    aug.set(_key_path('cert'), '/etc/coturn/certs/cert.pem')
    aug.set(_key_path('pkey'), '/etc/coturn/certs/pkey.pem')
    aug.set(_key_path('no-tlsv1'), 'true')
    aug.set(_key_path('no-tlsv1_1'), 'true')
    aug.set(_key_path('no-cli'), 'true')
    aug.set(_key_path('listening-ip[1]'), '::')
    # Keep ::1 because at least two IP addresses of same class are needed for
    # enabling alternate port (port + 1). This is in turn needed for NAT
    # Behavior Discovery (RFC 5780).
    aug.set(_key_path('listening-ip[2]'), '::1')

    aug.save()

    action_utils.service_try_restart('coturn')


@privileged
def get_config() -> dict[str, str]:
    """Return the current configuration."""
    aug = augeas_load()
    config = {
        'static_auth_secret': aug.get(_key_path('static-auth-secret')),
        'realm': aug.get(_key_path('realm')),
    }
    return config


@privileged
def set_domain(domain_name: str):
    """Set the TLS domain.

    This value is usually not stored. So, set realm value even though it is not
    needed to set realm for REST API based authentication.
    """
    aug = augeas_load()
    aug.set(_key_path('realm'), domain_name)
    aug.save()


def augeas_load():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Simplevars/lens', 'Simplevars.lns')
    aug.set('/augeas/load/Simplevars/incl[last() + 1]', str(CONFIG_FILE))
    aug.load()

    return aug
