# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for calibre views.
"""

from unittest.mock import call, patch

import pytest
from django import urls
from django.http.response import Http404

from freedombox import module_loader
from freedombox.modules.calibre import views

# For all tests, use freedombox.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('freedombox.urls')


@pytest.fixture(autouse=True, scope='module')
def fixture_calibre_urls():
    """Make sure calibre app's URLs are part of freedombox.urls."""
    with (patch('freedombox.module_loader._modules_to_load', new=[]) as
          modules, patch('freedombox.urls.urlpatterns', new=[])):
        modules.append('freedombox.modules.calibre')
        module_loader.include_urls()
        yield


@pytest.fixture(autouse=True)
def calibre_patch():
    """Patch calibre methods."""
    with patch('freedombox.modules.calibre.privileged.list_libraries'
               ) as list_libraries:
        list_libraries.return_value = ['TestExistingLibrary']

        yield


@patch('freedombox.modules.calibre.privileged.create_library')
def test_create_library(create_library, rf):
    """Test that create library view works."""
    form_data = {'calibre-name': 'TestLibrary'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response = view(request)

    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    request.assert_has_message('Library created.')
    create_library.assert_has_calls([call('TestLibrary')])


@patch('freedombox.modules.calibre.privileged.create_library')
def test_create_library_failed(create_library, rf):
    """Test that create library fails as expected."""
    create_library.side_effect = RuntimeError('TestError')
    form_data = {'calibre-name': 'TestLibrary'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response = view(request)

    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    request.assert_has_message(
        'An error occurred while creating the library. TestError')


def test_create_library_existing_library(rf):
    """Test that create library errors out for an existing library name."""
    form_data = {'calibre-name': 'TestExistingLibrary'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response = view(request)

    assert response.context_data['form'].errors['name'][
        0] == 'A library with this name already exists.'
    assert response.status_code == 200


def test_create_library_invalid_name(rf):
    """Test that create library errors out for invalid name."""
    form_data = {'calibre-name': 'Invalid Library'}
    request = rf.post(urls.reverse('calibre:create-library'), data=form_data)
    view = views.CreateLibraryView.as_view()
    response = view(request)

    assert response.context_data['form'].errors['name'][
        0] == 'Enter a valid value.'
    assert response.status_code == 200


@patch('freedombox.app.App.get')
def test_delete_library_confirmation_view(_app, rf):
    """Test that deleting library confirmation shows correct name."""
    response = views.delete_library(rf.get(''), name='TestExistingLibrary')
    assert response.status_code == 200
    assert response.context_data['name'] == 'TestExistingLibrary'


@patch('freedombox.modules.calibre.privileged.delete_library')
@patch('freedombox.app.App.get')
def test_delete_library(_app, delete_library, rf):
    """Test that deleting a library works."""
    request = rf.post('')
    response = views.delete_library(request, name='TestExistingLibrary')
    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    request.assert_has_message('TestExistingLibrary deleted.')
    delete_library.assert_has_calls([call('TestExistingLibrary')])


@patch('freedombox.modules.calibre.privileged.delete_library')
def test_delete_library_error(delete_library, rf):
    """Test that deleting a library shows error when operation fails."""
    delete_library.side_effect = ValueError('TestError')
    request = rf.post('')
    response = views.delete_library(request, name='TestExistingLibrary')
    assert response.status_code == 302
    assert response.url == urls.reverse('calibre:index')
    request.assert_has_message(
        'Could not delete TestExistingLibrary: TestError')


def test_delete_library_non_existing(rf):
    """Test that deleting a library shows error when operation fails."""
    with pytest.raises(Http404):
        views.delete_library(rf.post(''), name='TestNonExistingLibrary')

    with pytest.raises(Http404):
        views.delete_library(rf.get(''), name='TestNonExistingLibrary')
