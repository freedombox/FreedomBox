
import os.path

import pytest
from selenium import webdriver


@pytest.fixture(scope="module")
def browser():
    b = webdriver.PhantomJS()
    b.set_window_size(1120, 550)
    # TODO: quit
    return b


_screenshot_cnt = 0


def shot(browser, title):
    global _screenshot_cnt
    _screenshot_cnt += 1
    d = '/tmp/artifacts/screenshots'
    fn = os.path.join(d, "{:03d}_{}.png".format(_screenshot_cnt, title))
    browser.save_screenshot(fn)


@pytest.mark.integ_browser
def test_browser(browser):
    """Test first login, account creation, setup.
    """
    browser.get("https://127.0.0.1:443")
    shot(browser, "initial")
