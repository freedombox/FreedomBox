# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for privileged snapshot operations.
"""

import pathlib

import pytest

from plinth.modules.snapshot import privileged

systemctl_path = pathlib.Path('/usr/bin/systemctl')
systemd_installed = pytest.mark.skipif(not systemctl_path.exists(),
                                       reason='systemd not available')


@pytest.mark.parametrize('input_path,escaped_path',
                         [('.snapshots', '\\x2esnapshots'), ('/', '-'),
                          ('/home/user', 'home-user'), (':_.', ':_.')])
@systemd_installed
def test_systemd_path_escape(input_path, escaped_path):
    """Test escaping systemd paths."""
    assert escaped_path == privileged._systemd_path_escape(input_path)
