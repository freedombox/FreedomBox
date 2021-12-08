# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test the Let's Encrypt component for managing certificates.
"""

import json
from unittest.mock import call, patch

import pytest

from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.names.components import DomainName, DomainType


@pytest.fixture(name='empty_letsencrypt_list', autouse=True)
def fixture_empty_letsencrypt_list():
    """Remove all entries from Let's Encrypt component list."""
    LetsEncrypt._all = {}


@pytest.fixture(name='component')
def fixture_component():
    """Create a new component for testing."""
    return LetsEncrypt(
        'test-component', domains=['valid.example', 'invalid.example'],
        daemons=['test-daemon'], should_copy_certificates=True,
        private_key_path='/etc/test-app/{domain}/private.path',
        certificate_path='/etc/test-app/{domain}/certificate.path',
        user_owner='test-user', group_owner='test-group',
        managing_app='test-app')


@pytest.fixture(name='get_status')
def fixture_get_status():
    """Return patched letsencrypt.get_status() method."""
    domains = ['valid.example']
    with patch('plinth.modules.letsencrypt.get_status') as get_status:
        get_status.return_value = {
            'domains': {
                domain: {
                    'lineage': '/etc/letsencrypt/live/' + domain,
                    'validity': 'valid',
                }
                for domain in domains
            }
        }
        yield get_status


@pytest.fixture(name='domain_list')
def fixture_domain_list():
    """Return patch DomainName.list() method."""
    method = 'plinth.modules.names.components.DomainName.list'
    with patch(method) as domain_list:
        DomainType._all = {}
        DomainType('domain-type-1', 'type-1', 'url1', False)
        DomainType('domain-type-2', 'type-2', 'url1', True)
        domain1 = DomainName('domain-name-1', 'invalid1.example',
                             'domain-type-1', '__all__')
        domain2 = DomainName('domain-name-2', 'valid.example', 'domain-type-2',
                             '__all__')
        domain3 = DomainName('domain-name-3', 'invalid2.example',
                             'domain-type-2', '__all__')
        domain_list.return_value = [domain1, domain2, domain3]
        yield domain_list


@pytest.fixture(name='superuser_run')
def fixture_superuser_run():
    """Return patched plinth.actions.superuser_run() method."""
    with patch('plinth.actions.superuser_run') as superuser_run:
        yield superuser_run


def test_init_without_arguments():
    """Test that component is initialized with defaults properly."""
    component = LetsEncrypt('test-component')

    assert component.component_id == 'test-component'
    assert component.domains is None
    assert component.daemons is None
    assert not component.should_copy_certificates
    assert component.private_key_path is None
    assert component.certificate_path is None
    assert component.user_owner is None
    assert component.group_owner is None
    assert component.managing_app is None
    assert len(component._all) == 1
    assert component._all['test-component'] == component


def test_init(component):
    """Test initializing the component."""
    assert component.domains == ['valid.example', 'invalid.example']
    assert component.daemons == ['test-daemon']
    assert component.should_copy_certificates
    assert component.private_key_path == '/etc/test-app/{domain}/private.path'
    assert component.certificate_path == \
        '/etc/test-app/{domain}/certificate.path'
    assert component.user_owner == 'test-user'
    assert component.group_owner == 'test-group'
    assert component.managing_app == 'test-app'


def test_init_values():
    """Test initializing with invalid values."""
    properties = {
        'private_key_path': 'test-private-key-path',
        'certificate_path': 'test-certificate-path',
        'user_owner': 'test-user',
        'group_owner': 'test-group',
        'managing_app': 'test-app'
    }
    LetsEncrypt('test-component', should_copy_certificates=True, **properties)
    for key in properties:
        new_properties = dict(properties)
        new_properties[key] = None
        with pytest.raises(ValueError):
            LetsEncrypt('test-component', should_copy_certificates=True,
                        **new_properties)


def test_domains():
    """Test getting domains."""
    component = LetsEncrypt('test-component', domains=lambda: ['test-domains'])
    assert component.domains == ['test-domains']


def test_list():
    """Test listing components."""
    component1 = LetsEncrypt('test-component1')
    component2 = LetsEncrypt('test-component2')
    assert set(LetsEncrypt.list()) == {component1, component2}


def _assert_copy_certificate_called(component, superuser_run, domains):
    """Check that copy certificate calls have been made properly."""
    copy_calls = [
        mock_call for mock_call in superuser_run.mock_calls
        if mock_call[1][0] == 'letsencrypt'
        and mock_call[1][1][0] == 'copy-certificate'
    ]
    expected_calls = []
    for domain, domain_status in domains.items():
        if domain_status == 'valid':
            source_private_key_path = \
                '/etc/letsencrypt/live/{}/privkey.pem'.format(domain)
            source_certificate_path = \
                '/etc/letsencrypt/live/{}/fullchain.pem'.format(domain)
        else:
            source_private_key_path = '/etc/ssl/private/ssl-cert-snakeoil.key'
            source_certificate_path = '/etc/ssl/certs/ssl-cert-snakeoil.pem'

        private_key_path = '/etc/test-app/{}/private.path'.format(domain)
        certificate_path = '/etc/test-app/{}/certificate.path'.format(domain)
        expected_call = call('letsencrypt', [
            'copy-certificate', '--managing-app', component.managing_app,
            '--user-owner', component.user_owner, '--group-owner',
            component.group_owner, '--source-private-key-path',
            str(source_private_key_path), '--source-certificate-path',
            str(source_certificate_path), '--private-key-path',
            private_key_path, '--certificate-path', certificate_path
        ])
        expected_calls.append(expected_call)

    assert len(expected_calls) == len(copy_calls)
    for expected_call in expected_calls:
        print(expected_call)
        print(copy_calls)
        assert expected_call in copy_calls


def _assert_restarted_daemons(daemons, superuser_run):
    """Check that a call has restarted the daemons of a component."""
    run_calls = [
        mock_call for mock_call in superuser_run.mock_calls
        if mock_call[1][0] == 'service'
    ]
    expected_calls = [
        call('service', ['try-restart', daemon]) for daemon in daemons
    ]
    assert len(expected_calls) == len(run_calls)
    for expected_call in expected_calls:
        assert expected_call in run_calls


def test_setup_certificates(superuser_run, get_status, component):
    """Test that initial copying of certs for an app works."""
    component.setup_certificates()
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'valid',
        'invalid.example': 'invalid'
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_setup_certificates_without_copy(superuser_run, get_status, component):
    """Test that initial copying of certs for an app works."""
    component.should_copy_certificates = False
    component.setup_certificates()
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_setup_certificates_with_app_domains(superuser_run, get_status,
                                             component):
    """Test that initial copying of certs for an app works."""
    component._domains = ['irrelevant1.example', 'irrelevant2.example']
    component.setup_certificates(
        app_domains=['valid.example', 'invalid.example'])
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'valid',
        'invalid.example': 'invalid'
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_setup_certificates_with_all_domains(domain_list, superuser_run,
                                             get_status, component):
    """Test that initial copying for certs works when app domains is '*'."""
    component._domains = '*'
    component.setup_certificates()
    _assert_copy_certificate_called(
        component, superuser_run, {
            'valid.example': 'valid',
            'invalid1.example': 'invalid',
            'invalid2.example': 'invalid'
        })
    _assert_restarted_daemons(component.daemons, superuser_run)


def _assert_compare_certificate_called(component, superuser_run, domains):
    """Check that compare certificate was called properly."""
    expected_calls = []
    for domain in domains:
        source_private_key_path = \
            '/etc/letsencrypt/live/{}/privkey.pem'.format(domain)
        source_certificate_path = \
            '/etc/letsencrypt/live/{}/fullchain.pem'.format(domain)
        private_key_path = '/etc/test-app/{}/private.path'.format(domain)
        certificate_path = '/etc/test-app/{}/certificate.path'.format(domain)
        expected_call = call('letsencrypt', [
            'compare-certificate', '--managing-app', component.managing_app,
            '--source-private-key-path',
            str(source_private_key_path), '--source-certificate-path',
            str(source_certificate_path), '--private-key-path',
            private_key_path, '--certificate-path', certificate_path
        ])
        expected_calls.append(expected_call)

    superuser_run.assert_has_calls(expected_calls)


def test_get_status(component, superuser_run, get_status):
    """Test that getting domain status works."""
    superuser_run.return_value = json.dumps({'result': True})
    assert component.get_status() == {
        'valid.example': 'valid',
        'invalid.example': 'self-signed'
    }
    _assert_compare_certificate_called(component, superuser_run,
                                       ['valid.example'])


def test_get_status_outdate_copy(component, superuser_run, get_status):
    """Test that getting domain status works with outdated copy."""
    superuser_run.return_value = json.dumps({'result': False})
    assert component.get_status() == {
        'valid.example': 'outdated-copy',
        'invalid.example': 'self-signed'
    }
    _assert_compare_certificate_called(component, superuser_run,
                                       ['valid.example'])


def test_get_status_without_copy(component, get_status):
    """Test that getting domain status works without copying."""
    component.should_copy_certificates = False
    assert component.get_status() == {
        'valid.example': 'valid',
        'invalid.example': 'self-signed'
    }


def test_on_certificate_obtained(superuser_run, component):
    """Test that certificate obtained event handler works."""
    component.on_certificate_obtained(['valid.example', 'irrelevant.example'],
                                      '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'valid',
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_obtained_with_all_domains(superuser_run, component):
    """Test that certificate obtained event handler works for app with
       all domains.
    """
    component._domains = '*'
    component.on_certificate_obtained(['valid.example'],
                                      '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'valid',
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_obtained_irrelevant(superuser_run, component):
    """Test that certificate obtained event handler works with
       irrelevant domain.
    """
    component.on_certificate_obtained(
        ['irrelevant.example'], '/etc/letsencrypt/live/irrelevant.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons([], superuser_run)


def test_on_certificate_obtained_without_copy(superuser_run, component):
    """Test that certificate obtained event handler works without copying."""
    component.should_copy_certificates = False
    component.on_certificate_obtained(['valid.example'],
                                      '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_renewed(superuser_run, component):
    """Test that certificate renewed event handler works."""
    component.on_certificate_renewed(['valid.example', 'irrelevant.example'],
                                     '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'valid',
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_renewed_irrelevant(superuser_run, component):
    """Test that certificate renewed event handler works for
       irrelevant domains.
"""
    component.on_certificate_renewed(
        ['irrelevant.example'], '/etc/letsencrypt/live/irrelevant.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons([], superuser_run)


def test_on_certificate_renewed_without_copy(superuser_run, component):
    """Test that certificate renewed event handler works without copying."""
    component.should_copy_certificates = False
    component.on_certificate_renewed(['valid.example'],
                                     '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_revoked(superuser_run, component):
    """Test that certificate revoked event handler works."""
    component.on_certificate_revoked(['valid.example', 'irrelevant.example'],
                                     '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'invalid',
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_revoked_irrelevant(superuser_run, component):
    """Test that certificate revoked event handler works for
       irrelevant domains.
    """
    component.on_certificate_revoked(
        ['irrelevant.example'], '/etc/letsencrypt/live/irrelevant.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons([], superuser_run)


def test_on_certificate_revoked_without_copy(superuser_run, component):
    """Test that certificate revoked event handler works without copying."""
    component.should_copy_certificates = False
    component.on_certificate_revoked(['valid.example'],
                                     '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_deleted(superuser_run, component):
    """Test that certificate deleted event handler works."""
    component.on_certificate_deleted(['valid.example', 'irrelevant.example'],
                                     '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {
        'valid.example': 'invalid',
    })
    _assert_restarted_daemons(component.daemons, superuser_run)


def test_on_certificate_deleted_irrelevant(superuser_run, component):
    """Test that certificate deleted event handler works for
       irrelevant domains.
    """
    component.on_certificate_deleted(
        ['irrelevant.example'], '/etc/letsencrypt/live/irrelevant.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons([], superuser_run)


def test_on_certificate_deleted_without_copy(superuser_run, component):
    """Test that certificate deleted event handler works without copying."""
    component.should_copy_certificates = False
    component.on_certificate_deleted(['valid.example'],
                                     '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, superuser_run, {})
    _assert_restarted_daemons(component.daemons, superuser_run)
