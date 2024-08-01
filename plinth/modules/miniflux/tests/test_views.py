# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for Miniflux views."""

from unittest.mock import patch

import pytest
from django import urls
from django.contrib.messages.storage.fallback import FallbackStorage

from plinth import module_loader
from plinth.modules.miniflux import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')


@pytest.fixture(autouse=True, scope='module')
def fixture_miniflux_urls():
    """Make sure Miniflux app's URLs are part of plinth.urls."""
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=[]):
        modules.append('plinth.modules.miniflux')
        module_loader.include_urls()
        yield


def make_request(request, view, **kwargs):
    """Make request with a message storage."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    response = view(request, **kwargs)

    return response, messages


##########################
# Create Admin User view #
##########################


def test_create_admin_user_view(rf):
    """Test that the create admin user view loads successfully."""
    request = rf.get(urls.reverse('miniflux:create-admin-user'))
    view = views.CreateAdminUserView.as_view()
    response, _ = make_request(request, view)

    assert response.status_code == 200


@patch('plinth.modules.miniflux.privileged.create_admin_user')
def test_create_admin_user_form_valid(create_admin_user, rf):
    """Test that the create admin user form is valid and redirects."""
    form_data = {
        'miniflux-username': 'admin',
        'miniflux-password': 'strongpassword',
        'miniflux-password_confirmation': 'strongpassword'
    }
    request = rf.post(urls.reverse('miniflux:create-admin-user'),
                      data=form_data)
    view = views.CreateAdminUserView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 302
    assert list(messages)[0].message == 'Created admin user: admin'


def test_passwords_do_not_match(rf):
    """Test that the form shows an error when passwords do not match."""
    form_data = {
        'miniflux-username': 'admin',
        'miniflux-password': 'strongpassword',
        'miniflux-password_confirmation': 'weakpassword'
    }
    request = rf.post(urls.reverse('miniflux:create-admin-user'),
                      data=form_data)
    view = views.CreateAdminUserView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 200
    assert response.context_data['form'].errors['password_confirmation'][
        0] == 'Passwords do not match.'


def test_password_too_short(rf):
    """Test that the form shows an error when the password is too short."""
    form_data = {
        'miniflux-username': 'demo',
        'miniflux-password': 'demo',
        'miniflux-password_confirmation': 'demo'
    }
    request = rf.post(urls.reverse('miniflux:create-admin-user'),
                      data=form_data)
    view = views.CreateAdminUserView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 200
    assert response.context_data['form'].errors['password'][
        0] == 'Ensure this value has at least 6 characters (it has 4).'


@patch('plinth.modules.miniflux.privileged.create_admin_user')
def test_recreate_existing_user(create_admin_user, rf):
    """Test that trying to recreate an existing user fails."""
    create_admin_user.side_effect = Exception(
        'Skipping admin user creation because it already exists')

    form_data = {
        'miniflux-username': 'admin',
        'miniflux-password': 'strongpassword',
        'miniflux-password_confirmation': 'strongpassword'
    }
    request = rf.post(urls.reverse('miniflux:create-admin-user'),
                      data=form_data)
    view = views.CreateAdminUserView.as_view()
    response, messages = make_request(request, view)

    error_msg = ('An error occurred while creating the user: Skipping admin '
                 'user creation because it already exists.')
    assert response.status_code == 302
    assert list(messages)[0].message == error_msg


############################
# Reset User Password view #
############################


@patch('plinth.modules.miniflux.privileged.reset_user_password')
def test_reset_user_password_form_valid(reset_user_password, rf):
    """Test that the reset user password form is valid and redirects."""
    reset_user_password.return_value = 'Password changed!'

    form_data = {
        'miniflux-username': 'admin',
        'miniflux-password': 'strongpassword',
        'miniflux-password_confirmation': 'strongpassword'
    }
    request = rf.post(urls.reverse('miniflux:reset-user-password'),
                      data=form_data)
    view = views.ResetUserPasswordView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 302
    assert list(messages)[0].message == 'Password reset for user: admin'


@patch('plinth.modules.miniflux.privileged.reset_user_password')
def test_reset_user_password_for_invalid_user(reset_user_password, rf):
    """Test that the resetting user password for an invalid user fails."""
    reset_user_password.side_effect = Exception('user not found')

    form_data = {
        'miniflux-username': 'admin',
        'miniflux-password': 'strongpassword',
        'miniflux-password_confirmation': 'strongpassword'
    }
    request = rf.post(urls.reverse('miniflux:reset-user-password'),
                      data=form_data)
    view = views.ResetUserPasswordView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 302
    assert list(
        messages
    )[0].message == 'An error occurred during password reset: user not found.'
