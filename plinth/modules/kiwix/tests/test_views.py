# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix views.
"""

from plinth import module_loader
from django import urls
from unittest.mock import call, patch
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http.response import Http404
from django.test.client import encode_multipart, RequestFactory

import pytest

from plinth.modules.kiwix import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')

ZIM_ID = 'bc4f8cdf-5626-2b13-3860-0033deddfbea'


@pytest.fixture(autouse=True, scope='module')
def fixture_kiwix_urls():
    """Make sure kiwix app's URLs are part of plinth.urls."""
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=[]):
        modules.append('plinth.modules.kiwix')
        module_loader.include_urls()
        yield


def make_request(request, view, **kwargs):
    """Make request with a message storage."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    response = view(request, **kwargs)

    return response, messages


@pytest.fixture(autouse=True)
def kiwix_patch():
    """Patch kiwix methods."""
    with patch('plinth.modules.kiwix.privileged.list_content_packages'
               ) as list_libraries:
        list_libraries.return_value = {
            ZIM_ID: {
                'title': 'TestExistingContentPackage',
                'description': 'A sample content package',
                'path': 'test_existing_content_package'
            }
        }
        yield


@pytest.fixture()
def storage_info_patch():
    """Patch storage info method."""
    with patch('plinth.modules.storage.get_mount_info') as get_mount_info:
        get_mount_info.return_value = {'free_bytes': 1000000000000}
        yield


@patch('plinth.modules.kiwix.privileged.add_content')
def test_add_content_package(add_content, rf):
    """Test that adding content view works."""
    with open('plinth/modules/kiwix/tests/data/FreedomBox.zim',
              'rb') as zim_file:
        post_data = {
            'kiwix-file': zim_file,
        }
        post_data = encode_multipart('BoUnDaRyStRiNg', post_data)
        request = rf.post(
            '', data=post_data, content_type='multipart/form-data; '
            'boundary=BoUnDaRyStRiNg')
        response, messages = make_request(request,
                                          views.AddContentView.as_view())
        assert response.status_code == 302
        assert response.url == urls.reverse('kiwix:index')
        assert list(messages)[0].message == 'Content package added.'
        add_content.assert_has_calls([call('/tmp/FreedomBox.zim')])


@patch('plinth.modules.kiwix.privileged.add_content')
def test_add_content_package_failed(add_content, rf):
    """Test that adding content package fails in case of an error."""
    add_content.side_effect = RuntimeError('TestError')
    with open('plinth/modules/kiwix/tests/data/FreedomBox.zim',
              'rb') as zim_file:
        post_data = {
            'kiwix-file': zim_file,
        }
        post_data = encode_multipart('BoUnDaRyStRiNg', post_data)
        request = rf.post(
            '', data=post_data, content_type='multipart/form-data; '
            'boundary=BoUnDaRyStRiNg')
        response, messages = make_request(request,
                                          views.AddContentView.as_view())
        assert response.status_code == 302
        assert response.url == urls.reverse('kiwix:index')
        assert list(messages)[0].message == \
            'Failed to add content package.'


@patch('plinth.app.App.get')
def test_delete_package_confirmation_view(_app, rf):
    """Test that deleting package confirmation shows correct title."""
    response, _ = make_request(rf.get(''), views.delete_content, zim_id=ZIM_ID)
    assert response.status_code == 200
    assert response.context_data['name'] == 'TestExistingContentPackage'


@patch('plinth.modules.kiwix.privileged.delete_content_package')
@patch('plinth.app.App.get')
def test_delete_content_package(_app, delete_content_package, rf):
    """Test that deleting a content package works."""
    response, messages = make_request(rf.post(''), views.delete_content,
                                      zim_id=ZIM_ID)
    assert response.status_code == 302
    assert response.url == urls.reverse('kiwix:index')
    assert list(messages)[0].message == 'TestExistingContentPackage deleted.'
    delete_content_package.assert_has_calls([call(ZIM_ID)])


@patch('plinth.modules.kiwix.privileged.delete_content_package')
def test_delete_content_package_error(delete_content_package, rf):
    """Test that deleting a content package shows an error when operation fails."""
    delete_content_package.side_effect = ValueError('TestError')
    response, messages = make_request(rf.post(''), views.delete_content,
                                      zim_id=ZIM_ID)
    assert response.status_code == 302
    assert response.url == urls.reverse('kiwix:index')
    assert list(messages)[0].message == \
        'Could not delete TestExistingContentPackage: TestError'


def test_delete_content_package_non_existing(rf):
    """Test that deleting a content package shows error when operation fails."""
    with pytest.raises(Http404):
        make_request(rf.post(''), views.delete_content,
                     zim_id='NonExistentZimId')

    with pytest.raises(Http404):
        make_request(rf.get(''), views.delete_content,
                     zim_id='NonExistentZimId')
