# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for (U)ser (Web) (S)ites.
"""

from plinth.modules.apache import (uws_directory_of_user, uws_url_of_user,
                                   uws_directory_of_url, uws_url_of_directory,
                                   user_of_uws_directory, user_of_uws_url)


def test_uws_namings():
    """Test name solvers for user, url and directory of UWS."""

    assert '/home/usr/public_html' == uws_directory_of_user('usr')
    assert '/~usr/' == uws_url_of_user('usr')

    f = user_of_uws_directory
    assert f('/home/usr/lacks/the/UWS/directory') is None
    assert 'usr' == f('/home/usr/public_html/is/a/normal/UWS/file')
    assert 'usr' == f('/home/usr/public_html/is/a/normal/UWS/path/')
    assert '€.;#@|' == f('/home/€.;#@|/public_html/is/stange/but/valid/')

    f = user_of_uws_url
    assert f('/usr/is/not/a/valid/UWS/url/due/to/missing/tilde') is None
    assert 'usr' == f('whatever/~usr/is/considered/a/valid/UWS/path')
    assert 'usr' == f('~usr')
    assert 'usr' == f('~usr/')
    assert 'usr' == f('/~usr/')

    assert '/home/usr/public_html' == uws_directory_of_url('~usr/any/file')
    assert '/~usr/' == uws_url_of_directory('/home/usr/public_html/any/file')
