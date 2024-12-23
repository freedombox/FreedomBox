# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom context processors.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from django.urls import resolve

from plinth import context_processors as cp
from plinth import menu as menu_module


@pytest.fixture(name='menu', autouse=True)
def fixture_menu():
    """Initialized menu module."""
    menu_module.Menu._all_menus = set()
    menu_module.init()
    menu_module.Menu('home-id', name='Home', url_name='index')
    menu_module.Menu('apps-id', name='Apps', url_name='apps',
                     parent_url_name='index')
    menu_module.Menu('testapp-id', name='Test App', url_name='testapp:index',
                     parent_url_name='apps')


@patch('plinth.notification.Notification')
def test_common(Notification, load_cfg, rf):
    """Verify that the common() function returns the correct values."""
    url = '/apps/testapp/create/'
    request = rf.get(url)
    request.resolver_match = resolve(url)
    request.user = Mock()
    request.user.groups.filter().exists = Mock(return_value=True)
    request.session = MagicMock()
    response = cp.common(request)
    assert response is not None

    config = response['cfg']
    assert config is not None
    assert config.box_name == 'FreedomBox'
    assert response['box_name'] == 'FreedomBox'
    assert len(response['breadcrumbs']) == 4
    assert response['active_section_url'] == '/apps/'
    assert response['user_is_admin']
