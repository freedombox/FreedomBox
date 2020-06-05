# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for tahoe app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('tahoe.feature')


@then(
    parsers.parse(
        '{domain:S} should be a tahoe {introducer_type:w} introducer'))
def tahoe_assert_introducer(session_browser, domain, introducer_type):
    assert _get_introducer(session_browser, domain, introducer_type)


@then(
    parsers.parse(
        '{domain:S} should not be a tahoe {introducer_type:w} introducer'))
def tahoe_assert_not_introducer(session_browser, domain, introducer_type):
    assert not _get_introducer(session_browser, domain, introducer_type)


@given(parsers.parse('{domain:S} is not a tahoe introducer'))
def tahoe_given_remove_introducer(session_browser, domain):
    if _get_introducer(session_browser, domain, 'connected'):
        _remove_introducer(session_browser, domain)


@when(parsers.parse('I add {domain:S} as a tahoe introducer'))
def tahoe_add_introducer(session_browser, domain):
    _add_introducer(session_browser, domain)


@given(parsers.parse('{domain:S} is a tahoe introducer'))
def tahoe_given_add_introducer(session_browser, domain):
    if not _get_introducer(session_browser, domain, 'connected'):
        _add_introducer(session_browser, domain)


@when(parsers.parse('I remove {domain:S} as a tahoe introducer'))
def tahoe_remove_introducer(session_browser, domain):
    _remove_introducer(session_browser, domain)


def _get_introducer(browser, domain, introducer_type):
    """Return an introducer element with a given type from tahoe-lafs."""
    functional.nav_to_module(browser, 'tahoe')
    css_class = '.{}-introducers .introducer-furl'.format(introducer_type)
    for furl in browser.find_by_css(css_class):
        if domain in furl.text:
            return furl.parent

    return None


def _add_introducer(browser, domain):
    """Add a new introducer into tahoe-lafs."""
    functional.nav_to_module(browser, 'tahoe')

    furl = 'pb://ewe4zdz6kxn7xhuvc7izj2da2gpbgeir@tcp:{}:3456/' \
           'fko4ivfwgqvybppwar3uehkx6spaaou7'.format(domain)
    browser.fill('pet_name', 'testintroducer')
    browser.fill('furl', furl)
    functional.submit(browser, form_class='form-add-introducer')


def _remove_introducer(browser, domain):
    """Remove an introducer from tahoe-lafs."""
    introducer = _get_introducer(browser, domain, 'connected')
    functional.submit(browser, element=introducer.find_by_css('.form-remove'))
