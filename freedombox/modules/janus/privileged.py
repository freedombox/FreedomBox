# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configure Janus server.
"""

from plinth import action_utils
from plinth.actions import privileged

JANUS_CONF_PATH = '/etc/janus/janus.jcfg'


@privileged
def setup():
    """Setup Janus server."""
    with open(JANUS_CONF_PATH, 'r', encoding='utf-8') as config_file:
        config_lines = config_file.readlines()

    with open(JANUS_CONF_PATH, 'w', encoding='utf-8') as config_file:
        for line in config_lines:
            if '#rtp_port_range' in line:
                config_file.write("\trtp_port_range = \"50176-51199\"\n")
            else:
                config_file.write(line)

    action_utils.service_try_restart('janus')
