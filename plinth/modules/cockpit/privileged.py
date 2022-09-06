# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configure Cockpit.
"""

import augeas

from plinth import action_utils
from plinth.actions import privileged

CONFIG_FILE = '/etc/cockpit/cockpit.conf'


def _load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/inifile/lens', 'Puppet.lns')
    aug.set('/augeas/load/inifile/incl[last() + 1]', CONFIG_FILE)
    aug.load()
    return aug


@privileged
def setup():
    """Setup Cockpit configuration."""
    aug = _load_augeas()
    aug.set('/files' + CONFIG_FILE + '/WebService/UrlRoot', '/_cockpit/')
    aug.remove('/files' + CONFIG_FILE + '/WebService/Origins')
    aug.save()
    action_utils.service_restart('cockpit.socket')
    # Accommodate changes in Apache configuration file from v1 to v2.
    action_utils.service_reload('apache2')
