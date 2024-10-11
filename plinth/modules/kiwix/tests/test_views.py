# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix views.
"""

from unittest.mock import call, patch, MagicMock

import pytest
from django import urls
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http.response import Http404

from plinth import module_loader
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
def fixture_kiwix_patch():
    """Patch kiwix methods."""
    with patch(
            'plinth.modules.kiwix.privileged.list_packages') as list_libraries:
        list_libraries.return_value = {
            ZIM_ID: {
                'title': 'TestExistingPackage',
                'description': 'A sample content package',
                'path': 'test_existing_package'
            }
        }
        yield


@pytest.fixture()
def file_path(tmp_path):
    return str(tmp_path / 'FreedomBox.zim')


def uploaded_file():
    return SimpleUploadedFile('FreedomBox.zim', content=b'FreedomBox rocks!',
                              content_type='application/octet-stream')


@pytest.fixture()
def add_package_request(rf, file_path):
    """Patch add_package."""
    post_data = {'kiwix-file': uploaded_file()}
    request = rf.post('', data=post_data)
    request.FILES['kiwix-file'].temporary_file_path = MagicMock(
        return_value=file_path)
    return request


@patch('plinth.modules.kiwix.privileged.add_package')
def test_add_package(add_package, file_path, add_package_request):
    """Test that adding content view works."""
    response, messages = make_request(add_package_request,
                                      views.AddPackageView.as_view())
    assert response.status_code == 302
    assert response.url == urls.reverse('kiwix:index')
    assert list(messages)[0].message == 'Content package added.'
    add_package.assert_has_calls([call('FreedomBox.zim', file_path)])


@patch('plinth.modules.kiwix.privileged.add_package')
def test_add_package_failed(add_package, add_package_request):
    """Test that adding content package fails in case of an error."""
    add_package.side_effect = RuntimeError('TestError')
    response, messages = make_request(add_package_request,
                                      views.AddPackageView.as_view())
    assert response.status_code == 302
    assert response.url == urls.reverse('kiwix:index')
    assert list(messages)[0].message == 'Failed to add content package.'


@patch('plinth.app.App.get')
def test_delete_package_confirmation_view(_app, rf):
    """Test that deleting content confirmation shows correct title."""
    response, _ = make_request(rf.get(''), views.delete_package, zim_id=ZIM_ID)
    assert response.status_code == 200
    assert response.context_data['name'] == 'TestExistingPackage'


@patch('plinth.modules.kiwix.privileged.delete_package')
@patch('plinth.app.App.get')
def test_delete_package(_app, delete_package, rf):
    """Test that deleting a content package works."""
    response, messages = make_request(rf.post(''), views.delete_package,
                                      zim_id=ZIM_ID)
    assert response.status_code == 302
    assert response.url == urls.reverse('kiwix:index')
    assert list(messages)[0].message == 'TestExistingPackage deleted.'
    delete_package.assert_has_calls([call(ZIM_ID)])


@patch('plinth.modules.kiwix.privileged.delete_package')
def test_delete_package_error(delete_package, rf):
    """Test that deleting content shows an error when operation fails."""
    delete_package.side_effect = ValueError('TestError')
    response, messages = make_request(rf.post(''), views.delete_package,
                                      zim_id=ZIM_ID)
    assert response.status_code == 302
    assert response.url == urls.reverse('kiwix:index')
    assert list(messages)[0].message == \
        'Could not delete TestExistingPackage: TestError'


def test_delete_package_non_existing(rf):
    """Test that deleting content shows error when operation fails."""
    with pytest.raises(Http404):
        make_request(rf.post(''), views.delete_package,
                     zim_id='NonExistentZimId')

    with pytest.raises(Http404):
        make_request(rf.get(''), views.delete_package,
                     zim_id='NonExistentZimId')
