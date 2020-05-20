# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ttrss app.
"""

from pytest_bdd import given, scenarios, then, when

from plinth.tests import functional

scenarios('ttrss.feature')


@given('I subscribe to a feed in ttrss')
def ttrss_subscribe(session_browser):
    _subscribe(session_browser)


@when('I unsubscribe from the feed in ttrss')
def ttrss_unsubscribe(session_browser):
    _unsubscribe(session_browser)


@then('I should be subscribed to the feed in ttrss')
def ttrss_assert_subscribed(session_browser):
    assert _is_subscribed(session_browser)


def _ttrss_load_main_interface(browser):
    """Load the TT-RSS interface."""
    functional.access_url(browser, 'ttrss')
    overlay = browser.find_by_id('overlay')
    functional.eventually(lambda: not overlay.visible)


def _is_feed_shown(browser, invert=False):
    return browser.is_text_present('Planet Debian') != invert


def _subscribe(browser):
    """Subscribe to a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    browser.find_by_text('Actions...').click()
    browser.find_by_text('Subscribe to feed...').click()
    browser.find_by_id('feedDlg_feedUrl').fill(
        'https://planet.debian.org/atom.xml')
    browser.find_by_text('Subscribe').click()
    if browser.is_text_present('You are already subscribed to this feed.'):
        browser.find_by_text('Cancel').click()

    expand = browser.find_by_css('span.dijitTreeExpandoClosed')
    if expand:
        expand.first.click()

    assert functional.eventually(_is_feed_shown, [browser])


def _unsubscribe(browser):
    """Unsubscribe from a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    expand = browser.find_by_css('span.dijitTreeExpandoClosed')
    if expand:
        expand.first.click()

    browser.find_by_text('Planet Debian').click()
    browser.execute_script("quickMenuGo('qmcRemoveFeed')")
    prompt = browser.get_alert()
    prompt.accept()

    assert functional.eventually(_is_feed_shown, [browser, True])


def _is_subscribed(browser):
    """Return whether subscribed to a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    return browser.is_text_present('Planet Debian')
