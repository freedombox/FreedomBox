# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for config module.
"""

import pytest
import os

from unittest.mock import (patch, MagicMock)

from plinth import __main__ as plinth_main
from plinth.modules.apache import uws_directory_of_user
from plinth.modules.config import (home_page_url2scid, get_home_page,
                                   _home_page_scid2url, change_home_page)
from plinth.modules.config.forms import ConfigurationForm


def test_hostname_field():
    """Test that hostname field accepts only valid hostnames."""
    valid_hostnames = [
        'a', '0a', 'a0', 'AAA', '00', '0-0', 'example-hostname', 'example',
        '012345678901234567890123456789012345678901234567890123456789012'
    ]
    invalid_hostnames = [
        '', '-', '-a', 'a-', '.a', 'a.', 'a.a', '?', 'a?a',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ]

    for hostname in valid_hostnames:
        form = ConfigurationForm({
            'hostname': hostname,
            'domainname': 'example.com'
        })
        assert form.is_valid()

    for hostname in invalid_hostnames:
        form = ConfigurationForm({
            'hostname': hostname,
            'domainname': 'example.com'
        })
        assert not form.is_valid()


def test_domainname_field():
    """Test that domainname field accepts only valid domainnames."""
    valid_domainnames = [
        '', 'a', '0a', 'a0', 'AAA', '00', '0-0', 'example-hostname', 'example',
        'example.org', 'a.b.c.d', 'a-0.b-0.c-0',
        '012345678901234567890123456789012345678901234567890123456789012',
        ((('x' * 63) + '.') * 3) + 'x' * 61
    ]
    invalid_domainnames = [
        '-', '-a', 'a-', '.a', 'a.', '?', 'a?a', 'a..a', 'a.-a', '.',
        ((('x' * 63) + '.') * 3) + 'x' * 62, 'x' * 64
    ]

    for domainname in valid_domainnames:
        form = ConfigurationForm({
            'hostname': 'example',
            'domainname': domainname
        })
        assert form.is_valid()

    for domainname in invalid_domainnames:
        form = ConfigurationForm({
            'hostname': 'example',
            'domainname': domainname
        })
        assert not form.is_valid()


def test_homepage_mapping():
    """Basic tests for homepage functions."""
    f = home_page_url2scid
    assert f(None) is None
    assert f('/unknown/url') is None
    assert 'plinth' == f('/plinth/')
    assert 'plinth' == f('/plinth')
    assert 'plinth' == f('plinth')
    assert 'apache-default' == f('/index.html')
    assert 'uws-user' == f('/~user')
    assert 'uws-user' == f('/~user/whatever/else')
    # assert 'config' == f('/plinth/apps/sharing/')

    f = _home_page_scid2url
    assert f(None) is None
    assert '/plinth/' == f('plinth')
    assert '/index.html' == f('apache-default')


def test_homepage_mapping_skip_ci():
    """Special tests for homepage functions."""

    try:
        UWS_DIRECTORY = uws_directory_of_user(os.getlogin())
    except OSError:
        reason = "Needs access to ~/ directory. " \
               + "CI sandboxed workspace doesn't provide it."
        pytest.skip(reason)

    if os.path.exists(UWS_DIRECTORY):
        reason = "UWS dir {} exists already.".format(UWS_DIRECTORY)
        pytest.skip(reason)

    f = _home_page_scid2url
    try:
        os.mkdir(UWS_DIRECTORY)
    except FileNotFoundError:
        pytest.skip('Home folder cannot be accessed on buildd.')

    assert '/~fbx/' == f('uws-fbx')
    os.rmdir(UWS_DIRECTORY)
    assert f('uws-fbx') is None


class Dict2Obj(object):
    """Mock object made out of any dict."""

    def __init__(self, a_dict):
        self.__dict__ = a_dict


@patch('plinth.frontpage.Shortcut.list',
       MagicMock(return_value=[
           Dict2Obj({
               'url': 'url/for/' + id,
               'component_id': id
           }) for id in ('a', 'b')
       ]))
@pytest.mark.usefixtures('needs_root')
def test_homepage_field():
    """Test homepage changes.

    Test Cases:
        1) FreedomBox Homepage (default),
        2) Apache default,
        3) A user's website of an...
        3.1) unexisting user
        3.2) existing user without a page
        3.3) existing user page.
        4) A FreedomBox App.
        4.1) unknown app
        4.2) uninstalled app
        4.3) disabled app
        4.4) enabled app

    Note: If run on a pristine unconfigured FreedomBox, this test will leave
          the homepage default-configured. (Imperfect cleanup in such case).

    Pending: Specific test cases to distiguish 4.1,2,3.
             Currently they share the same test case.
    """
    try:
        UWS_DIRECTORY = uws_directory_of_user(os.getlogin())
    except OSError:
        reason = "Needs access to ~/ directory, etc. " \
               + "CI sandboxed workspace doesn't provide it."
        pytest.skip(reason)

    DEFAULT_HOME_PAGE = 'plinth'
    ORIGINAL_HOME_PAGE = get_home_page() or DEFAULT_HOME_PAGE

    if ORIGINAL_HOME_PAGE not in (DEFAULT_HOME_PAGE, None):
        reason = "Unexpected home page {}.".format(ORIGINAL_HOME_PAGE)
        pytest.skip(reason)

    # invalid changes fall back to default:
    for scid in ('uws-unexisting', 'uws-fbx', 'missing_app'):
        change_home_page(scid)
        assert get_home_page() == DEFAULT_HOME_PAGE

    os.mkdir(UWS_DIRECTORY)

    # valid changes actually happen:
    for scid in ('b', 'a', 'uws-fbx', 'apache-default', 'plinth'):
        change_home_page(scid)
        assert get_home_page() == scid

    # cleanup:
    change_home_page(ORIGINAL_HOME_PAGE)
    os.rmdir(UWS_DIRECTORY)
    assert get_home_page() == ORIGINAL_HOME_PAGE


def test_locale_path():
    """
    Test that the 'locale' directory is in the same folder as __main__.py.
    This is required for detecting translated languages.
    """
    plinth_dir = os.path.dirname(plinth_main.__file__)
    locale_dir = os.path.join(plinth_dir, 'locale')
    assert os.path.isdir(locale_dir)
