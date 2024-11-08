# SPDX-License-Identifier: AGPL-3.0-or-later
"""
pytest configuration for all tests.
"""

import importlib
import os
import pathlib

import pytest

try:
    importlib.import_module('splinter')
    importlib.import_module('selenium')
    _functional_libs_available = True
except ImportError:
    _functional_libs_available = False


def pytest_ignore_collect(path, config):
    """Ignore functional tests when splinter is not available."""
    if path.basename == 'test_functional.py':
        return not _functional_libs_available


def pytest_configure(config):
    """Register additional markers, one for each app."""
    for app in (pathlib.Path(__file__).parent / 'modules').iterdir():
        if not app.is_dir():
            continue

        config.addinivalue_line('markers', app.name)


def pytest_collection_modifyitems(config, items):
    """Filter out specificly marked tests unless explicitly requested.

    The EXTENDED_TESTING environment variable is borrowed from the Lancaster
    consensus met by the Pearl community. See
    https://github.com/Perl-Toolchain-Gang/toolchain-site/blob/master/lancaster-consensus.md
    """

    def skip(item, reason):
        item.add_marker(pytest.mark.skip(reason=reason))

    extended = 'EXTENDED_TESTING' in os.environ
    if not (extended or config.getoption('--include-functional')):
        for item in items:
            if 'functional' in item.keywords or (
                    item.parent.fspath.basename
                    and item.parent.fspath.basename == 'test_functional.py'):
                skip(item, '--include-functional not provided')

    if not extended:
        for item in items:
            if 'heavy' in item.keywords:
                skip(item, ('Takes too much time. '
                            'Set EXTENDED_TESTING=1 to force run'))


@pytest.fixture(name='load_cfg')
def fixture_load_cfg():
    """Load test configuration."""
    from plinth import cfg

    keys = ('file_root', 'config_dir', 'data_dir', 'custom_static_dir',
            'store_file', 'actions_dir', 'doc_dir', 'server_dir', 'host',
            'port', 'use_x_forwarded_for', 'use_x_forwarded_host',
            'secure_proxy_ssl_header', 'box_name', 'develop')
    saved_state = {}
    for key in keys:
        saved_state[key] = getattr(cfg, key)

    root_dir = pathlib.Path(__file__).resolve().parent
    cfg_file = root_dir / 'plinth' / 'develop.config'
    cfg.read_file(str(cfg_file))
    yield cfg

    for key in keys:
        setattr(cfg, key, saved_state[key])


@pytest.fixture(name='develop_mode')
def fixture_develop_mode(load_cfg):
    """Turn on development mode for a test."""
    load_cfg.develop = True
    yield
    load_cfg.develop = False


@pytest.fixture(name='needs_root', scope='session')
def fixture_needs_root():
    """Skip test if not running in root mode."""
    if os.geteuid() != 0:
        pytest.skip('Needs to be root')


@pytest.fixture(name='needs_not_root', scope='session')
def fixture_needs_not_root():
    """Skip test if running in root mode."""
    if os.geteuid() == 0:
        pytest.skip('Needs not to be root')


@pytest.fixture(name='needs_sudo')
def fixture_needs_sudo():
    """Skip test if sudo command is not available."""
    if not os.path.isfile('/usr/bin/sudo'):
        pytest.skip('Needs sudo command installed.')


@pytest.fixture(scope='session')
def splinter_selenium_implicit_wait():
    """Disable implicit waiting."""
    return 0


@pytest.fixture(scope='session')
def splinter_wait_time():
    """Disable explicit waiting."""
    return 0.01


@pytest.fixture(scope='session')
def splinter_browser_load_condition():
    """When a page it loaded, wait until <body> is available."""

    def _load_condition(browser):
        if browser.url == 'about:blank':
            return True

        ready_state = browser.execute_script('return document.readyState;')
        return ready_state == 'complete'

    return _load_condition


@pytest.fixture(name='mock_privileged')
def fixture_mock_privileged(request):
    """Mock the privileged decorator to nullify its effects."""
    try:
        privileged_modules_to_mock = request.module.privileged_modules_to_mock
    except AttributeError:
        raise AttributeError(
            'mock_privileged fixture requires "privileged_module_to_mock" '
            'attribute at module level')

    for module_name in privileged_modules_to_mock:
        module = importlib.import_module(module_name)
        for name, member in module.__dict__.items():
            wrapped = getattr(member, '__wrapped__', None)
            if not callable(member) or not wrapped:
                continue

            if not getattr(member, '_privileged', False):
                continue

            setattr(wrapped, '_original_wrapper', member)
            module.__dict__[name] = wrapped

    yield

    for module_name in privileged_modules_to_mock:
        module = importlib.import_module(module_name)
        for name, member in module.__dict__.items():
            wrapper = getattr(member, '_original_wrapper', None)
            if not callable(member) or not wrapper:
                continue

            module.__dict__[name] = wrapper


@pytest.fixture(name='splinter_screenshot_dir', scope='session')
def fixture_splinter_screenshot_dir(request):
    """Set default screenshot directory to ./screenshots.

    This can be overridden using --splinter-screenshot-dir=foo as the option.
    """
    option = request.config.getoption('--splinter-screenshot-dir')
    screenshots_dir = option if option != '.' else './screenshots'
    return os.path.abspath(screenshots_dir)


@pytest.fixture(autouse=True)
def fixture_fix_session_browser_screenshots(request):
    """Fix a bug in pytest-splinter for screenshots.

    When using session_browser, pytest-splinter does not take a screenshot when
    a test has failed. It is uses internal pytest API on the FixtureRequest
    object. This API was removed in later versions of pytest causing the
    failure. Re-implement the fixture that has the problem fixing this issue.

    Drop this fixture after a fix is merged and released in pytest-splinter.
    See: https://github.com/pytest-dev/pytest-splinter/pull/157
    """
    yield

    if not request.config.pluginmanager.has_plugin('pytest-splinter'):
        return

    session_tmpdir = request.getfixturevalue('session_tmpdir')
    splinter_session_scoped_browser = request.getfixturevalue(
        'splinter_session_scoped_browser')
    splinter_make_screenshot_on_failure = request.getfixturevalue(
        'splinter_make_screenshot_on_failure')
    splinter_screenshot_dir = request.getfixturevalue(
        'splinter_screenshot_dir')
    splinter_screenshot_getter_html = request.getfixturevalue(
        'splinter_screenshot_getter_html')
    splinter_screenshot_getter_png = request.getfixturevalue(
        'splinter_screenshot_getter_png')
    splinter_screenshot_encoding = request.getfixturevalue(
        'splinter_screenshot_encoding')

    # Screenshot for function scoped browsers is handled in
    # browser_instance_getter
    if not splinter_session_scoped_browser:
        return

    for name in request.fixturenames:
        fixture_def = request._fixture_defs.get(name)
        if not fixture_def or not fixture_def.cached_result:
            continue

        value = fixture_def.cached_result[0]
        should_take_screenshot = (hasattr(value, '__splinter_browser__')
                                  and splinter_make_screenshot_on_failure
                                  and getattr(request.node, 'splinter_failure',
                                              True))

        from pytest_splinter import plugin
        if should_take_screenshot:
            kwargs = {
                'request':
                    request,
                'fixture_name':
                    name,
                'session_tmpdir':
                    session_tmpdir,
                'browser_instance':
                    value,
                'splinter_screenshot_dir':
                    splinter_screenshot_dir,
                'splinter_screenshot_getter_html':
                    splinter_screenshot_getter_html,
                'splinter_screenshot_getter_png':
                    splinter_screenshot_getter_png,
                'splinter_screenshot_encoding':
                    splinter_screenshot_encoding
            }

            plugin._take_screenshot(**kwargs)


@pytest.fixture(name='host_sudo')
def fixture_host_sudo(host):
    """Pytest fixture to run commands with sudo."""
    with host.sudo():
        yield host
