# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure OpenVPN server."""

import os
import shutil
import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged

KEYS_DIRECTORY = '/etc/openvpn/freedombox-keys'

DH_PARAMS = f'{KEYS_DIRECTORY}/pki/dh.pem'

EC_PARAMS_DIR = f'{KEYS_DIRECTORY}/pki/ecparams'

SERVER_CONFIGURATION_PATH = '/etc/openvpn/server/freedombox.conf'

SERVICE_NAME = 'openvpn-server@freedombox'

CA_CERTIFICATE_PATH = os.path.join(KEYS_DIRECTORY, 'pki', 'ca.crt')
USER_CERTIFICATE_PATH = os.path.join(KEYS_DIRECTORY, 'pki', 'issued',
                                     '{username}.crt')
USER_KEY_PATH = os.path.join(KEYS_DIRECTORY, 'pki', 'private',
                             '{username}.key')
ATTR_FILE = os.path.join(KEYS_DIRECTORY, 'pki', 'index.txt.attr')

SERVER_CONFIGURATION = '''
port 1194
proto udp
proto udp6
dev tun

client-to-client

ca /etc/openvpn/freedombox-keys/pki/ca.crt
cert /etc/openvpn/freedombox-keys/pki/issued/server.crt
key /etc/openvpn/freedombox-keys/pki/private/server.key

dh none

server 10.91.0.0 255.255.255.0
keepalive 10 120
verb 3

tls-server
tls-version-min 1.2
cipher AES-256-CBC
script-security 2
'''

CLIENT_CONFIGURATION = '''
client
remote {remote} 1194
proto udp
proto udp6
dev tun
nobind
remote-cert-tls server
cipher AES-256-CBC
redirect-gateway
verb 3
<ca>
{ca}</ca>
<cert>
{cert}</cert>
<key>
{key}</key>'''

CERTIFICATE_CONFIGURATION = {
    'EASYRSA_ALGO': 'ec',
    'EASYRSA_BATCH': '1',
    'EASYRSA_DIGEST': 'sha512',
    'KEY_CONFIG': '/usr/share/easy-rsa/openssl-easyrsa.cnf',
    'KEY_DIR': KEYS_DIRECTORY,
    'EASYRSA_OPENSSL': 'openssl',
    'EASYRSA_CA_EXPIRE': '3650',
    'EASYRSA_CERT_EXPIRE': '3650',
    'EASYRSA_REQ_COUNTRY': 'US',
    'EASYRSA_REQ_PROVINCE': 'NY',
    'EASYRSA_REQ_CITY': 'New York',
    'EASYRSA_REQ_ORG': 'FreedomBox',
    'EASYRSA_REQ_EMAIL': 'me@freedombox',
    'EASYRSA_REQ_OU': 'Home',
    'EASYRSA_REQ_NAME': 'FreedomBox'
}

COMMON_ARGS = {'env': CERTIFICATE_CONFIGURATION, 'cwd': KEYS_DIRECTORY}


@privileged
def setup():
    """Setup configuration, CA and certificates."""
    _write_server_config()
    _create_certificates()
    _setup_firewall()
    action_utils.service_enable(SERVICE_NAME)
    action_utils.service_restart(SERVICE_NAME)


def _write_server_config():
    """Write server configuration."""
    with open(SERVER_CONFIGURATION_PATH, 'w', encoding='utf-8') as file_handle:
        file_handle.write(SERVER_CONFIGURATION)


def _setup_firewall():
    """Add TUN device to internal zone in firewalld."""

    def _configure_interface(interface, operation):
        """Add or remove an interface into internal zone."""
        command = [
            'firewall-cmd', '--zone', 'internal',
            '--{}-interface'.format(operation), interface
        ]
        subprocess.call(command)
        subprocess.call(command + ['--permanent'])

    def _is_tunplus_enabled():
        """Return whether tun+ interface is already added."""
        try:
            process = subprocess.run(
                ['firewall-cmd', '--zone', 'internal', '--list-interfaces'],
                stdout=subprocess.PIPE, check=True)
            return 'tun+' in process.stdout.decode().strip().split()
        except subprocess.CalledProcessError:
            return True  # Safer

    # XXX: Due to https://bugs.debian.org/919517 when tun+ interface is added,
    # firewalld is unable to handle it in nftables backend causing firewalld to
    # break while applying rules. This makes the entire system unreachable.
    # Hack around the problem by adding a few tun interfaces into the internal
    # zone. Hopefully, OpenVPN setting 'dev tun' will end up using one of those
    # if the tun devices are not used by other services. When the issue is
    # fixed, use tun+ instead.
    is_tunplus_set = _is_tunplus_enabled()
    _configure_interface('tun+', 'remove')
    for index in range(8):
        _configure_interface('tun{}'.format(index), 'add')

    if is_tunplus_set:
        action_utils.service_restart('firewalld')


def _init_pki():
    """Initialize easy-rsa PKI directory to create configuration file."""
    subprocess.check_call(['/usr/share/easy-rsa/easyrsa', 'init-pki'],
                          **COMMON_ARGS)


def _create_certificates():
    """Generate CA and server certificates."""
    try:
        os.mkdir(KEYS_DIRECTORY, 0o700)
    except FileExistsError:
        pass

    _init_pki()
    easy_rsa = '/usr/share/easy-rsa/easyrsa'
    subprocess.check_call([easy_rsa, 'build-ca', 'nopass'], **COMMON_ARGS)
    subprocess.check_call([easy_rsa, 'build-server-full', 'server', 'nopass'],
                          **COMMON_ARGS)


@privileged
def get_profile(username: str, remote_server: str) -> str:
    """Return the profile for a user."""
    if username == 'ca' or username == 'server':
        raise Exception('Invalid username')

    user_certificate = USER_CERTIFICATE_PATH.format(username=username)
    user_key = USER_KEY_PATH.format(username=username)

    if not _is_non_empty_file(user_certificate) or \
       not _is_non_empty_file(user_key):
        set_unique_subject('no')  # Set unique subject in attribute file to no
        subprocess.check_call([
            '/usr/share/easy-rsa/easyrsa', 'build-client-full', username,
            'nopass'
        ], env=CERTIFICATE_CONFIGURATION, cwd=KEYS_DIRECTORY)

    user_certificate_string = _read_file(user_certificate)
    user_key_string = _read_file(user_key)
    ca_string = _read_file(CA_CERTIFICATE_PATH)

    return CLIENT_CONFIGURATION.format(ca=ca_string,
                                       cert=user_certificate_string,
                                       key=user_key_string,
                                       remote=remote_server)


def set_unique_subject(value):
    """Set the unique_subject value to a particular value."""
    aug = load_augeas()
    aug.set('/files' + ATTR_FILE + '/unique_subject', value)
    aug.save()


def _read_file(filename):
    """Return the entire contents of a file as string."""
    with open(filename, 'r', encoding='utf-8') as file_handle:
        return ''.join(file_handle.readlines())


def _is_non_empty_file(filepath):
    """Return whether a file exists and is not zero size."""
    return os.path.isfile(filepath) and os.path.getsize(filepath) > 0


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)

    # shell-script config file lens
    aug.set('/augeas/load/Simplevars/lens', 'Simplevars.lns')
    aug.set('/augeas/load/Simplevars/incl[last() + 1]', ATTR_FILE)
    aug.load()
    return aug


@privileged
def uninstall():
    """Remove configuration directory for OpenVPN."""
    shutil.rmtree('/etc/openvpn', ignore_errors=True)
