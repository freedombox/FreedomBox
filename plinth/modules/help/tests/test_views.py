# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for help views.

Design: - Make tests independent from URL policy by using Django names instead
          of URLs to call the help module. For this, some additional fixture
          work is needed: pytestmark and fixture_app_urls().

Pending: - status log

"""

import json
import pathlib
import subprocess
from unittest.mock import patch

import pytest
from django import urls
from django.conf import settings
from django.http import Http404
from django.urls import re_path

from plinth import cfg
from plinth import menu as menu_module
from plinth import module_loader
from plinth.modules import help as help_module
from plinth.modules.help import views

# For all tests, use plinth.urls instead of urls configured for testing
pytestmark = pytest.mark.urls('plinth.urls')


def _is_page(response):
    """Minimal check on help views."""
    return (response.status_code == 200 and 'title' in response.context_data
            and response['content-type'] == 'text/html; charset=utf-8')


@pytest.fixture(autouse=True, scope='module')
def fixture_app_urls():
    """Make sure app's URLs are part of plinth.urls."""
    urls = [
        re_path(r'^apps/$', views.index, name='apps'),
        re_path(r'^system/$', views.index, name='system')
    ]
    with patch('plinth.module_loader._modules_to_load', new=[]) as modules, \
            patch('plinth.urls.urlpatterns', new=urls):
        modules.append('plinth.modules.help')
        module_loader.include_urls()
        yield


@pytest.fixture(autouse=True, scope='module')
def fixture_developer_configuration():
    """Make sure docs are read from current directory instead of /usr."""
    cfg.read_file(cfg.get_develop_config_path())


@pytest.fixture(name='menu', autouse=True)
def fixture_menu():
    """Initialized menu module."""
    menu_module.init()
    help_module.HelpApp()  # Create all menu components


@pytest.mark.parametrize("view_name, view", (
    ('feedback', views.feedback),
    ('support', views.support),
    ('index', views.index),
))
def test_simple_help_pages(rf, view_name, view):
    """Simple common test for certain help views."""
    response = view(rf.get(urls.reverse('help:' + view_name)))
    assert _is_page(response)


@patch('apt.Cache')
@patch('gzip.decompress')
@patch('requests.get')
def test_contribute_page(requests_get, decompress, apt_cache, rf):
    """Test the contribute page."""
    issues = [{
        'type': 'testing-autorm',
        'packages': ['autormpkg'],
        'source': 'autormsrc',
        'bugs': ['123']
    }, {
        'type': 'no-testing',
        'package': ['notestingpkg'],
        'source': 'nottestingsrc',
    }, {
        'type': 'gift',
        'package': ['giftpkg'],
        'bug': '456',
        'title': 'bug 456 title',
    }, {
        'type': 'help',
        'package': ['helppkg'],
        'bug': '567',
        'title': 'bug 567 title',
    }]
    decompress.return_value = json.dumps(issues)
    response = views.contribute(rf.get(urls.reverse('help:contribute')))
    assert _is_page(response)
    assert issues == (response.context_data['testing_autorm'] +
                      response.context_data['no_testing'] +
                      response.context_data['gift'] +
                      response.context_data['help'])


@patch('plinth.modules.upgrades.views.is_newer_version_available')
@patch('plinth.modules.upgrades.views.get_os_release')
def test_about(_get_os_release, _is_newer_version_available, rf):
    """Test some expected items in about view."""
    about_url = urls.reverse('help:about')
    response = views.about(rf.get(about_url))
    assert _is_page(response)
    for item in ('version', 'new_version', 'os_release'):
        assert item in response.context_data


# ---------------------------------------------------------------------------
# Tests for serving the offline user guide ( the "manual")
#
# The manual can be requested:
# - Either complete on a single page or page by page.
# - Specifying (or not) the language.
# - The complete manual can be requested in HTML or PDF formats.
#
# Expected Behaviour Rules:
# - If the page isn't specified, the help module returns the full manual in
#   one single page.
# - The help module tries first to return the page in the specified
#   language. If not found (either that page doesn't exist or the language
#   wasn't secified) it falls back to its twin in the fallback language. If
#   it is neither available, it shows a proper error message.
#
# Design Decisions:
# - The PDF manual has a separate function to serve it.
# - The 'Manual' page doesn't exist as such. However there are files named
#   'Manual' containing the complete full manual in one single page.
# - In order to avoid loops, the fallback language is intercepted and
#   treated specifically.
#   - Problem: Requesting a missing page in a language that happens to be
#              the fallback one, missing it would cause the help module to
#              redirect to the same page, closing thereby a neverending loop.
#              The web served would probably break that loop, but it would
#              cause confusion to the user.
# - CI environments don't setup FreedomBox completely. A regular setup run is
#   impractically slow (10-15 mins), if even posible. Compiling and deploying
#   the manual is just 3 extra lines in .gitlab-ci.yml file:
#    - make -C doc
#    - mkdir -p /usr/share/freedombox/manual
#    - cp -r doc/manual /usr/share/freedombox/manual
#   But again, this causes the 4 minutes of test preparation to bump to 6.
#   It's not worth for just testing the offline manual, so the tests guess if
#   they are running in a restricted environment and skip.

canary = pathlib.Path('doc/manual/en/Coturn.part.html')
TRANSLATIONS = ('es', )
MANUAL_PAGES = ('Apache_userdir', 'APU', 'Backups', 'BananaPro', 'BeagleBone',
                'bepasty', 'Bind', 'Calibre', 'Cockpit', 'Configure',
                'Contribute', 'Coturn', 'Cubieboard2', 'Cubietruck',
                'DateTime', 'Debian', 'Deluge', 'Developer', 'Diagnostics',
                'Download', 'DynamicDNS', 'ejabberd', 'Firewall',
                'freedombox-manual', 'GettingHelp', 'GitWeb', 'Hardware',
                'I2P', 'Ikiwiki', 'Infinoted', 'Introduction', 'JSXC',
                'LetsEncrypt', 'Maker', 'MatrixSynapse', 'MediaWiki',
                'Minetest', 'MiniDLNA', 'Mumble', 'NameServices', 'Networks',
                'OpenVPN', 'OrangePiZero', 'PageKite', 'pcDuino3',
                'Performance', 'PineA64+', 'PioneerEdition', 'Plinth', 'Power',
                'Privoxy', 'Quassel', 'QuickStart', 'Radicale', 'RaspberryPi2',
                'RaspberryPi3B+', 'RaspberryPi3B', 'RaspberryPi4B',
                'ReleaseNotes', 'Rock64', 'RockPro64', 'Roundcube', 'Samba',
                'Searx', 'SecureShell', 'Security', 'ServiceDiscovery',
                'Shadowsocks', 'Sharing', 'Snapshots', 'Storage', 'Syncthing',
                'TinyTinyRSS', 'Tor', 'Transmission', 'Upgrades', 'USBWiFi',
                'Users', 'VirtualBox', 'WireGuard')
_restricted_reason = ('Needs installed manual. '
                      'CI speed-optimized workspace does not provide it.')
not_restricted_environment = pytest.mark.skipif(not canary.exists(),
                                                reason=_restricted_reason)


@pytest.mark.parametrize('lang', (None, '-'))
def test_full_default_manual(rf, lang):
    """Test request for the full default manual.

    Expected: Redirect to the full manual in the fallback language.

    """
    manual_url = urls.reverse('help:manual')
    response = views.manual(rf.get(manual_url), lang=lang)
    assert response.status_code == 302
    assert response.url == '/help/manual/en/'

    # With a language cookie set
    request = rf.get(manual_url)
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = TRANSLATIONS[0]
    response = views.manual(request, lang=lang)
    assert response.status_code == 302
    assert response.url == f'/help/manual/{TRANSLATIONS[0]}/'


@pytest.mark.parametrize('lang', (None, '-'))
def test_default_manual_by_pages(rf, lang):
    """Test page-specific requests for the (default) manual.

    Expected: Redirect to their respective twins in the fallback language.
    Pending.: Redirect pages with plus-sign '+' in their name.

    """
    manual_url = urls.reverse('help:manual')
    for page in MANUAL_PAGES:
        if '+' in page or 'Manual' in page:  # Pine64+ & RaspberryPi3B+
            continue

        response = views.manual(rf.get(manual_url), lang=lang, page=page)
        assert response.status_code == 302
        assert response.url == '/help/manual/en/' + page

        # With a language cookie set
        request = rf.get(manual_url)
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = TRANSLATIONS[0]
        response = views.manual(request, lang=lang, page=page)
        assert response.status_code == 302
        assert response.url == f'/help/manual/{TRANSLATIONS[0]}/{page}'


@not_restricted_environment
def test_specific_full_manual_translation(rf):
    """Test request for specific translated manuals.

    Expected: All return a page.

    """
    manual_url = urls.reverse('help:manual')
    for lang in ('es', 'en'):
        response = views.manual(rf.get(manual_url), lang=lang)
        assert _is_page(response)


@not_restricted_environment
def test_specific_manual_translation_by_pages(rf):
    """Test that translated-page-specific requests.

    Expected: All known page names return pages.

    """
    manual_url = urls.reverse('help:manual')
    for lang in ('es', 'en'):
        for page in MANUAL_PAGES:
            response = views.manual(rf.get(manual_url), page=page, lang=lang)
            assert _is_page(response)


@not_restricted_environment
def test_full_manual_requested_by_page_name(rf):
    """Test requests for 'Manual'.

    Note: 'Manual' is a file, not a manual page.
    Expected: Return a proper not found message (HTTP 404)
    Currently: Non fallback languages return a page.
               This is wrong, but doesn't cause any harm.

    """
    manual_url = urls.reverse('help:manual')
    page = 'Manual'

    for lang in TRANSLATIONS:
        response = views.manual(rf.get(manual_url), page=page, lang=lang)
        assert _is_page(response)

    with pytest.raises(Http404):
        views.manual(rf.get(manual_url), page=page, lang='en')


def test_missing_page(rf):
    """Test requests for missing pages.

    Expected:
    - Unspecified language: Fall back to its fallback twin.
    - Translated languages: Fall back to its fallback twin.
    - Fallback language...: Return a proper not found message (HTTP 404)
    - Unknown languages...: Fall back to its fallback twin.

    """
    manual_url = urls.reverse('help:manual')
    page = 'unknown'
    for lang in TRANSLATIONS + ('unknown', None):
        response = views.manual(rf.get(manual_url), page=page, lang=lang)
        assert response.status_code == 302
        assert response.url == '/help/manual/en/unknown'

    with pytest.raises(Http404):
        views.manual(rf.get(manual_url), page=page, lang='en')


@not_restricted_environment
def test_download_full_manual_file(rf, tmp_path):
    """Test download of manual.

    Design: - Downloads the default manual, a translated one and the
              fallback translation. None should fail. Then compares
              them.
            - Call diff command for fast comparision. Comparing the
              over 10MB bytestrings in python is insanely slow.

    """

    def _diff(file_name_a, file_name_b, same):
        file_a = tmp_path / file_name_a
        file_b = tmp_path / file_name_b
        process = subprocess.run(
            ['diff', '-q', str(file_a), str(file_b)], check=False)
        assert bool(process.returncode) != same

    url = urls.reverse('help:manual')
    manuals = {
        'unspecified': rf.get(url),
        'translated': rf.get(url, HTTP_ACCEPT_LANGUAGE='es'),
        'fallback': rf.get(url, HTTP_ACCEPT_LANGUAGE='en')
    }
    for name, request in manuals.items():
        response = views.download_manual(request)
        assert response.status_code == 200
        file = tmp_path / (name + '.pdf')
        file.write_bytes(response.content)

    _diff('fallback.pdf', 'unspecified.pdf', same=True)
    _diff('fallback.pdf', 'translated.pdf', same=False)
