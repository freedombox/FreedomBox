# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for WordPress.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.wordpress]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'wordpress')
    yield
    functional.app_disable(session_browser, 'wordpress')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'wordpress')

    functional.app_enable(session_browser, 'wordpress')
    assert functional.service_is_running(session_browser, 'wordpress')
    assert functional.is_available(session_browser, 'wordpress')

    functional.app_disable(session_browser, 'wordpress')
    assert functional.service_is_not_running(session_browser, 'wordpress')
    assert not functional.is_available(session_browser, 'wordpress')


def test_post(session_browser):
    """Test writing a blog post."""
    functional.app_enable(session_browser, 'wordpress')
    _write_post(session_browser, 'FunctionalTest')
    assert _get_post(session_browser, 'FunctionalTest')
    _delete_post(session_browser, 'FunctionalTest')
    assert not _get_post(session_browser, 'FunctionalTest')


def test_public_mode(session_browser):
    """Test that site is available without login in public mode."""
    functional.app_enable(session_browser, 'wordpress')
    _enable_public_mode(session_browser, True)

    def no_login_prompt():
        _load_site(session_browser)
        return not functional.is_login_prompt(session_browser)

    try:
        functional.logout(session_browser)
        functional.eventually(no_login_prompt)
    finally:
        functional.login(session_browser)


def test_private_mode(session_browser):
    """Test that site is not available without login in public mode."""
    functional.app_enable(session_browser, 'wordpress')
    _enable_public_mode(session_browser, False)

    def login_prompt():
        _load_site(session_browser)
        return functional.is_login_prompt(session_browser)

    try:
        functional.logout(session_browser)
        functional.eventually(login_prompt)
    finally:
        functional.login(session_browser)


@pytest.mark.backups
def test_backup(session_browser):
    """Test backing up and restoring."""
    functional.app_enable(session_browser, 'wordpress')
    _write_post(session_browser, 'FunctionalTest')
    functional.backup_create(session_browser, 'wordpress', 'test_wordpress')
    _delete_post(session_browser, 'FunctionalTest')
    functional.uninstall(session_browser, 'wordpress')
    functional.backup_restore(session_browser, 'wordpress', 'test_wordpress')
    assert _get_post(session_browser, 'FunctionalTest')


def _load_site(browser):
    """Visit WordPress site and wait until becomes available."""
    functional.visit(browser, '/wordpress/wp-admin/')

    def loaded():
        browser.reload()
        title_node = browser.find_by_css('title')
        return (not title_node or '404' not in title_node[0].text)

    functional.eventually(loaded)


def _visit_site(browser):
    """Visit WordPress and run the first setup wizard if needed."""
    _load_site(browser)
    if '/install.php' in browser.url:
        # continue past language selection screen
        if browser.find_by_id('language-continue'):
            browser.find_by_id('language-continue').click()

        browser.fill('weblog_title', 'Test Blog')
        browser.fill('user_name', functional.config['DEFAULT']['username'])
        # browser.fill() once does not work for some reason for password field
        browser.fill('admin_password',
                     functional.config['DEFAULT']['password'])
        browser.fill('admin_password',
                     functional.config['DEFAULT']['password'])
        browser.check('pw_weak')
        browser.fill('admin_email', 'admin@example.org')
        submit_button = browser.find_by_id('submit')
        functional.submit(browser, element=submit_button)

        if not browser.find_by_css('.install-success'):
            raise Exception('WordPress installation failed')

        functional.visit(browser, '/wordpress/wp-admin/')

    if not browser.find_by_id('wpadminbar'):
        functional.visit(browser, '/wordpress/wp-login.php')
        browser.fill('log', functional.config['DEFAULT']['username'])
        browser.fill('pwd', functional.config['DEFAULT']['password'])
        login_button = browser.find_by_id('wp-submit')
        functional.submit(browser, element=login_button)


def _write_post(browser, title):
    """Create a blog post in WordPress site."""
    post = _get_post(browser, title)
    if post:
        _delete_post(browser, title)

    functional.visit(browser, '/wordpress/wp-admin/post-new.php')
    if browser.find_by_css('.edit-post-welcome-guide'):
        browser.find_by_css('.components-modal__header button')[0].click()

    if browser.find_by_id('post-title-0'):
        browser.find_by_id('post-title-0').fill(title)
    else:
        if browser.find_by_css('.editor-visual-editor.is-iframed'):
            with browser.get_iframe('editor-canvas') as iframe:
                iframe.find_by_css('.editor-post-title').first.type(title)
        else:
            browser.find_by_css('.editor-post-title').first.type(title)

    browser.find_by_css('.editor-post-publish-button__button')[0].click()
    functional.eventually(browser.find_by_css, ['.editor-post-publish-button'])
    browser.find_by_css('.editor-post-publish-button')[0].click()


def _delete_post(browser, title):
    """Delete a blog post in WordPress site."""
    post = _get_post(browser, title)
    if not post:
        raise Exception('Post not found')

    delete_element = post.find_by_css('.submitdelete')[0]
    browser.visit(delete_element['href'])


def _get_post(browser, title):
    """Return whether a blog post with a given title is available."""
    _visit_site(browser)
    functional.visit(browser, '/wordpress/wp-admin/edit.php')
    xpath = '//tr[contains(@class, "type-post")][.//a[contains(@class, ' \
        f'"row-title") and contains(text(), "{title}")]]'
    post = browser.find_by_xpath(xpath)
    return post[0] if post else None


def _enable_public_mode(browser, should_enable):
    """Enable/disable the public mode."""
    checkbox = browser.find_by_id('id_is_public')
    if should_enable:
        checkbox.check()
    else:
        checkbox.uncheck()

    functional.submit(browser, form_class='form-configuration')
