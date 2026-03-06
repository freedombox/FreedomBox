# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test the components provides by oidc app."""

from unittest.mock import patch

import pytest
from oauth2_provider.models import Application

from ..components import OpenIDConnect


@pytest.fixture(name='openid_connect')
def fixture_openid_connect():
    """Return an OpenIDConnect object."""
    return OpenIDConnect(
        'test-openidconnect', 'test-client', 'Test Client',
        ['https://testdomain.example/a', 'https://{domain}/b'])


def test_openidconnect_init():
    """Test initialization of openidconnect object."""
    component = OpenIDConnect('test-openidconnect', 'test-client',
                              'Test Client', ['https://testdomain.example/a'])
    assert component.component_id == 'test-openidconnect'
    assert component.client_id == 'test-client'
    assert component.name == 'Test Client'
    assert component.redirect_uris == ['https://testdomain.example/a']
    assert component.post_logout_redirect_uris == ''
    assert component.client_type == Application.CLIENT_CONFIDENTIAL
    assert component.authorization_grant_type == \
        Application.GRANT_AUTHORIZATION_CODE
    assert component.algorithm == Application.HS256_ALGORITHM
    assert not component.hash_client_secret
    assert not component.skip_authorization

    component = OpenIDConnect('test-openidconnect', 'test-client',
                              'Test Client', ['https://testdomain.example/a'],
                              skip_authorization=True)
    assert component.skip_authorization


@pytest.mark.django_db
def test_get_client_secret(openid_connect):
    """Test retrieving client secret."""
    with pytest.raises(Application.DoesNotExist):
        openid_connect.get_client_secret()

    openid_connect.setup(old_version=0)
    assert len(openid_connect.get_client_secret()) == 128


@pytest.mark.django_db
@patch('plinth.modules.names.components.DomainName.list_names')
def test_setup(list_names, openid_connect):
    """Test creating a DB object."""
    list_names.return_value = ('a.example', 'b.example')
    expected_redirect_uris = [
        'https://testdomain.example/a', 'https://a.example/b',
        'https://b.example/b', 'https://localhost/b'
    ]
    expected_origins = [
        'https://a.example', 'https://b.example', 'https://localhost'
    ]

    # Test creating fresh DB entry
    openid_connect.setup(old_version=0)
    obj = Application.objects.get(client_id=openid_connect.client_id)
    assert obj.client_id == openid_connect.client_id
    assert len(obj.client_secret) == 128
    assert not obj.user
    assert set(obj.redirect_uris.split(' ')) == set(expected_redirect_uris)
    assert obj.post_logout_redirect_uris == ''
    assert obj.client_type == Application.CLIENT_CONFIDENTIAL
    assert obj.authorization_grant_type == Application.GRANT_AUTHORIZATION_CODE
    assert not obj.hash_client_secret
    assert obj.name == 'Test Client'
    assert obj.algorithm == Application.HS256_ALGORITHM
    assert set(obj.allowed_origins.split(' ')) == set(expected_origins)
    assert not obj.skip_authorization

    # Test updating existing DB entry
    list_names.return_value = ('c.example', )
    expected_redirect_uris = ['https://c.example/c', 'https://localhost/c']
    expected_origins = ['https://c.example', 'https://localhost']
    openid_connect.redirect_uris = ['https://{domain}/c']
    openid_connect.allowed_origins = expected_origins
    openid_connect.post_logout_redirect_uris = 'a b'
    openid_connect.client_type = Application.CLIENT_PUBLIC
    openid_connect.authorization_grant_type = Application.GRANT_IMPLICIT
    openid_connect.hash_client_secret = True
    openid_connect.name = 'New name'
    openid_connect.algorithm = Application.RS256_ALGORITHM
    openid_connect.skip_authorization = True
    openid_connect.setup(old_version=0)
    obj = Application.objects.get(client_id=openid_connect.client_id)
    assert set(obj.redirect_uris.split(' ')) == set(expected_redirect_uris)
    assert set(obj.allowed_origins.split(' ')) == set(expected_origins)
    assert obj.post_logout_redirect_uris == 'a b'
    assert obj.client_type == Application.CLIENT_PUBLIC
    assert obj.authorization_grant_type == Application.GRANT_IMPLICIT
    assert obj.hash_client_secret
    assert obj.name == 'New name'
    assert obj.algorithm == Application.RS256_ALGORITHM
    assert obj.skip_authorization
