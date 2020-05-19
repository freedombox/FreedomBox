# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from contextlib import contextmanager

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait

from . import interface

# unlisted services just use the service_name as module name
service_module = {
    'ntp': 'datetime',
}


def get_service_module(service_name):
    module = service_name
    if service_name in service_module:
        module = service_module[service_name]
    return module


def is_running(browser, service_name):
    interface.nav_to_module(browser, get_service_module(service_name))
    return len(browser.find_by_id('service-not-running')) == 0


def is_not_running(browser, service_name):
    interface.nav_to_module(browser, get_service_module(service_name))
    return len(browser.find_by_id('service-not-running')) != 0


def eventually(function, args=[], timeout=30):
    """Execute a function returning a boolean expression till it returns
    True or a timeout is reached"""
    end_time = time.time() + timeout
    current_time = time.time()
    while current_time < end_time:
        if function(*args):
            return True

        time.sleep(0.1)
        current_time = time.time()

    return False


@contextmanager
def wait_for_page_update(browser, timeout=300, expected_url=None):
    page_body = browser.find_by_tag('body').first
    yield
    WebDriverWait(browser, timeout).until(page_loaded(page_body, expected_url))


class page_loaded():
    """
    Wait until a page (re)loaded.

    - element: Wait until this element gets stale
    - expected_url (optional): Wait for the URL to become <expected_url>.
      This can be necessary to wait for a redirect to finish.
    """

    def __init__(self, element, expected_url=None):
        self.element = element
        self.expected_url = expected_url

    def __call__(self, driver):
        is_stale = False
        try:
            self.element.has_class('whatever_class')
        except StaleElementReferenceException:
            if self.expected_url is None:
                is_stale = True
            else:
                if driver.url.endswith(self.expected_url):
                    is_stale = True
        return is_stale
