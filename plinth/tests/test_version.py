# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for Version class.
"""

from plinth.version import Version


def test_version_comparisons():
    """Test comparing Debian package version numbers."""
    assert Version('3.1.8-1') == Version('3.1.8-1')
    assert Version('3.1.8-1') <= Version('4~')
    assert Version('3.1.8-1') < Version('4~')
    assert Version('4.0.0-1') >= Version('4~')
    assert Version('4.0') >= Version('4~')
    assert Version('4.0.0-1') > Version('4~')
    assert Version('4.0') > Version('4~')


def test_backport_versions():
    """Test comparing Debian backports package version numbers."""
    assert Version('3.1.7-1~bpo11+1') == Version('3.1.7-1~bpo11+1')
    assert Version('3.1.7-1~bpo11+1') <= Version('4~')
    assert Version('3.1.7-1~bpo11+1') < Version('4~')
    assert Version('4.0.0-1~bpo11+1') >= Version('4~')
    assert Version('4.0.0-1~bpo11+1') > Version('4~')


def test_dfsg_versions():
    """Test comparing Debian DFSG package version numbers."""
    assert Version('1.3.0+dfsg-2.2') == Version('1.3.0+dfsg-2.2')
    assert Version('1.3.0+dfsg-2.2') <= Version('1.4~')
    assert Version('1.3.0+dfsg-2.2') < Version('1.4~')
    assert Version('1.4.0+dfsg-1.1') >= Version('1.4~')
    assert Version('1.4.0+dfsg-1.1') > Version('1.4~')


def test_git_versions():
    """Test comparing Debian git package version numbers."""
    assert Version('21~git20210204.b4cbc79+dfsg-1') == \
        Version('21~git20210204.b4cbc79+dfsg-1')
    assert Version('21~git20210204.b4cbc79+dfsg-1') <= Version('22~')
    assert Version('21~git20210204.b4cbc79+dfsg-1') < Version('22~')
    assert Version('22~git20210204.b4cbc79+dfsg-1') >= Version('22~')
    assert Version('22~git20210204.b4cbc79+dfsg-1') > Version('22~')
