# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure infinoted."""

import grp
import os
import pathlib
import pwd
import shutil
import subprocess
import time

from plinth import action_utils
from plinth.actions import privileged

DATA_DIR = '/var/lib/infinoted'
KEY_DIR = '/etc/infinoted'
SYNC_DIR = os.path.join(DATA_DIR, 'sync')

CONF_PATH = '/etc/xdg/infinoted.conf'
CONF = f'''
[infinoted]

# Possible values : no-tls, allow-tls, require-tls
security-policy=require-tls

# Absolute path of the certificate file.
certificate-file=/etc/infinoted/infinoted-cert.pem

# Absolute path of the private key file.
key-file=/etc/infinoted/infinoted-key.pem

# Enable plugins
plugins=note-text;autosave;logging;directory-sync

# Specify a path to use a root certificate instead of a certificate-key pair.
#certificate-chain=

#password=

# Automatically save documents every few seconds
[autosave]

# Setting this to 0 disables autosave.
interval=60

# Synchronize files to another directory in plain text format
[directory-sync]

# Directory to sync plain text files
directory={SYNC_DIR}

# Synchronize seconds
interval=60

# Log additional events
[logging]

# Log when users connect or disconnect
log-connections=true

# Log errors with client connections such as a connection reset
log-connection-errors=true
'''

SYSTEMD_SERVICE_PATH = '/etc/systemd/system/infinoted.service'
SYSTEMD_SERVICE = '''
#
# This file is managed and overwritten by Plinth.  If you wish to edit
# it, disable infinoted in Plinth, remove this file and manage it manually.
#

[Unit]
Description=collaborative text editor service
Documentation=man:infinoted(1)
After=network.target

[Service]
User=infinoted
Group=infinoted
ExecStart=/usr/bin/infinoted
ConfigurationDirectory=infinoted
ConfigurationDirectoryMode=0750
LockPersonality=yes
NoNewPrivileges=yes
PrivateDevices=yes
PrivateMounts=yes
PrivateTmp=yes
ProtectControlGroups=yes
ProtectHome=yes
ProtectKernelLogs=yes
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectSystem=full
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictRealtime=yes
StateDirectory=infinoted
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
'''


def _kill_daemon():
    """Try to kill the infinoted daemon for upto 5 minutes."""
    end_time = time.time() + 300
    while time.time() < end_time:
        try:
            action_utils.run(['infinoted', '--kill-daemon'], check=True)
            break
        except subprocess.CalledProcessError:
            pass

        time.sleep(1)


@privileged
def setup():
    """Configure infinoted after install."""
    if not os.path.isfile(CONF_PATH):
        with open(CONF_PATH, 'w', encoding='utf-8') as file_handle:
            file_handle.write(CONF)

    with open(SYSTEMD_SERVICE_PATH, 'w', encoding='utf-8') as file_handle:
        file_handle.write(SYSTEMD_SERVICE)

    action_utils.service_daemon_reload()

    # Create infinoted group if needed.
    try:
        grp.getgrnam('infinoted')
    except KeyError:
        action_utils.run(['addgroup', '--system', 'infinoted'], check=True)

    # Create infinoted user if needed.
    try:
        pwd.getpwnam('infinoted')
    except KeyError:
        action_utils.run([
            'adduser', '--system', '--ingroup', 'infinoted', '--home',
            DATA_DIR, '--gecos', 'Infinoted collaborative editing server',
            'infinoted'
        ], check=True)

    for directory in (DATA_DIR, KEY_DIR, SYNC_DIR):
        if not os.path.exists(directory):
            os.makedirs(directory, mode=0o750)
        shutil.chown(directory, user='infinoted', group='infinoted')

    if not os.path.exists(KEY_DIR + '/infinoted-cert.pem'):
        old_umask = os.umask(0o027)
        try:
            # infinoted doesn't have a "create key and exit" mode. Run as
            # daemon so we can stop after.
            action_utils.run([
                'infinoted', '--create-key', '--create-certificate',
                '--daemonize'
            ], check=True)
            _kill_daemon()
        finally:
            os.umask(old_umask)

    # Always check the ownership of certificate files, in case setup
    # failed previously.
    shutil.chown(KEY_DIR + '/infinoted-cert.pem', user='infinoted',
                 group='infinoted')
    shutil.chown(KEY_DIR + '/infinoted-key.pem', user='infinoted',
                 group='infinoted')


@privileged
def uninstall():
    """Remove data, certs, config and systemd unit files."""
    for directory in DATA_DIR, KEY_DIR:
        shutil.rmtree(directory, ignore_errors=True)

    for file_ in CONF_PATH, SYSTEMD_SERVICE_PATH:
        pathlib.Path(file_).unlink(missing_ok=True)
