# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom Django template tags.
"""

from plinth.templatetags import plinth_extras


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
        menu = plinth_extras.mark_active_menuitem(menu, check_path)
        _assert_active_url(menu, expected_active_path)
        assert _verify_active_menuitems(menu)
