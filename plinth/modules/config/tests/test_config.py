# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for config module.
"""

import os
import pathlib
from unittest.mock import Mock, patch

import pytest

from plinth import __main__ as plinth_main
from plinth import utils
from plinth.modules.apache import uws_directory_of_user, uws_url_of_user
from plinth.modules.config import (_home_page_scid2url, change_home_page,
                                   get_home_page, home_page_url2scid)


def test_homepage_mapping():
    """Basic tests for homepage functions."""
    func = home_page_url2scid
    assert func(None) == 'apache-default'
    assert func('/unknown/url') is None
    assert func('/plinth/') == 'plinth'
    assert func('/plinth') == 'plinth'
    assert func('plinth') == 'plinth'
    assert func('/index.html') == 'apache-default'
    assert func('/~user') == 'uws-user'
    assert func('/~user/whatever/else') == 'uws-user'

    func = _home_page_scid2url
    assert func('plinth') == '/plinth/'
    assert func('apache-default') is None


def test_homepage_mapping_skip_ci():
    """Special tests for homepage functions."""
    try:
        user = os.getlogin()
    except OSError:
        # See msg383161 in https://bugs.python.org/issue40821
        reason = "Needs access to ~/ directory. " \
               + "CI sandboxed workspace doesn't provide it."
        pytest.skip(reason)
    uws_directory = uws_directory_of_user(user)
    uws_url = uws_url_of_user(user)
    uws_scid = home_page_url2scid(uws_url)

    # Check test's precondition:
    if os.path.exists(uws_directory):
        # Don't blindly remove a pre-existing directory. Just skip the test.
        reason = "UWS directory {} exists already.".format(uws_directory)
        pytest.skip(reason)

    # AC: Return scid if UWS directory exists:
    try:
        os.mkdir(uws_directory)
    except Exception:
        reason = "Needs access to ~/ directory. " \
               + "CI sandboxed workspace doesn't provide it."
        pytest.skip(reason)
    assert _home_page_scid2url(uws_scid) == uws_url

    # AC: Return None if it doesn't:
    os.rmdir(uws_directory)
    assert _home_page_scid2url(uws_scid) == '/plinth/'


@patch(
    'plinth.frontpage.Shortcut.list',
    Mock(return_value=[
        Mock(url='url/for/' + id, component_id=id) for id in ('a', 'b')
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

    Note: We take fbx as website user because of our testing container.

    Pending: - Specific test cases to distinguish 4.1,2,3.
               Currently they share the same test case.
             - Search for another valid user apart from fbx.
    """
    user = 'test_' + utils.random_string(size=12)
    uws_directory = uws_directory_of_user(user)
    uws_url = uws_url_of_user(user)
    uws_scid = home_page_url2scid(uws_url)

    default_home_page = 'plinth'
    original_home_page = get_home_page() or default_home_page
    change_home_page(default_home_page)  # Set to known value explicitly

    # AC: invalid changes fall back to default:
    for scid in ('uws-unexisting', uws_scid, 'missing_app'):
        change_home_page(scid)
        assert get_home_page() == default_home_page

    # AC: valid changes actually happen:
    pathlib.Path(uws_directory).mkdir(parents=True)
    for scid in ('b', 'a', uws_scid, 'apache-default', 'plinth'):
        change_home_page(scid)
        assert get_home_page() == scid

    # cleanup:
    change_home_page(original_home_page)
    os.rmdir(uws_directory)
    assert get_home_page() == original_home_page


def test_locale_path():
    """
    Test that the 'locale' directory is in the same folder as __main__.py.
    This is required for detecting translated languages.
    """
    plinth_dir = os.path.dirname(plinth_main.__file__)
    locale_dir = os.path.join(plinth_dir, 'locale')
    assert os.path.isdir(locale_dir)
