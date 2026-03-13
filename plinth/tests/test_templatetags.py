# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom Django template tags.
"""

from unittest.mock import patch

from plinth.templatetags import extras


def _assert_active_url(menu, url):
    """Verify that only the given url is set as 'active' in the menu"""
    for item in menu:
        if item['url'] == url:
            assert item['active']
        else:
            assert not item['active']


def _verify_active_menuitems(menu):
    """Verify that one and only one menuitem is marked as active"""
    return sum([item['active'] for item in menu]) == 1


def test_highlighting():
    """Test detection of active subsubmenu items using request.path"""
    menu = [{
        'url': '/abc/123/abc/',
        'text': 'abc'
    }, {
        'url': '/abc/123/',
        'text': 'overview'
    }, {
        'url': '/abc/123/crunch/',
        'text': 'crunch'
    }, {
        'url': '/abc/123/create/',
        'text': 'create'
    }]

    tests = [['/abc/123/crunch/new/', '/abc/123/crunch/'],
             ['/abc/123/create/', '/abc/123/create/'],
             ['/abc/123/nolink/', '/abc/123/'], ['/abc/123/abx/', '/abc/123/'],
             ['/abc/123/ab/', '/abc/123/'], ['/abc/123/', '/abc/123/']]

    for check_path, expected_active_path in tests:
        menu = extras.mark_active_menuitem(menu, check_path)
        _assert_active_url(menu, expected_active_path)
        assert _verify_active_menuitems(menu)


@patch('plinth.web_server.resolve_static_path')
def test_icon(resolve_static_path, tmp_path):
    """Test that the icon tag works for basic usage."""
    icon1 = tmp_path / 'icon1.svg'
    icon1.write_text('<svg><cirlcle></circle></svg>')
    resolve_static_path.return_value = icon1
    return_value = extras.icon('icon1')
    assert return_value == ('<svg class="svg-icon" data-icon-name="icon1" '
                            '><cirlcle></circle></svg>')


@patch('plinth.web_server.resolve_static_path')
def test_icon_attributes(resolve_static_path, tmp_path):
    """Test that the icon tag works with attributes."""
    icon1 = tmp_path / 'icon1.svg'
    icon1.write_text('<svg><cirlcle></circle></svg>')
    resolve_static_path.return_value = icon1

    attributes = {'class': 'test-class'}
    return_value = extras.icon('icon1', **attributes)
    assert return_value == ('<svg class="test-class" data-icon-name="icon1" '
                            '><cirlcle></circle></svg>')

    attributes = {'data-test': 'test-value'}
    return_value = extras.icon('icon1', **attributes)
    assert return_value == ('<svg data-test="test-value" class="svg-icon" '
                            'data-icon-name="icon1" ><cirlcle></circle></svg>')


@patch('plinth.utils.random_string')
@patch('plinth.web_server.resolve_static_path')
def test_icon_auto_ids(resolve_static_path, random_string, tmp_path):
    """Test that the icon tag works for implementing automatic IDs."""
    random_string.return_value = 'randomvalue'
    icon2 = tmp_path / 'icon2.svg'
    icon2.write_text('<svg><cirlcle id="autoidmagic-foo"></circle>'
                     '<path id="autoidmagic-bar"></path></svg>')
    resolve_static_path.return_value = icon2
    return_value = extras.icon('icon2')
    assert return_value == ('<svg class="svg-icon" data-icon-name="icon2" >'
                            '<cirlcle id="randomvalue-foo"></circle>'
                            '<path id="randomvalue-bar"></path></svg>')


@patch('plinth.web_server.resolve_static_path')
def test_icon_xml_stripping(resolve_static_path, tmp_path):
    """Test that the icon tag strips the XML header."""
    icon2 = tmp_path / 'icon2.svg'
    icon2.write_text('<?xml version="1.0" encoding="utf-8">\n'
                     '<svg><cirlcle></circle></svg>')
    resolve_static_path.return_value = icon2
    return_value = extras.icon('icon2')
    assert return_value == ('<svg class="svg-icon" data-icon-name="icon2" >'
                            '<cirlcle></circle></svg>')
