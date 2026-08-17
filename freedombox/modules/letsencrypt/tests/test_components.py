# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test the Let's Encrypt component for managing certificates.
"""

import contextlib
import random
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
    reload_daemons = random.choice([True, False])
    component = LetsEncrypt(
        'test-component', domains=['valid.example', 'invalid.example'],
        daemons=['test-daemon'], should_copy_certificates=True,
        private_key_path='/etc/test-app/{domain}/private.path',
        certificate_path='/etc/test-app/{domain}/certificate.path',
        user_owner='test-user', group_owner='test-group',
        managing_app='test-app', reload_daemons=reload_daemons)
    assert component.reload_daemons == reload_daemons
    return component


@pytest.fixture(name='copy_certificate')
def fixture_copy_certificate():
    """Patch and return privileged.copy_certificate call."""
    with patch('plinth.modules.letsencrypt.privileged.copy_certificate'
               ) as copy_certificate:
        yield copy_certificate


@pytest.fixture(name='compare_certificate')
def fixture_compare_certificate():
    """Patch and return privileged.compare_certificate call."""
    with patch('plinth.modules.letsencrypt.privileged.compare_certificate'
               ) as compare_certificate:
        yield compare_certificate


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
    assert not component.reload_daemons
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


def _assert_copy_certificate_called(component, copy_certificate, domains):
    """Check that copy certificate calls have been made properly."""
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
        expected_call = call(component.managing_app,
                             str(source_private_key_path),
                             str(source_certificate_path), private_key_path,
                             certificate_path, component.user_owner,
                             component.group_owner)
        expected_calls.append(expected_call)

    copy_certificate.assert_has_calls(expected_calls, any_order=True)


@contextlib.contextmanager
def _assert_restarted_daemons(component, daemons=None):
    """Check that a call has restarted the daemons of a component."""
    daemons = daemons if daemons is not None else component.daemons

    expected_calls = [call(daemon) for daemon in daemons]
    with patch('plinth.privileged.service.try_reload_or_restart'
               ) as try_reload_or_restart, patch(
                   'plinth.privileged.service.try_restart') as try_restart:
        yield

        if component.reload_daemons:
            try_reload_or_restart.assert_has_calls(expected_calls,
                                                   any_order=True)
            try_restart.assert_not_called()
        else:
            try_restart.assert_has_calls(expected_calls, any_order=True)
            try_reload_or_restart.assert_not_called()


def test_setup_certificates(copy_certificate, get_status, component):
    """Test that initial copying of certs for an app works."""
    with _assert_restarted_daemons(component):
        component.setup_certificates()

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'valid',
        'invalid.example': 'invalid'
    })


def test_setup_certificates_without_copy(copy_certificate, get_status,
                                         component):
    """Test that initial copying of certs for an app works."""
    component.should_copy_certificates = False
    with _assert_restarted_daemons(component):
        component.setup_certificates()

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_setup_certificates_with_app_domains(copy_certificate, get_status,
                                             component):
    """Test that initial copying of certs for an app works."""
    component._domains = ['irrelevant1.example', 'irrelevant2.example']
    with _assert_restarted_daemons(component):
        component.setup_certificates(
            app_domains=['valid.example', 'invalid.example'])

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'valid',
        'invalid.example': 'invalid'
    })


def test_setup_certificates_with_all_domains(domain_list, copy_certificate,
                                             get_status, component):
    """Test that initial copying for certs works when app domains is '*'."""
    component._domains = '*'
    with _assert_restarted_daemons(component):
        component.setup_certificates()

    _assert_copy_certificate_called(
        component, copy_certificate, {
            'valid.example': 'valid',
            'invalid1.example': 'invalid',
            'invalid2.example': 'invalid'
        })


def _assert_compare_certificate_called(component, compare_certificate,
                                       domains):
    """Check that compare certificate was called properly."""
    expected_calls = []
    for domain in domains:
        source_private_key_path = \
            '/etc/letsencrypt/live/{}/privkey.pem'.format(domain)
        source_certificate_path = \
            '/etc/letsencrypt/live/{}/fullchain.pem'.format(domain)
        private_key_path = '/etc/test-app/{}/private.path'.format(domain)
        certificate_path = '/etc/test-app/{}/certificate.path'.format(domain)
        expected_call = call(component.managing_app,
                             str(source_private_key_path),
                             str(source_certificate_path), private_key_path,
                             certificate_path)
        expected_calls.append(expected_call)

    compare_certificate.assert_has_calls(expected_calls, any_order=True)


def test_get_status(component, compare_certificate, get_status):
    """Test that getting domain status works."""
    compare_certificate.return_value = True
    assert component.get_status() == {
        'valid.example': 'valid',
        'invalid.example': 'self-signed'
    }
    _assert_compare_certificate_called(component, compare_certificate,
                                       ['valid.example'])


def test_get_status_outdate_copy(component, compare_certificate, get_status):
    """Test that getting domain status works with outdated copy."""
    compare_certificate.return_value = False
    assert component.get_status() == {
        'valid.example': 'outdated-copy',
        'invalid.example': 'self-signed'
    }
    _assert_compare_certificate_called(component, compare_certificate,
                                       ['valid.example'])


def test_get_status_without_copy(component, get_status):
    """Test that getting domain status works without copying."""
    component.should_copy_certificates = False
    assert component.get_status() == {
        'valid.example': 'valid',
        'invalid.example': 'self-signed'
    }


def test_on_certificate_obtained(copy_certificate, component):
    """Test that certificate obtained event handler works."""
    with _assert_restarted_daemons(component):
        component.on_certificate_obtained(
            ['valid.example', 'irrelevant.example'],
            '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'valid',
    })


def test_on_certificate_obtained_with_all_domains(copy_certificate, component):
    """Test that certificate obtained event handler works for app with
       all domains.
    """
    component._domains = '*'
    with _assert_restarted_daemons(component):
        component.on_certificate_obtained(
            ['valid.example'], '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'valid',
    })


def test_on_certificate_obtained_irrelevant(copy_certificate, component):
    """Test that certificate obtained event handler works with
       irrelevant domain.
    """
    with _assert_restarted_daemons(component, []):
        component.on_certificate_obtained(
            ['irrelevant.example'],
            '/etc/letsencrypt/live/irrelevant.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_obtained_without_copy(copy_certificate, component):
    """Test that certificate obtained event handler works without copying."""
    component.should_copy_certificates = False
    with _assert_restarted_daemons(component):
        component.on_certificate_obtained(
            ['valid.example'], '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_renewed(copy_certificate, component):
    """Test that certificate renewed event handler works."""
    with _assert_restarted_daemons(component):
        component.on_certificate_renewed(
            ['valid.example', 'irrelevant.example'],
            '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'valid',
    })


def test_on_certificate_renewed_irrelevant(copy_certificate, component):
    """Test that cert renewed event handler works for irrelevant domains."""
    with _assert_restarted_daemons(component, []):
        component.on_certificate_renewed(
            ['irrelevant.example'],
            '/etc/letsencrypt/live/irrelevant.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_renewed_without_copy(copy_certificate, component):
    """Test that certificate renewed event handler works without copying."""
    component.should_copy_certificates = False
    with _assert_restarted_daemons(component):
        component.on_certificate_renewed(
            ['valid.example'], '/etc/letsencrypt/live/valid.example/')
    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_revoked(copy_certificate, component):
    """Test that certificate revoked event handler works."""
    with _assert_restarted_daemons(component):
        component.on_certificate_revoked(
            ['valid.example', 'irrelevant.example'],
            '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'invalid',
    })


def test_on_certificate_revoked_irrelevant(copy_certificate, component):
    """Test that certificate revoked event handler works for
       irrelevant domains.
    """
    with _assert_restarted_daemons(component, []):
        component.on_certificate_revoked(
            ['irrelevant.example'],
            '/etc/letsencrypt/live/irrelevant.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_revoked_without_copy(copy_certificate, component):
    """Test that certificate revoked event handler works without copying."""
    component.should_copy_certificates = False
    with _assert_restarted_daemons(component):
        component.on_certificate_revoked(
            ['valid.example'], '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_deleted(copy_certificate, component):
    """Test that certificate deleted event handler works."""
    with _assert_restarted_daemons(component):
        component.on_certificate_deleted(
            ['valid.example', 'irrelevant.example'],
            '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {
        'valid.example': 'invalid',
    })


def test_on_certificate_deleted_irrelevant(copy_certificate, component):
    """Test that certificate deleted event handler works for
       irrelevant domains.
    """
    with _assert_restarted_daemons(component, []):
        component.on_certificate_deleted(
            ['irrelevant.example'],
            '/etc/letsencrypt/live/irrelevant.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})


def test_on_certificate_deleted_without_copy(copy_certificate, component):
    """Test that certificate deleted event handler works without copying."""
    component.should_copy_certificates = False
    with _assert_restarted_daemons(component):
        component.on_certificate_deleted(
            ['valid.example'], '/etc/letsencrypt/live/valid.example/')

    _assert_copy_certificate_called(component, copy_certificate, {})
