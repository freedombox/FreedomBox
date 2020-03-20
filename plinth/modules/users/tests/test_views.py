# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for users views.
"""

from unittest.mock import Mock, patch

import pytest
from django import urls
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from plinth import module_loader
from plinth.modules.users import views

from ..components import UsersAndGroups

# For all tests, plinth.urls instead of urls configured for testing, and
# django database
pytestmark = [pytest.mark.urls('plinth.urls'), pytest.mark.django_db]


@pytest.fixture(autouse=True, scope='module')
def fixture_users_urls():
    """Make sure users app's URLs are part of plinth.urls."""
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=[]):
        modules.append('plinth.modules.users')
        module_loader.include_urls()
        yield


def action_run(action, options, **kwargs):
    """Action return values."""
    if action == 'users' and options == ['get-group-users', 'admin']:
        return 'admin'
    if action == 'ssh' and options[:2] == ['get-keys', '--username']:
        return ''
    if action == 'users' and options == ['get-user-groups', 'tester']:
        return ''

    return None


@pytest.fixture(autouse=True)
def module_patch():
    """Patch users module."""
    pwd_users = [Mock(pw_name='root'), Mock(pw_name='plinth')]

    UsersAndGroups._all_components = set()
    UsersAndGroups('test-users-and-groups',
                   groups={'admin': 'The admin group'})
    UsersAndGroups('users-and-groups-minetest',
                   reserved_usernames=['debian-minetest'])

    with patch('pwd.getpwall', return_value=pwd_users),\
            patch('plinth.actions.superuser_run', side_effect=action_run):
        yield


def make_request(request, view, as_admin=True, **kwargs):
    """Make request with a message storage and users created."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    user = User.objects.create(username='tester')
    admin_user = User.objects.create(username='admin')

    request.user = admin_user if as_admin else user

    with patch('plinth.modules.users.forms.is_user_admin',
               return_value=as_admin),\
            patch('plinth.modules.users.views.is_user_admin',
                  return_value=as_admin),\
            patch('plinth.modules.users.views.update_session_auth_hash'):

        response = view(request, **kwargs)

    return response, messages


def test_users_list_view(rf):
    """Test that users list view has correct view data."""
    with patch('plinth.views.AppView.get_context_data',
               return_value={'is_enabled': True}):
        view = views.UserList.as_view()
        response, messages = make_request(rf.get('/'), view)

        assert response.context_data['last_admin_user'] == 'admin'
        assert response.status_code == 200


@pytest.mark.parametrize('username', ['test-new', 'test-neW@2_'])
def test_create_user_view(rf, username):
    """Test that user creation with valid usernames succeeds."""
    password = 'testingtesting'
    form_data = {
        'username': username,
        'password1': password,
        'password2': password
    }

    request = rf.post(urls.reverse('users:create'), data=form_data)
    view = views.UserCreate.as_view()
    response, messages = make_request(request, view)

    assert list(messages)[0].message == 'User {} created.'.format(username)
    assert response.status_code == 302
    assert response.url == urls.reverse('users:index')


def test_create_user_form_view(rf):
    """Test that a username field on create form has correct attributes."""
    request = rf.get(urls.reverse('users:create'))
    view = views.UserCreate.as_view()
    response, messages = make_request(request, view)

    assert response.context_data['form'].fields['username'].widget.attrs == {
        'maxlength': '150',
        'autofocus': 'autofocus',
        'autocapitalize': 'none',
        'autocomplete': 'username'
    }
    assert response.status_code == 200


@pytest.mark.parametrize('username',
                         ['-tester', 'testér', 'test+test', 't', 'test test'])
def test_create_user_invalid_username_view(rf, username):
    """Test that user creation with invalid username fails."""
    form_data = {
        'username': username,
        'password1': 'testingtesting',
        'password2': 'testingtesting'
    }

    request = rf.post(urls.reverse('users:create'), data=form_data)
    view = views.UserCreate.as_view()
    response, messages = make_request(request, view)

    assert response.context_data['form'].errors['username'][
        0] == 'Enter a valid username.'
    assert response.status_code == 200


@pytest.mark.parametrize(
    'username,error',
    [('testuser', 'A user with that username already exists.'),
     ('root', 'Username is taken or is reserved.'),
     ('rooT', 'Username is taken or is reserved.'),
     ('debian-minetest', 'Username is taken or is reserved.')])
def test_create_user_taken_or_reserved_username_view(rf, username, error):
    """Test that user creation with taken or reserved username fails."""
    User.objects.create(username='testuser')
    form_data = {
        'username': username,
        'password1': 'testingtesting',
        'password2': 'testingtesting'
    }

    request = rf.post(urls.reverse('users:create'), data=form_data)
    view = views.UserCreate.as_view()
    response, messages = make_request(request, view)

    assert response.context_data['form'].errors['username'][0] == error
    assert response.status_code == 200


def test_update_user_view(rf):
    """Test that updating username succeeds."""
    user = 'tester'
    new_username = 'tester-renamed'
    form_data = {
        'username': new_username,
        'password1': 'testingtesting',
        'password2': 'testingtesting'
    }

    url = urls.reverse('users:edit', kwargs={'slug': user})
    request = rf.post(url, data=form_data)
    view = views.UserUpdate.as_view()
    response, messages = make_request(request, view, as_admin=True, slug=user)

    assert list(messages)[0].message == 'User {} updated.'.format(new_username)
    assert response.status_code == 302
    assert response.url == urls.reverse('users:edit',
                                        kwargs={'slug': new_username})


def test_update_user_without_permissions_view(rf):
    """Test that updating other user as non-admin user raises exception."""
    form_data = {
        'username': 'admin-renamed',
        'password1': 'testingtesting',
        'password2': 'testingtesting'
    }

    url = urls.reverse('users:edit', kwargs={'slug': 'admin'})
    request = rf.post(url, data=form_data)
    view = views.UserUpdate.as_view()

    with pytest.raises(PermissionDenied):
        make_request(request, view, as_admin=False, slug='admin')


def test_delete_user_view(rf):
    """Test that user deletion succeeds."""
    user = 'tester'

    url = urls.reverse('users:delete', kwargs={'slug': user})
    request = rf.post(url)
    view = views.UserDelete.as_view()
    response, messages = make_request(request, view, as_admin=True, slug=user)

    assert list(messages)[0].message == 'User {} deleted.'.format(user)
    assert response.status_code == 302
    assert response.url == urls.reverse('users:index')


def test_user_change_password_view(rf):
    """Test that changing password succeeds."""
    user = 'admin'
    form_data = {
        'new_password1': 'testingtesting2',
        'new_password2': 'testingtesting2'
    }

    url = urls.reverse('users:change_password', kwargs={'slug': user})
    request = rf.post(url, data=form_data)
    view = views.UserChangePassword.as_view()
    response, messages = make_request(request, view, as_admin=True, slug=user)

    assert list(messages)[0].message == 'Password changed successfully.'
    assert response.status_code == 302
    assert response.url == urls.reverse('users:edit', kwargs={'slug': user})


def test_user_change_password_without_permissions_view(rf):
    """
    Test that changing other user password as a non-admin user raises
    exception.
    """
    user = 'admin'
    form_data = {
        'new_password1': 'adminadmin2',
        'new_password2': 'adminadmin2'
    }

    url = urls.reverse('users:change_password', kwargs={'slug': user})
    request = rf.post(url, data=form_data)
    view = views.UserChangePassword.as_view()

    with pytest.raises(PermissionDenied):
        make_request(request, view, as_admin=False, slug=user)
