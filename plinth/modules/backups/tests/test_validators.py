# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for form field validators in backups.
"""

import pytest
from django.core.exceptions import ValidationError

from .. import split_path
from ..forms import repository_validator


def _validate_repository(valid_list, invalid_list, path_string):
    """Assert that repository strings in given list (in)validate properly."""
    for item in valid_list:
        repository_validator(path_string.format(item))

    for item in invalid_list:
        path = path_string.format(item)
        with pytest.raises(ValidationError):
            repository_validator(path)


def test_repository_paths_validation():
    """Test that repository strings are validated properly."""
    valid_paths = ['sshuser@10.0.2.2:~/backups']
    invalid_paths = [
        'mary had a little lamb', 'someone@example.com', 'www.example.com',
        'sshuser@hostname'
    ]
    path_string = '{}'
    _validate_repository(valid_paths, invalid_paths, path_string)


def test_repository_username_validation():
    """Test that usernames in repository string are validated properly."""
    valid_usernames = ['sshuser', 'cypher_punk-2077', '_user', '_-_']
    invalid_usernames = ['1two', 'somebody else']
    path_string = '{}@example.org:~/backups'
    _validate_repository(valid_usernames, invalid_usernames, path_string)


def test_repository_hostname_validation():
    """Test that hostnames in repository string are validated properly."""
    valid_hostnames = [
        '192.168.0.1', 'fe80::2078:6c26:498a:1fa5%wlps0', 'freedombox.org',
        '1.percent.org', 'freedombox', '::1'
    ]
    invalid_hostnames = ['192.fe80::2089:1fa5']
    path_string = 'user@{}:~/backups'
    _validate_repository(valid_hostnames, invalid_hostnames, path_string)


def test_repository_dir_path_validation():
    """Test that paths in repository string are validated properly."""
    valid_dir_paths = [
        '~/backups', '/home/user/backup-folder_1/', '', '/foo:bar/'
    ]
    invalid_dir_paths = []
    path_string = 'user@localhost:{}'
    _validate_repository(valid_dir_paths, invalid_dir_paths, path_string)


def test_respository_with_colon_path():
    """Test that a colon is possible in directory path."""
    _, hostname, path = split_path('user@fe80::2078:6c26:498a:1fa5:/foo:bar')
    assert hostname == 'fe80::2078:6c26:498a:1fa5'
    assert path == '/foo:bar'
