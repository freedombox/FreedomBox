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
Tests for samba views.
"""

import json
import urllib
from unittest.mock import patch

import pytest
from django import urls
from django.contrib.messages.storage.fallback import FallbackStorage
from plinth import module_loader
from plinth.errors import ActionError
from plinth.modules.samba import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')

USERS = {"access_ok": ["testuser"], 'password_re_enter_needed': []}

DISKS = [{
    'device': '/dev/sda1',
    'label': '',
    'filesystem_type': 'ext4',
    'mount_point': '/',
    'file_system_type': 'ext4',
    'percent_used': 63,
    'size_str': '9.5 GiB',
    'used_str': '5.7 GiB'
}]

SHARES = [
    {
        "name": "disk",
        "mount_point": "/",
        "path": "/var/lib/freedombox/shares/open_share",
        "share_type": "open"
    },
    {
        "name": "disk_home",
        "mount_point": "/",
        "path": "/var/lib/freedombox/shares/homes/%u",
        "share_type": "home"
    },
    {
        "name": "otherdisk",
        "mount_point": "/media/root/otherdisk",
        "path": "/media/root/otherdisk/FreedomBox/shares/homes/open_share",
        "share_type": "open"
    }
]


@pytest.fixture(autouse=True, scope='module')
def fixture_samba_urls():
    """Make sure samba app's URLs are part of plinth.urls."""
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=[]):
        modules.append('plinth.modules.samba')
        module_loader.include_urls()
        yield


def action_run(action, options, **kwargs):
    """Action return values."""
    if action == 'samba' and options == ['get-shares']:
        return json.dumps(SHARES)

    return None


@pytest.fixture(autouse=True)
def samba_patch_actions():
    """Patch actions scripts runner."""
    with patch('plinth.actions.superuser_run', side_effect=action_run):
        yield


def make_request(request, view, **kwargs):
    """Make request with a message storage."""
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    response = view(request, **kwargs)

    return response, messages


def test_samba_shares_view(rf):
    """Test that a share list has correct view data."""
    with patch('plinth.views.AppView.get_context_data',
               return_value={'is_enabled': True}), patch(
                   'plinth.modules.samba.get_users',
                   return_value=USERS), patch(
                       'plinth.modules.storage.get_disks', return_value=DISKS):
        view = views.SambaAppView.as_view()
        response, _ = make_request(rf.get(''), view)

        assert response.context_data['disks'] == DISKS
        assert response.context_data['shared_mounts'] == {
            '/': ['open', 'home'],
            '/media/root/otherdisk': ['open']
        }
        assert response.context_data['unavailable_shares'] == [{
            'mount_point':
                '/media/root/otherdisk',
            'name':
                'otherdisk',
            'path':
                '/media/root/otherdisk/FreedomBox/shares/homes/open_share',
            'share_type':
                'open'
        }]
        assert response.context_data['users'] == USERS
        assert response.status_code == 200


def test_enable_samba_share_view(rf):
    """Test that enabling share sends correct success message."""
    form_data = {'filesystem_type': 'ext4', 'open_share': 'enable'}
    mount_point = urllib.parse.quote('/')
    response, messages = make_request(
        rf.post('', data=form_data), views.share, mount_point=mount_point)

    assert list(messages)[0].message == 'Share enabled.'
    assert response.status_code == 302
    assert response.url == urls.reverse('samba:index')


def test_enable_samba_share_failed_view(rf):
    """Test that share enabling failure sends correct error message."""
    form_data = {'filesystem_type': 'ext4', 'open_share': 'enable'}
    mount_point = urllib.parse.quote('/')
    error_message = 'Sharing failed'
    with patch('plinth.modules.samba.add_share',
               side_effect=ActionError(error_message)):
        response, messages = make_request(
            rf.post('', data=form_data), views.share, mount_point=mount_point)

        assert list(messages)[0].message == 'Error enabling share: {0}'.format(
            error_message)
        assert response.status_code == 302
        assert response.url == urls.reverse('samba:index')


def test_disable_samba_share(rf):
    """Test that enabling share sends correct success message."""
    form_data = {'filesystem_type': 'ext4', 'open_share': 'disable'}
    mount_point = urllib.parse.quote('/')
    response, messages = make_request(
        rf.post('', data=form_data), views.share, mount_point=mount_point)

    assert list(messages)[0].message == 'Share disabled.'
    assert response.status_code == 302
    assert response.url == urls.reverse('samba:index')


def test_disable_samba_share_failed_view(rf):
    """Test that share disabling failure sends correct error message."""
    form_data = {'filesystem_type': 'ext4', 'open_share': 'disable'}
    mount_point = urllib.parse.quote('/')
    error_message = 'Unsharing failed'
    with patch('plinth.modules.samba.delete_share',
               side_effect=ActionError(error_message)):
        response, messages = make_request(
            rf.post('', data=form_data), views.share, mount_point=mount_point)

        assert list(messages)[
            0].message == 'Error disabling share: {0}'.format(error_message)
        assert response.status_code == 302
        assert response.url == urls.reverse('samba:index')
