# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test actions for configuring bind
"""
from pathlib import Path

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


@pytest.fixture
def bind_zones_folder(tmp_path):
    """Setup the a bind configuration file temporary directory."""
    test_zone_file = """
;
; BIND data file for local loopback interface
;
$TTL	604800
@	IN	SOA	{name} root.localhost. (
			      2		; Serial
			 604800		; Refresh
			  86400		; Retry
			2419200		; Expire
			 604800 )	; Negative Cache TTL
;
@	IN	NS	{name}
@	IN	A	{a_record}
@	IN	AAAA	{aaaa_record}
    """ # noqa

    old_zones_dir = bind.ZONES_DIR
    bind.ZONES_DIR = tmp_path
    zones_dir_path = Path(bind.ZONES_DIR)
    zones_dir_path.mkdir(exist_ok=True, parents=True)

    local_path = zones_dir_path / "local.zone"
    local_path.write_text(
        test_zone_file.format(name='localhost.', a_record="127.0.0.1",
                              aaaa_record="::1")
    )

    custom_zone_path = zones_dir_path / "custom.zone"
    custom_zone_path.write_text(
        test_zone_file.format(name='custom.domain.', a_record="10.10.10.1",
                              aaaa_record="fe80::c6e9:84ff:fe16:95da")
    )

    yield

    local_path.unlink()
    custom_zone_path.unlink()
    bind.ZONES_DIR = old_zones_dir


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


@pytest.mark.usefixtures('bind_zones_folder')
def test_get_correct_served_domains():
    """
    Test that get_served_domains collects the right a/aaaa records from zone
    files
    """
    served_domains = bind.get_served_domains()

    assert served_domains['localhost.'] == ["127.0.0.1", "::1"]
    assert served_domains['custom.domain.'] == [
        "10.10.10.1", "fe80::c6e9:84ff:fe16:95da"]
