# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configuration helper for Transmission daemon.
"""

import json
import pathlib
from typing import Union

from plinth import action_utils
from plinth.actions import privileged

_transmission_config = pathlib.Path('/etc/transmission-daemon/settings.json')


@privileged
def get_configuration() -> dict[str, str]:
    """Return the current configuration in JSON format."""
    return json.loads(_transmission_config.read_text(encoding='utf-8'))


@privileged
def merge_configuration(configuration: dict[str, Union[str, bool]]):
    """Merge given JSON configuration with existing configuration."""
    current_configuration = _transmission_config.read_bytes()
    current_configuration = json.loads(current_configuration)

    new_configuration = current_configuration
    new_configuration.update(configuration)
    new_configuration = json.dumps(new_configuration, indent=4, sort_keys=True)

    _transmission_config.write_text(new_configuration, encoding='utf-8')
    action_utils.service_reload('transmission-daemon')
