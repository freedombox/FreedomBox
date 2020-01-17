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
Tests for gitweb views.
"""

import json
from unittest.mock import patch

import pytest
from django import urls
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http.response import Http404

from plinth import module_loader
from plinth.errors import ActionError
from plinth.modules.gitweb import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')

EXISTING_REPOS = [
    {
        'name': 'something',
        'description': '',
        'owner': '',
        'access': 'public',
        'is_private': False
    },
    {
        'name': 'something2',
        'description': '',
        'owner': '',
        'access': 'private',
        'is_private': True
    },
]


@pytest.fixture(autouse=True, scope='module')
def fixture_gitweb_urls():
    """Make sure gitweb app's URLs are part of plinth.urls."""
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=[]):
        modules.append('plinth.modules.gitweb')
        module_loader.include_urls()
        yield


def action_run(*args, **kwargs):
    """Action return values."""
    if args[1][0] == 'repo-info':
        return json.dumps(EXISTING_REPOS[0])

    if args[1][0] == 'check-repo-exists':
        return True

    return None


@pytest.fixture(autouse=True)
def gitweb_patch():
    """Patch gitweb."""
    with patch('plinth.modules.gitweb.app') as app_patch, \
            patch('plinth.actions.superuser_run', side_effect=action_run), \
            patch('plinth.actions.run', side_effect=action_run):
        app_patch.get_repo_list.return_value = [{
            'name': EXISTING_REPOS[0]['name']
        }, {
            'name': EXISTING_REPOS[1]['name']
        }]
        yield


def make_request(request, view, **kwargs):
    """Make request with a message storage."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    response = view(request, **kwargs)

    return response, messages


def test_repos_view(rf):
    """Test that a repo list has correct view data."""
    with patch('plinth.views.AppView.get_context_data',
               return_value={'is_enabled': True}):
        view = views.GitwebAppView.as_view()
        response, _ = make_request(rf.get(''), view)

        assert response.context_data['repos'] == [{
            'name': EXISTING_REPOS[0]['name']
        }, {
            'name': EXISTING_REPOS[1]['name']
        }]
        assert response.status_code == 200


def test_create_repo_view(rf):
    """Test that repo create view sends correct success message."""
    form_data = {
        'gitweb-name': 'something_other',
        'gitweb-description': 'test description',
        'gitweb-owner': 'test owner',
        'gitweb-is_private': True
    }
    request = rf.post(urls.reverse('gitweb:create'), data=form_data)
    view = views.CreateRepoView.as_view()
    response, messages = make_request(request, view)

    assert list(messages)[0].message == 'Repository created.'
    assert response.status_code == 302


def test_create_repo_duplicate_name_view(rf):
    """Test that repo create view shows correct error message."""
    form_data = {
        'gitweb-name': EXISTING_REPOS[0]['name'],
        'gitweb-description': '',
        'gitweb-owner': ''
    }
    request = rf.post(urls.reverse('gitweb:create'), data=form_data)
    view = views.CreateRepoView.as_view()
    response, _ = make_request(request, view)

    assert response.context_data['form'].errors['name'][
        0] == 'A repository with this name already exists.'
    assert response.status_code == 200


def test_create_repo_invalid_name_view(rf):
    """Test that repo create view shows correct error message."""
    form_data = {
        'gitweb-name': '.something_other',
        'gitweb-description': '',
        'gitweb-owner': ''
    }
    request = rf.post(urls.reverse('gitweb:create'), data=form_data)
    view = views.CreateRepoView.as_view()
    response, _ = make_request(request, view)

    assert response.context_data['form'].errors['name'][
        0] == 'Invalid repository name.'
    assert response.status_code == 200


def test_create_repo_failed_view(rf):
    """Test that repo creation failure sends correct error message."""
    with patch('plinth.modules.gitweb.create_repo',
               side_effect=ActionError('Error')):
        form_data = {
            'gitweb-name': 'something_other',
            'gitweb-description': '',
            'gitweb-owner': ''
        }
        request = rf.post(urls.reverse('gitweb:create'), data=form_data)
        view = views.CreateRepoView.as_view()
        response, messages = make_request(request, view)

        assert list(messages)[
            0].message == 'An error occurred while creating the repository.'
        assert response.status_code == 302


def test_clone_repo_view(rf):
    """Test that cloning repo sends correct succcess message."""
    form_data = {
        'gitweb-name': 'https://example.com/test.git',
        'gitweb-description': '',
        'gitweb-owner': ''
    }
    request = rf.post(urls.reverse('gitweb:create'), data=form_data)
    view = views.CreateRepoView.as_view()
    response, messages = make_request(request, view)

    with pytest.raises(AttributeError):
        getattr(response.context_data['form'], 'errors')

    assert list(messages)[0].message == 'Repository created.'
    assert response.status_code == 302


def test_clone_repo_missing_remote_view(rf):
    """Test that cloning non-existing repo shows correct error message."""
    with patch('plinth.modules.gitweb.repo_exists', return_value=False):
        form_data = {
            'gitweb-name': 'https://example.com/test.git',
            'gitweb-description': '',
            'gitweb-owner': ''
        }
        request = rf.post(urls.reverse('gitweb:create'), data=form_data)
        view = views.CreateRepoView.as_view()
        response, _ = make_request(request, view)

        assert response.context_data['form'].errors['name'][
            0] == 'Remote repository is not available.'
        assert response.status_code == 200


def test_edit_repository_view(rf):
    """Test that editing repo sends correct success message."""
    form_data = {
        'gitweb-name': 'something_other.git',
        'gitweb-description': 'test-description',
        'gitweb-owner': 'test-owner',
        'gitweb-is_private': True
    }
    url = urls.reverse('gitweb:edit',
                       kwargs={'name': EXISTING_REPOS[0]['name']})
    request = rf.post(url, data=form_data)
    view = views.EditRepoView.as_view()
    response, messages = make_request(request, view,
                                      name=EXISTING_REPOS[0]['name'])

    assert list(messages)[0].message == 'Repository edited.'
    assert response.status_code == 302


def test_edit_nonexisting_repository_view(rf):
    """Test that trying to edit non-existing repository raises 404."""
    non_existing_repo = {'name': 'something_other'}
    request = rf.post(urls.reverse('gitweb:edit', kwargs=non_existing_repo),
                      data={})
    view = views.EditRepoView.as_view()

    with pytest.raises(Http404):
        make_request(request, view, **non_existing_repo)


def test_edit_repository_duplicate_name_view(rf):
    """Test that renaming to already existing repo name shows correct error
    message.

    """
    form_data = {
        'gitweb-name': EXISTING_REPOS[1]['name'],
        'gitweb-description': 'test-description',
        'gitweb-owner': 'test-owner'
    }
    url = urls.reverse('gitweb:edit',
                       kwargs={'name': EXISTING_REPOS[0]['name']})
    request = rf.post(url, data=form_data)
    view = views.EditRepoView.as_view()
    response, _ = make_request(request, view, **EXISTING_REPOS[0])

    assert response.context_data['form'].errors['name'][
        0] == 'A repository with this name already exists.'
    assert response.status_code == 200


def test_edit_repository_invalid_name_view(rf):
    """Test that renaming repo to invalid name shows correct error message."""
    form_data = {
        'gitweb-name': '.something',
        'gitweb-description': 'test-description',
        'gitweb-owner': 'test-owner'
    }
    url = urls.reverse('gitweb:edit',
                       kwargs={'name': EXISTING_REPOS[0]['name']})
    request = rf.post(url, data=form_data)
    view = views.EditRepoView.as_view()
    response, _ = make_request(request, view, **EXISTING_REPOS[0])

    assert response.context_data['form'].errors['name'][
        0] == 'Invalid repository name.'
    assert response.status_code == 200


def test_edit_repository_no_change_view(rf):
    """Test that not changing any values don't edit the repo."""
    with patch('plinth.modules.gitweb.edit_repo') as edit_repo:
        form_data = {
            'gitweb-name': EXISTING_REPOS[0]['name'],
            'gitweb-description': EXISTING_REPOS[0]['description'],
            'gitweb-owner': EXISTING_REPOS[0]['owner']
        }
        request = rf.post(
            urls.reverse('gitweb:edit',
                         kwargs={'name': EXISTING_REPOS[0]['name']}),
            data=form_data)
        view = views.EditRepoView.as_view()
        response, _ = make_request(request, view, **EXISTING_REPOS[0])

        assert not edit_repo.called, 'method should not have been called'
        assert response.status_code == 302


def test_edit_repository_failed_view(rf):
    """Test that failed repo editing sends correct error message."""
    with patch('plinth.modules.gitweb.edit_repo',
               side_effect=ActionError('Error')):
        form_data = {
            'gitweb-name': 'something_other',
            'gitweb-description': 'test-description',
            'gitweb-owner': 'test-owner'
        }
        request = rf.post(
            urls.reverse('gitweb:edit',
                         kwargs={'name': EXISTING_REPOS[0]['name']}),
            data=form_data)
        view = views.EditRepoView.as_view()
        response, messages = make_request(request, view, **EXISTING_REPOS[0])

        assert list(
            messages)[0].message == 'An error occurred during configuration.'
        assert response.status_code == 302


def test_delete_repository_confirmation_view(rf):
    """Test that repo deletion confirmation shows correct repo name."""
    response, _ = make_request(rf.get(''), views.delete,
                               name=EXISTING_REPOS[0]['name'])

    assert response.context_data['name'] == EXISTING_REPOS[0]['name']
    assert response.status_code == 200


def test_delete_repository_view(rf):
    """Test that repo deletion sends correct success message."""
    response, messages = make_request(rf.post(''), views.delete,
                                      name=EXISTING_REPOS[0]['name'])

    assert list(messages)[0].message == '{} deleted.'.format(
        EXISTING_REPOS[0]['name'])
    assert response.status_code == 302


def test_delete_repository_fail_view(rf):
    """Test that failed repository deletion sends correct error message."""

    with patch('plinth.modules.gitweb.delete_repo',
               side_effect=ActionError('Error')):
        response, messages = make_request(rf.post(''), views.delete,
                                          name=EXISTING_REPOS[0]['name'])

        assert list(
            messages)[0].message == 'Could not delete {}: Error'.format(
                EXISTING_REPOS[0]['name'])
        assert response.status_code == 302


def test_delete_non_existing_repository_view(rf):
    """Test that deleting non-existing repository raises 404."""
    with pytest.raises(Http404):
        make_request(rf.post(''), views.delete, name='unknown_repo')
