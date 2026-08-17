# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Matrix-Synapse server."""

import hashlib
import hmac
import json
import os
import pathlib
import shutil

import requests
import yaml

from plinth import action_utils, utils
from plinth.actions import privileged

CONF_DIR = "/etc/matrix-synapse/conf.d/"

ORIG_CONF_PATH = '/etc/matrix-synapse/homeserver.yaml'
SERVER_NAME_PATH = CONF_DIR + 'server_name.yaml'
STATIC_CONF_PATH = CONF_DIR + 'freedombox-static.yaml'
LISTENERS_CONF_PATH = CONF_DIR + 'freedombox-listeners.yaml'
REGISTRATION_CONF_PATH = CONF_DIR + 'freedombox-registration.yaml'
REGISTRATION_SECRET_PATH = CONF_DIR + 'freedombox-registration-secret.yaml'
ADMIN_ACCESS_TOKEN_PATH = CONF_DIR + 'freedombox-admin-access-token.txt'
TURN_CONF_PATH = CONF_DIR + 'freedombox-turn.yaml'
OVERRIDDEN_TURN_CONF_PATH = CONF_DIR + 'turn.yaml'
FREEDOMBOX_ADMIN_USERNAME = 'freedombox-admin'
ADMIN_API_BASE = 'http://localhost:8008/_synapse/admin/v1/'

STATIC_CONFIG = {
    'max_upload_size': '100M',
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
    'suppress_key_server_warning': True,
    'trusted_key_servers': [{
        'server_name': 'matrix.org'
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

    if config.get('enable_registration_without_verification'):
        registration_verification = 'disabled'
    elif config.get('registration_requires_token'):
        registration_verification = 'token'
    else:
        registration_verification = None

    return {
        'public_registration': bool(config.get('enable_registration', False)),
        'registration_verification': registration_verification,
    }


@privileged
def set_config(public_registration: bool,
               registration_verification: str | None = None):
    """Enable/disable public user registration."""
    if registration_verification == 'token':
        _create_registration_token()

    config = {'enable_registration': public_registration}
    if public_registration and registration_verification in ('disabled', None):
        config['enable_registration_without_verification'] = True
    elif registration_verification == 'token':
        config['registration_requires_token'] = True

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


@privileged
def fix_public_registrations():
    """If public registrations are enabled, set validation mechanism."""
    config = get_config()
    if (config['public_registration']
            and config['registration_verification'] is None):
        set_config(public_registration=True,
                   registration_verification='disabled')


def _ensure_server_is_running():
    """Raise an exception if matrix-synapse server is not running."""
    if not action_utils.service_is_running('matrix-synapse'):
        raise ProcessLookupError


def _get_registration_shared_secret() -> str:
    """Ensure that server is set to use a shared secret for registration."""
    secret_file = pathlib.Path(REGISTRATION_SECRET_PATH)
    if secret_file.exists():
        with secret_file.open() as file_handle:
            return yaml.safe_load(file_handle)['registration_shared_secret']

    secret = utils.generate_password()
    # Ensure that file is readable by matrix-synapse user and root.
    previous_umask = os.umask(0o077)
    try:
        secret_file.write_text(f'registration_shared_secret: "{secret}"\n')
    finally:
        os.umask(previous_umask)

    shutil.chown(secret_file, 'matrix-synapse', 'nogroup')
    action_utils.service_try_restart('matrix-synapse')
    return secret


def _parse_api_error(response):
    """Raise exception if the response of API call was an error."""
    if response.get('errcode'):
        raise ConnectionError(response['errcode'], response['error'])


def _get_access_token() -> str:
    """Create a new freedombox-admin account and return its access token.

    For user registration Admin API, see:
    https://matrix-org.github.io/synapse/latest/admin_api/register_api.html
    """
    access_token_path = pathlib.Path(ADMIN_ACCESS_TOKEN_PATH)
    if access_token_path.exists():
        return access_token_path.read_text().strip()

    shared_secret = _get_registration_shared_secret()
    nonce = _get_nonce()
    username = FREEDOMBOX_ADMIN_USERNAME
    # No need to store password, we will use the access token.
    password = utils.generate_password()
    mac = _generate_mac(shared_secret, nonce, username, password, True)
    data = {
        'nonce': nonce,
        'username': username,
        'displayname': 'FreedomBox Admin',
        'password': password,
        'admin': True,
        'mac': mac
    }
    request = requests.post(ADMIN_API_BASE + 'register', json=data)
    response = request.json()
    _parse_api_error(response)

    # Ensure that file is only readable by root user.
    previous_umask = os.umask(0o077)
    try:
        access_token_path.write_text(response['access_token'])
    finally:
        os.umask(previous_umask)

    return response['access_token']


@privileged
def list_registration_tokens() -> list[dict[str, str | int | None]]:
    """Return the current list of registration tokens."""
    if not action_utils.service_is_running('matrix-synapse'):
        return []

    access_token = _get_access_token()
    return _list_registration_tokens(access_token)


def _get_headers(access_token: str):
    """Return the common HTTP headers needed for synapse admin API.

    For details on authorization to the Admin API, see:
    https://matrix-org.github.io/synapse/latest/usage/administration/admin_api/index.html
    """
    return {'Authorization': f'Bearer {access_token}'}


def _list_registration_tokens(
        access_token: str) -> list[dict[str, str | int | None]]:
    """Use Admin API to fetch the list of registration tokens.

    For details on registration tokens API, see:
    https://matrix-org.github.io/synapse/latest/usage/administration/admin_api/registration_tokens.html
    """
    request = requests.get(ADMIN_API_BASE + 'registration_tokens',
                           headers=_get_headers(access_token))
    response = request.json()
    _parse_api_error(response)
    return response['registration_tokens']


def _create_registration_token():
    """Make sure that at least one registration token is created.

    For details on registration tokens API, see:
    https://matrix-org.github.io/synapse/latest/usage/administration/admin_api/registration_tokens.html
    """
    _ensure_server_is_running()

    access_token = _get_access_token()
    tokens = _list_registration_tokens(access_token)
    for token in tokens:
        if token['uses_allowed'] is None and token['expiry_time'] is None:
            # A token with unlimited uses and for unlimited time already
            # exists.
            return

    if not tokens:
        # API can generate a token for us but it includes special chars which
        # is awkward to deal with for users.
        token = utils.generate_password(size=12)
        request = requests.post(ADMIN_API_BASE + 'registration_tokens/new',
                                headers=_get_headers(access_token),
                                json={'token': token})
        response = request.json()
        _parse_api_error(response)


def _get_nonce() -> str:
    """Make a preliminary registration request to get a nonce.

    Nonce must be returned to the server during actual registration request. It
    is used in computation of MAC and prevents replay attacks.
    https://matrix-org.github.io/synapse/latest/admin_api/register_api.html
    """
    request = requests.get(ADMIN_API_BASE + 'register')
    response = request.json()
    _parse_api_error(response)
    return response['nonce']


def _generate_mac(shared_secret: str, nonce: str, user: str, password: str,
                  admin: bool = False, user_type=None) -> str:
    """Generate MAC using HMAC-SHA1 algorithm.

    For information on how to encode the data for MAC computation, see:
    https://matrix-org.github.io/synapse/latest/admin_api/register_api.html
    """
    mac = hmac.new(
        key=shared_secret.encode('utf8'),
        digestmod=hashlib.sha1,
    )

    mac.update(nonce.encode('utf8'))
    mac.update(b'\x00')
    mac.update(user.encode('utf8'))
    mac.update(b'\x00')
    mac.update(password.encode('utf8'))
    mac.update(b'\x00')
    mac.update(b'admin' if admin else b'notadmin')
    if user_type:
        mac.update(b'\x00')
        mac.update(user_type.encode('utf8'))

    return mac.hexdigest()


@privileged
def uninstall():
    """Delete configuration and data directories."""
    for item in ['/etc/matrix-synapse/conf.d', '/var/lib/matrix-synapse']:
        shutil.rmtree(item, ignore_errors=True)
