#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from contextlib import contextmanager
from time import sleep

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait

from support import interface

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
    return len(browser.find_by_css('.running-status.active')) != 0


def is_not_running(browser, service_name):
    interface.nav_to_module(browser, get_service_module(service_name))
    return len(browser.find_by_css('.running-status.inactive')) != 0


def eventually(function, args=[], timeout=30):
    """Execute a function returning a boolean expression till it returns
    True or a timeout is reached"""
    counter = 1
    while counter < timeout:
        if function(*args):
            return True
        else:
            counter += 1
            sleep(1)
    return False


@contextmanager
def wait_for_page_update(browser, timeout=300):
    current_page = browser.find_by_tag('html').first
    yield
    WebDriverWait(browser, timeout).until(is_stale(current_page))


class is_stale():
    def __init__(self, element):
        self.element = element

    def __call__(self, driver):
        try:
            self.element.has_class('whatever_class')
            return False
        except StaleElementReferenceException:
            return True
