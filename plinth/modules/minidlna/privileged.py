# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure minidlna server."""

import subprocess
from os import chmod, fdopen, remove, stat
from shutil import move
from tempfile import mkstemp

import augeas

from plinth import action_utils
from plinth.actions import privileged
from plinth.utils import grep

CONFIG_PATH = '/etc/minidlna.conf'

SYSCTL_CONF = '''# This file is managed and overwritten by FreedomBox.
# Helps minidlna monitor changes in large media directories
fs.inotify.max_user_watches = 100000
'''


def _undo_old_configuration_changes():
    """Restore /etc/sysctl.conf to before our changes.

    Older version of minidlna app in FreedomBox < 20.9 wrote to
    /etc/sysctl.conf directly. This will cause conffile prompt during upgrade
    of procps package. Undo the changes so that upgrade can happen smoothly.

    """
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Sysctl/lens', 'Sysctl.lns')
    aug.set('/augeas/load/Sysctl/incl[last() + 1]', '/etc/sysctl.conf')
    aug.load()

    key_path = '/files/etc/sysctl.conf/fs.inotify.max_user_watches'
    if aug.get(key_path) == '100000':
        aug.remove(key_path)
        aug.save()


@privileged
def setup():
    """Increase inotify watches per folder.

    This is to allow minidlna to monitor changes in large media-dirs.
    """
    _undo_old_configuration_changes()
    with open('/etc/sysctl.d/50-freedombox-minidlna.conf', 'w',
              encoding='utf-8') as conf:
        conf.write(SYSCTL_CONF)

    subprocess.run(['systemctl', 'restart', 'systemd-sysctl'], check=True)


@privileged
def get_media_dir() -> str:
    """Retrieve media directory from minidlna.conf."""
    line = grep('^media_dir=', CONFIG_PATH)
    return line[0].split('=')[1]


@privileged
def set_media_dir(media_dir: str):
    """Set media directory in minidlna.conf."""
    line = grep('^media_dir=', CONFIG_PATH)[0]

    new_line = 'media_dir=%s\n' % media_dir
    replace_in_config_file(CONFIG_PATH, line, new_line)
    if action_utils.service_is_running('minidlna'):
        action_utils.service_restart('minidlna')


def replace_in_config_file(file_path, pattern, subst):
    """Replace a directive in configuration file.

    - Create a temporary minidlna.conf file
    - Replace the media dir config
    - Remove original one and move the temporary file
    - Preserve permissions as the original file
    """
    temp_file, temp_file_path = mkstemp()
    with fdopen(temp_file, 'w') as new_file:
        with open(file_path, encoding='utf-8') as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))

    old_st_mode = stat(file_path).st_mode
    remove(file_path)
    move(temp_file_path, file_path)
    chmod(file_path, old_st_mode)
