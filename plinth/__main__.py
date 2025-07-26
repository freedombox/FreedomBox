#!/usr/bin/python3
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import logging
import sys
import threading

import systemd.daemon

from . import __version__
from . import app as app_module
from . import (cfg, frontpage, glib, log, menu, module_loader, setup,
               web_framework, web_server)

precedence_commandline_arguments = ["server_dir", "develop"]

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Core functionality and web interface for FreedomBox',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # TODO: server_dir is actually a url prefix; use a better variable name
    parser.add_argument('--server_dir', default=None,
                        help='web server path under which to serve')
    parser.add_argument(
        '--develop', action='store_true', default=None,
        help=('run Plinth *insecurely* from current folder; '
              'enable auto-reloading and debugging options'))
    parser.add_argument('--setup', default=False, nargs='*',
                        help='run setup tasks on all essential apps and exit')
    parser.add_argument(
        '--setup-no-install', default=False, nargs='*',
        help='run setup tasks without installing packages and exit')
    parser.add_argument('--list-dependencies', default=False, nargs='*',
                        help='list package dependencies for essential modules')
    parser.add_argument('--list-apps', default=False, nargs='*',
                        help='list apps')
    parser.add_argument('--version', action='store_true', default=None,
                        help='show version and exit')

    return parser.parse_args()


def run_setup_and_exit(app_ids, allow_install=True):
    """Run setup on all essential apps and exit."""
    error_code = 0
    try:
        setup.run_setup_on_apps(app_ids, allow_install)
    except Exception:
        error_code = 1

    sys.exit(error_code)


def list_dependencies(app_ids):
    """List dependencies for all essential apps and exit."""
    error_code = 0
    try:
        if app_ids:
            setup.list_dependencies(app_ids=app_ids)
        else:
            setup.list_dependencies(essential=True)
    except Exception as exception:
        logger.error('Error listing dependencies - %s', exception)
        error_code = 1

    sys.exit(error_code)


def list_apps(apps_type):
    """List all/essential/optional apps and exit."""
    for app in app_module.App.list():
        is_essential = app.info.is_essential
        if 'essential' in apps_type and not is_essential:
            continue

        if 'optional' in apps_type and is_essential:
            continue

        print(f'{app.app_id}')

    sys.exit()


def adapt_config(arguments):
    """Give commandline arguments precedence over config entries"""
    for argument_name in precedence_commandline_arguments:
        argument_value = getattr(arguments, argument_name)
        if argument_value is not None:
            setattr(cfg, argument_name, argument_value)


def on_web_server_stop():
    """Stop all other threads since web server is trying to exit."""
    setup.stop()
    glib.stop()


def run_post_init_and_setup():
    """Run post-init operations on the apps and setup operations."""
    app_module.apps_post_init()
    frontpage.add_custom_shortcuts()

    # Handle app version updates.
    setup.run_setup_on_startup()  # Long running, retrying

    # Handle packages that have been updated else where that need a re-run of
    # setup.
    setup.on_dpkg_invoked()

    # Handle packages that have a pending configuration file prompt.
    setup.on_package_cache_updated()


def main():
    """Initialize and start the application"""
    arguments = parse_arguments()

    cfg.read()
    if arguments.develop:
        # Use the config in the current working directory
        cfg.read_file(cfg.get_develop_config_path())

    adapt_config(arguments)

    if arguments.version:
        print(f'FreedomBox {__version__}')
        sys.exit(0)

    if arguments.list_dependencies is not False:
        log.default_level = 'ERROR'
        module_loader.load_modules()
        app_module.apps_init()
        list_dependencies(arguments.list_dependencies)

    if arguments.list_apps is not False:
        log.default_level = 'ERROR'
        module_loader.load_modules()
        app_module.apps_init()
        list_apps(arguments.list_apps)

    log.init()

    web_framework.init()
    web_framework.post_init()

    logger.info('FreedomBox Service (Plinth) version - %s', __version__)
    for config_file in cfg.config_files:
        logger.info('Configuration loaded from file - %s', config_file)
    logger.info('Script prefix - %s', cfg.server_dir)

    module_loader.include_urls()

    menu.init()

    module_loader.load_modules()
    app_module.apps_init()

    if arguments.setup is not False:
        app_module.apps_post_init()
        run_setup_and_exit(arguments.setup, allow_install=True)

    if arguments.setup_no_install is not False:
        app_module.apps_post_init()
        run_setup_and_exit(arguments.setup_no_install, allow_install=False)

    threading.Thread(target=run_post_init_and_setup).start()

    glib.run()

    web_server.init()
    web_server.run(on_web_server_stop)

    # systemd will wait until notification to proceed with other processes. We
    # have service Type=notify.
    systemd.daemon.notify('READY=1')

    web_server.block()


if __name__ == '__main__':
    main()
