# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for calibre views.
"""

from unittest.mock import call, patch

import pytest
from django import urls
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http.response import Http404

from plinth import module_loader
from plinth.modules.calibre import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')


@pytest.fixture(autouse=True, scope='module')
def fixture_calibre_urls():
    """Make sure calibre app's URLs are part of plinth.urls."""
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=[]):
        modules.append('plinth.modules.calibre')
        module_loader.include_urls()
        yield


@pytest.fixture(autouse=True)
def calibre_patch():
    """Patch calibre methods."""
    with patch('plinth.modules.calibre.privileged.list_libraries'
               ) as list_libraries:
        list_libraries.return_value = ['TestExistingLibrary']

        yield


def make_request(request, view, **kwargs):
    """Make request with a message storage."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    response = view(request, **kwargs)

    return response, messages


@patch('plinth.modules.calibre.privileged.create_library')
def test_create_library(create_library, rf):
    """Test that create library view works."""
    form_data = {'calibre-name': 'TestLibrary'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    assert list(messages)[0].message == 'Library created.'
    create_library.assert_has_calls([call('TestLibrary')])


@patch('plinth.modules.calibre.privileged.create_library')
def test_create_library_failed(create_library, rf):
    """Test that create library fails as expected."""
    create_library.side_effect = RuntimeError('TestError')
    form_data = {'calibre-name': 'TestLibrary'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response, messages = make_request(request, view)

    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    assert list(messages)[0].message == \
        'An error occurred while creating the library. TestError'


def test_create_library_existing_library(rf):
    """Test that create library errors out for an existing library name."""
    form_data = {'calibre-name': 'TestExistingLibrary'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response, _ = make_request(request, view)

    assert response.context_data['form'].errors['name'][
        0] == 'A library with this name already exists.'
    assert response.status_code == 200


def test_create_library_invalid_name(rf):
    """Test that create library errors out for invalid name."""
    form_data = {'calibre-name': 'Invalid Library'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response, _ = make_request(request, view)

    assert response.context_data['form'].errors['name'][
        0] == 'Enter a valid value.'
    assert response.status_code == 200


@patch('plinth.app.App.get')
def test_delete_library_confirmation_view(_app, rf):
    """Test that deleting library confirmation shows correct name."""
    response, _ = make_request(rf.get(''), views.delete_library,
                               name='TestExistingLibrary')
    assert response.status_code == 200
    assert response.context_data['name'] == 'TestExistingLibrary'


@patch('plinth.modules.calibre.privileged.delete_library')
@patch('plinth.app.App.get')
def test_delete_library(_app, delete_library, rf):
    """Test that deleting a library works."""
    response, messages = make_request(rf.post(''), views.delete_library,
                                      name='TestExistingLibrary')
    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    assert list(messages)[0].message == 'TestExistingLibrary deleted.'
    delete_library.assert_has_calls([call('TestExistingLibrary')])


@patch('plinth.modules.calibre.privileged.delete_library')
def test_delete_library_error(delete_library, rf):
    """Test that deleting a library shows error when operation fails."""
    delete_library.side_effect = ValueError('TestError')
    response, messages = make_request(rf.post(''), views.delete_library,
                                      name='TestExistingLibrary')
    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    assert list(messages)[0].message == \
        'Could not delete TestExistingLibrary: TestError'


def test_delete_library_non_existing(rf):
    """Test that deleting a library shows error when operation fails."""
    with pytest.raises(Http404):
        make_request(rf.post(''), views.delete_library,
                     name='TestNonExistingLibrary')

    with pytest.raises(Http404):
        make_request(rf.get(''), views.delete_library,
                     name='TestNonExistingLibrary')
