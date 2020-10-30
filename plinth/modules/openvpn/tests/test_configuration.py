# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for OpenVPN configuration.
"""

import os
from unittest.mock import patch

import pytest

from plinth.modules import openvpn


@pytest.fixture(name='conf_file')
def fixture_conf_file(tmp_path):
    """Fixture that returns an empty configuration file."""
    return str(tmp_path / 'freedombox.conf')


def test_identify_rsa_configuration(conf_file):
    """Identify RSA configuration based on configuration file."""
    with patch('plinth.modules.openvpn.SERVER_CONFIGURATION_FILE', conf_file):
        with open(conf_file, 'w') as file_handle:
            file_handle.write('dh /etc/openvpn/freedombox-keys/pki/dh.pem')
        assert not openvpn.is_using_ecc()


def test_identify_ecc_configuration(conf_file):
    """Identify ECC configuration based on configuration file."""
    with patch('plinth.modules.openvpn.SERVER_CONFIGURATION_FILE', conf_file):
        with open(conf_file, 'w') as file_handle:
            file_handle.write('dh none')
        assert openvpn.is_using_ecc()


def test_is_setup_with_rsa(keys_directory, call_action):
    """is_setup should work with RSA configuration."""
    with patch('plinth.actions.superuser_run', call_action):
        (keys_directory / 'pki').mkdir()
        dh_params_file = keys_directory / 'pki' / 'dh.pem'
        dh_params_file.write_text('some content')
        assert openvpn.is_setup()
        os.remove(dh_params_file)


def test_is_setup_with_ecc(keys_directory, call_action):
    """is_setup should work with RSA configuration."""
    with patch('plinth.actions.superuser_run', call_action):
        (keys_directory / 'pki' / 'ecparams').mkdir(parents=True)
        ec_params_file = keys_directory / 'pki' / 'ecparams' / 'secp521r1.pem'
        ec_params_file.write_text('some content')
        assert openvpn.is_setup()
        os.remove(ec_params_file)
