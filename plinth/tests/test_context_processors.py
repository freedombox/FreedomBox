# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom context processors.
"""

from unittest.mock import MagicMock, Mock, patch

from django.urls import resolve

from plinth import context_processors as cp


@patch('plinth.notification.Notification')
def test_common(Notification, load_cfg, rf, test_menu):
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
