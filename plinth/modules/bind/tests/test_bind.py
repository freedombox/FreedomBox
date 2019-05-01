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
Test actions for configuring bind
"""

import pytest

from plinth.modules import bind


@pytest.fixture(name='configuration_file')
def fixture_configuration_file(tmp_path):
    """Setup the a bind configuration file temporary directory."""
    conf_file = tmp_path / 'named.conf.options'
    conf_file.write_text(bind.DEFAULT_CONFIG)
    old_config_file = bind.CONFIG_FILE
    bind.CONFIG_FILE = str(conf_file)
    yield
    bind.CONFIG_FILE = old_config_file


@pytest.mark.usefixtures('configuration_file')
def test_set_forwarders():
    """Test that setting forwarders works."""
    bind.set_forwarders('8.8.8.8 8.8.4.4')
    conf = bind.get_config()
    assert conf['forwarders'] == '8.8.8.8 8.8.4.4'

    bind.set_forwarders('')
    conf = bind.get_config()
    assert conf['forwarders'] == ''


@pytest.mark.usefixtures('configuration_file')
def test_enable_dnssec():
    """Test that enabling DNSSEC works."""
    bind.set_dnssec('enable')
    conf = bind.get_config()
    assert conf['enable_dnssec']

    bind.set_dnssec('disable')
    conf = bind.get_config()
    assert not conf['enable_dnssec']
