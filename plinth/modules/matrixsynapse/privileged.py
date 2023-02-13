# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Matrix-Synapse server."""

import json
import os
import pathlib
from typing import Optional

import yaml

from plinth import action_utils
from plinth.actions import privileged

CONF_DIR = "/etc/matrix-synapse/conf.d/"

ORIG_CONF_PATH = '/etc/matrix-synapse/homeserver.yaml'
SERVER_NAME_PATH = CONF_DIR + 'server_name.yaml'
STATIC_CONF_PATH = CONF_DIR + 'freedombox-static.yaml'
LISTENERS_CONF_PATH = CONF_DIR + 'freedombox-listeners.yaml'
REGISTRATION_CONF_PATH = CONF_DIR + 'freedombox-registration.yaml'
TURN_CONF_PATH = CONF_DIR + 'freedombox-turn.yaml'
OVERRIDDEN_TURN_CONF_PATH = CONF_DIR + 'turn.yaml'

STATIC_CONFIG = {
    'max_upload_size':
        '100M',
    'password_providers': [{
        'module': 'ldap_auth_provider.LdapAuthProvider',
        'config': {
            'enabled': True,
            'uri': 'ldap://localhost:389',
            'start_tls': False,
            'base': 'ou=users,dc=thisbox',
            'attributes': {
                'uid': 'uid',
                'name': 'uid',
                'mail': '',
            },
        },
    }, ],
}


@privileged
def post_install():
    """Perform post installation configuration."""
    with open(STATIC_CONF_PATH, 'w', encoding='utf-8') as static_conf_file:
        yaml.dump(STATIC_CONFIG, static_conf_file)

    # start with listener config from original homeserver.yaml
    with open(ORIG_CONF_PATH, encoding='utf-8') as orig_conf_file:
        orig_config = yaml.safe_load(orig_conf_file)

    listeners = orig_config['listeners']
    for listener in listeners:
        if listener['port'] == 8448:
            listener['bind_addresses'] = ['::', '0.0.0.0']
            listener.pop('bind_address', None)

    with open(LISTENERS_CONF_PATH, 'w',
              encoding='utf-8') as listeners_conf_file:
        yaml.dump({'listeners': listeners}, listeners_conf_file)


@privileged
def setup(domain_name: str):
    """Configure the domain name for matrix-synapse package."""
    action_utils.dpkg_reconfigure('matrix-synapse',
                                  {'server-name': domain_name})


def get_config():
    """Return the current configuration of matrix-synapse."""
    try:
        with open(REGISTRATION_CONF_PATH, encoding='utf-8') as reg_conf_file:
            config = yaml.safe_load(reg_conf_file)
    except FileNotFoundError:
        # Check if its set in original conffile.
        with open(ORIG_CONF_PATH, encoding='utf-8') as orig_conf_file:
            config = yaml.safe_load(orig_conf_file)

    return {
        'public_registration': bool(config.get('enable_registration', False)),
    }


@privileged
def set_config(public_registration: bool):
    """Enable/disable public user registration."""
    config = {'enable_registration': public_registration}
    with open(REGISTRATION_CONF_PATH, 'w', encoding='utf-8') as reg_conf_file:
        yaml.dump(config, reg_conf_file)

    action_utils.service_try_restart('matrix-synapse')


@privileged
def move_old_conf():
    """Move old configuration to backup so it can be restored by reinstall."""
    conf_file = pathlib.Path(ORIG_CONF_PATH)
    if conf_file.exists():
        backup_file = conf_file.with_suffix(conf_file.suffix + '.fbx-bak')
        conf_file.replace(backup_file)


def _set_turn_config(conf_file, conf):
    turn_server_config = json.loads(conf)

    if not turn_server_config['uris']:
        # No valid configuration, remove the configuration file
        try:
            os.remove(conf_file)
        except FileNotFoundError:
            pass

        return

    config = {
        'turn_uris': turn_server_config['uris'],
        'turn_shared_secret': turn_server_config['shared_secret'],
        'turn_user_lifetime': 86400000,
        'turn_allow_guests': True
    }

    with open(conf_file, 'w+', encoding='utf-8') as turn_config:
        yaml.dump(config, turn_config)


@privileged
def configure_turn(managed: bool, conf: str):
    """Set parameters for the STUN/TURN server to use with Matrix Synapse."""
    if managed:
        _set_turn_config(TURN_CONF_PATH, conf)
    else:
        _set_turn_config(OVERRIDDEN_TURN_CONF_PATH, conf)

    action_utils.service_try_restart('matrix-synapse')
