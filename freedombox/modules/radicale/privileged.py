# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Radicale."""

import os
import shutil

import augeas

from plinth import action_utils
from plinth.actions import privileged

CONFIG_FILE = '/etc/radicale/config'
LOG_PATH = '/var/log/radicale'
SERVICE_NAME = 'uwsgi-app@radicale.service'


@privileged
def setup():
    """Configure authentication to Apache remote user.

    For radicale < 3.5 (bookworm), this was set by configuration shipped with
    Debian. For radicale >= 3.5 (trixie), this needs to be explicitly. For
    simplicity, set is unconditionally.
    """
    aug = load_augeas()
    aug.set('auth/type', 'remote_user')
    aug.set('auth/lc_username', 'True')
    aug.save()
    # Service is started again by socket.
    action_utils.service_stop(SERVICE_NAME)


@privileged
def configure(rights_type: str):
    """Set the radicale rights type to a particular value."""
    if rights_type == 'owner_only':
        # Default rights file is equivalent to owner_only.
        rights_type = 'from_file'

    aug = load_augeas()
    aug.set('rights/type', rights_type)
    aug.save()
    action_utils.service_stop(SERVICE_NAME)


@privileged
def fix_paths():
    """Fix log path to work around a bug."""
    # Workaround for bug in radicale's uwsgi script (#931201)
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    # INI file lens
    aug.transform('Radicale', CONFIG_FILE)
    aug.set('/augeas/context', '/files' + CONFIG_FILE)
    aug.load()
    return aug


def get_rights_value():
    """Returns the current Rights value."""
    aug = load_augeas()
    value = aug.get('rights/type')

    if value == 'from_file':
        # Default rights file is equivalent to owner_only.
        value = 'owner_only'

    return value


@privileged
def uninstall():
    """Remove all radicale collections."""
    shutil.rmtree('/var/lib/private/radicale/', ignore_errors=True)
