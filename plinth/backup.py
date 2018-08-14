#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Utility methods for providing backup information.
"""


def validate(backup):
    """Validate the backup' information schema."""
    assert isinstance(backup, dict)

    assert 'config' in backup
    assert isinstance(backup['config'], dict)
    _validate_directories_and_files(backup['config'])

    assert 'data' in backup
    assert isinstance(backup['data'], dict)
    _validate_directories_and_files(backup['data'])

    assert 'secrets' in backup
    assert isinstance(backup['secrets'], dict)
    _validate_directories_and_files(backup['secrets'])

    assert 'services' in backup
    assert isinstance(backup['services'], list)

    return backup


def _validate_directories_and_files(df):
    """Validate directories and files structure."""
    assert 'directories' in df
    assert isinstance(df['directories'], list)
    assert 'files' in df
    assert isinstance(df['files'], list)
