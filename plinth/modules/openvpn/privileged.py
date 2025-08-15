# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure OpenVPN server."""

import datetime
import os
import pathlib
import shutil
import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged

KEYS_DIRECTORY = pathlib.Path('/etc/openvpn/freedombox-keys')
CA_CERTIFICATE_PATH = KEYS_DIRECTORY / 'pki' / 'ca.crt'
USER_CERTIFICATE_PATH = KEYS_DIRECTORY / 'pki' / 'issued' / '{username}.crt'
USER_KEY_PATH = KEYS_DIRECTORY / 'pki' / 'private' / '{username}.key'
ATTR_FILE = KEYS_DIRECTORY / 'pki' / 'index.txt.attr'

SERVER_CONFIGURATION_PATH = '/etc/openvpn/server/freedombox.conf'

SERVICE_NAME = 'openvpn-server@freedombox'

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

_EASY_RSA_CONFIGURATION = {
    'EASYRSA_ALGO': 'ec',  # Use Elliptic Curve Cryptography by default
    'EASYRSA_BATCH': '1',  # Prevent prompting
    'EASYRSA_DIGEST': 'sha512',
    'EASYRSA_CA_EXPIRE': '3650',  # 10 years expiry for CA root certificate
    'EASYRSA_CERT_EXPIRE': '3650',  # 10 years expiry for server/client certs
    'EASYRSA_CERT_RENEW': '1095',  # Renew cert if expiry less than 3 years
    'EASYRSA_REQ_COUNTRY': 'US',
    'EASYRSA_REQ_PROVINCE': 'NY',
    'EASYRSA_REQ_CITY': 'New York',
    'EASYRSA_REQ_ORG': 'FreedomBox',
    'EASYRSA_REQ_EMAIL': 'me@freedombox',
    'EASYRSA_REQ_OU': 'Home',
}


@privileged
def setup():
    """Setup configuration, CA and certificates."""
    _write_server_config()
    _create_certificates()
    _setup_firewall()
    action_utils.service_try_restart(SERVICE_NAME)


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
            process = action_utils.run(
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


def _run_easy_rsa(args):
    """Execute easy-rsa command with some default arguments."""
    return action_utils.run(['/usr/share/easy-rsa/easyrsa'] + args,
                            cwd=KEYS_DIRECTORY, check=True)


def _write_easy_rsa_config():
    """Write easy-rsa 'vars' file."""
    with (KEYS_DIRECTORY / 'pki' / 'vars').open('w') as file_handle:
        for key, value in _EASY_RSA_CONFIGURATION.items():
            file_handle.write(f'set_var {key} "{value}"\n')


def _is_renewable(cert_name):
    """Return whether a certificate is within configured renewable days.

    'easy-rsa renewable' command could be used to perform the check. However,
    the script fetches the expiry date of the certificate from the index.txt
    file. When this file has multiple entries for the same certificate base
    name, the results of the command are undesirable. Multiple entries for the
    same certificate base name can occur in the index.txt file in some unusual
    cases. For example, earlier versions of FreedomBox ran build-server-full
    followed by gen-req/sign-req. This approach created such entries. So,
    determine expiry here without using easy-rsa script.
    """
    cert_path = KEYS_DIRECTORY / 'pki' / 'issued' / (cert_name + '.crt')
    if not cert_path.exists():
        return False

    process = action_utils.run(
        ['openssl', 'x509', '-noout', '-enddate', '-in',
         str(cert_path)], check=True, stdout=subprocess.PIPE)
    date_string = process.stdout.decode().strip().partition('=')[2]
    cert_expiry_time = datetime.datetime.strptime(date_string,
                                                  '%b %d %H:%M:%S %Y GMT')
    cert_expiry_time = cert_expiry_time.replace(tzinfo=datetime.timezone.utc)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    renew_period = datetime.timedelta(
        days=int(_EASY_RSA_CONFIGURATION['EASYRSA_CERT_RENEW']))
    return (cert_expiry_time - now) < renew_period


def _renew(cert_name):
    """Renew a certificate and revoke the old certificate.

    Without revoking the old certificate, another renewal is not possible due
    to safety checks in easy-rsa script.
    """
    _run_easy_rsa(['renew', cert_name, 'nopass'])

    # Remove the old certificate so that more renewals can work
    _run_easy_rsa(['revoke-renewed', cert_name])


def _create_certificates():
    """Generate CA and server certificates."""
    KEYS_DIRECTORY.mkdir(mode=0o700, exist_ok=True)

    # Don't re-initialize PKI if it already exists. This will lead to wiping of
    # all existing certificates and downloaded profiles.
    if not (KEYS_DIRECTORY / 'pki').is_dir():
        _run_easy_rsa(['init-pki'])

    _write_easy_rsa_config()

    # Don't reinitialize the CA certificates. This will invalidate all existing
    # server/client certificates and downloaded client profiles.
    if not CA_CERTIFICATE_PATH.exists():
        _run_easy_rsa(['build-ca', 'nopass'])

    # Renew server certificate if already exists. Already downloaded profiles
    # don't change.
    server_cert = KEYS_DIRECTORY / 'pki' / 'issued' / 'server.crt'
    if not server_cert.exists():
        _run_easy_rsa(['build-server-full', 'server', 'nopass'])
    elif _is_renewable('server'):
        _renew('server')


@privileged
def get_profile(username: str, remote_server: str) -> str:
    """Return the profile for a user."""
    if username == 'ca' or username == 'server':
        raise Exception('Invalid username')

    user_certificate = str(USER_CERTIFICATE_PATH).format(username=username)
    user_key = str(USER_KEY_PATH).format(username=username)

    if not _is_non_empty_file(user_certificate) or \
       not _is_non_empty_file(user_key):
        set_unique_subject('no')  # Set unique subject in attribute file to no
        _run_easy_rsa(['build-client-full', username, 'nopass'])
    elif _is_renewable(username):
        _renew(username)

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
    aug.set('/files' + str(ATTR_FILE) + '/unique_subject', value)
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
    aug.set('/augeas/load/Simplevars/incl[last() + 1]', str(ATTR_FILE))
    aug.load()
    return aug


@privileged
def uninstall():
    """Remove configuration directory for OpenVPN."""
    shutil.rmtree('/etc/openvpn', ignore_errors=True)
