# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix views.
"""

import pathlib
from unittest.mock import call, patch

import pytest
from django import urls
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http.response import Http404

from plinth import module_loader
from plinth.modules.kiwix import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')

ZIM_ID = 'bc4f8cdf-5626-2b13-3860-0033deddfbea'

_data_dir = pathlib.Path(__file__).parent / 'data'


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
def fiture_kiwix_patch():
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


@patch('tempfile.TemporaryDirectory')
@patch('plinth.modules.kiwix.privileged.add_package')
def test_add_package(add_package, temp_dir_class, rf, tmp_path):
    """Test that adding content view works."""
    temp_dir_class.return_value.__enter__.return_value = str(tmp_path)
    with open(_data_dir / 'FreedomBox.zim', 'rb') as zim_file:
        post_data = {'kiwix-file': zim_file}
        request = rf.post('', data=post_data)
        response, messages = make_request(request,
                                          views.AddPackageView.as_view())
        assert response.status_code == 302
        assert response.url == urls.reverse('kiwix:index')
        assert list(messages)[0].message == 'Content package added.'
        add_package.assert_has_calls([call(f'{tmp_path}/FreedomBox.zim')])


@patch('plinth.modules.kiwix.privileged.add_package')
def test_add_package_failed(add_package, rf):
    """Test that adding content package fails in case of an error."""
    add_package.side_effect = RuntimeError('TestError')
    with open(_data_dir / 'FreedomBox.zim', 'rb') as zim_file:
        post_data = {'kiwix-file': zim_file}
        request = rf.post('', data=post_data)
        response, messages = make_request(request,
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
