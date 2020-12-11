# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for (U)ser (Web) (S)ites.
"""

from plinth.modules.apache import (uws_usr2dir, uws_dir2url, uws_url2usr,
                                   uws_usr2url, uws_url2dir, uws_dir2usr)


def test_uws_namings():
    """Test name solvers for user, url and directory of UWS."""

    assert '/home/usr/public_html' == uws_usr2dir('usr')
    assert '/~usr/' == uws_usr2url('usr')

    f = uws_dir2usr
    assert f('/home/usr/lacks/the/UWS/directory') is None
    assert 'usr' == f('/home/usr/public_html/is/a/normal/UWS/file')
    assert 'usr' == f('/home/usr/public_html/is/a/normal/UWS/path/')
    assert '€.;#@|' == f('/home/€.;#@|/public_html/is/stange/but/valid/')

    f = uws_url2usr
    assert f('/usr/is/not/a/valid/UWS/url/due/to/missing/tilde') is None
    assert 'usr' == f('whatever/~usr/is/considered/a/valid/UWS/path')
    assert 'usr' == f('~usr')
    assert 'usr' == f('~usr/')
    assert 'usr' == f('/~usr/')

    assert '/home/usr/public_html' == uws_url2dir('~usr/any/file')
    assert '/~usr/' == uws_dir2url('/home/usr/public_html/path/to/file')
