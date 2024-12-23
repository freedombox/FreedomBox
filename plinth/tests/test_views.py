# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for common FreedomBox views.
"""

import pytest
from django.urls import resolve

from plinth import menu as menu_module
from plinth.views import get_breadcrumbs, is_safe_url


@pytest.fixture(name='menu')
def fixture_menu():
    """Initialized menu module."""
    menu_module.Menu._all_menus = set()
    menu_module.init()
    menu_module.Menu('home-id', name='Home', url_name='index')
    menu_module.Menu('apps-id', name='Apps', url_name='apps',
                     parent_url_name='index')
    menu_module.Menu('testapp-id', name='Test App', url_name='testapp:index',
                     parent_url_name='apps')


def test_get_breadcrumbs(rf, menu):
    """Test that computing breadcrumbs works."""

    def _crumb(name: str, is_active: bool = False, url_name: str | None = None,
               is_active_section: bool = False):
        crumb = {'name': name, 'is_active': is_active, 'url_name': url_name}
        if is_active_section:
            crumb['is_active_section'] = True

        return crumb

    def _get(path: str):
        request = rf.get(path)
        request.resolver_match = resolve(path)
        return get_breadcrumbs(request)

    def _compare(dict1: dict[str, dict[str, str | bool]],
                 dict2: dict[str, dict[str, str | bool]]):
        """Compare dictionaries with order."""
        assert list(dict1.items()) == list(dict2.items())

    _compare(_get('/'), {'/': _crumb('Home', True, 'index', True)})
    _compare(
        _get('/apps/'), {
            '/apps/': _crumb('Apps', True, 'apps', True),
            '/': _crumb('Home', False, 'index'),
        })
    _compare(
        _get('/apps/testapp/'), {
            '/apps/testapp/': _crumb('Test App', True, 'testapp:index'),
            '/apps/': _crumb('Apps', False, 'apps', True),
            '/': _crumb('Home', False, 'index'),
        })
    _compare(
        _get('/apps/testapp/create/'), {
            '/apps/testapp/create/': _crumb('Here', True, 'testapp:create'),
            '/apps/testapp/': _crumb('Test App', False, 'testapp:index'),
            '/apps/': _crumb('Apps', False, 'apps', True),
            '/': _crumb('Home', False, 'index'),
        })
    _compare(
        _get('/test/1/2/3/'), {
            '/test/1/2/3/': _crumb('Here', True, 'test', True),
            '/': _crumb('Home', False, 'index'),
        })


@pytest.mark.parametrize('url', [
    '/plinth/login/',
    '/',
    'safe',
])
def test_is_safe_url_valid_url(url):
    """Test valid URLs for safe URL checks."""
    assert is_safe_url(url)


@pytest.mark.parametrize(
    'url',
    [
        '',
        None,
        '\\plinth',
        '///plinth',
        'https://example.com/plinth/login/',
        'https:///example.com',
        'https:///plinth/login',
        'ftp://example.com',
        'https://[aabb::ccdd',  # Invalid IPv6
    ])
def test_is_safe_url_invalid_url(url):
    """Test invalid URLs for safe URL checks."""
    assert not is_safe_url(url)
