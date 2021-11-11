#!/usr/bin/python3
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import logging
import sys

from . import (__version__, cfg, frontpage, glib, log, menu, module_loader,
               setup, utils, web_framework, web_server)

if utils.is_axes_old():
    import axes
    axes.default_app_config = 'plinth.axes_app_config.AppConfig'

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
    parser.add_argument(
        '--setup', default=False, nargs='*',
        help='run setup tasks on all essential modules and exit')
    parser.add_argument(
        '--setup-no-install', default=False, nargs='*',
        help='run setup tasks without installing packages and exit')
    parser.add_argument('--list-dependencies', default=False, nargs='*',
                        help='list package dependencies for essential modules')
    parser.add_argument('--list-modules', default=False, nargs='*',
                        help='list modules')

    return parser.parse_args()


def run_setup_and_exit(module_list, allow_install=True):
    """Run setup on all essential modules and exit."""
    error_code = 0
    try:
        setup.run_setup_on_modules(module_list, allow_install)
    except Exception:
        error_code = 1

    sys.exit(error_code)


def list_dependencies(module_list):
    """List dependencies for all essential modules and exit."""
    error_code = 0
    try:
        if module_list:
            setup.list_dependencies(module_list=module_list)
        else:
            setup.list_dependencies(essential=True)
    except Exception as exception:
        logger.error('Error listing dependencies - %s', exception)
        error_code = 1

    sys.exit(error_code)


def list_modules(modules_type):
    """List all/essential/optional modules and exit."""
    for module_name, module in module_loader.loaded_modules.items():
        module_is_essential = getattr(module, 'is_essential', False)
        if 'essential' in modules_type and not module_is_essential:
            continue
        elif 'optional' in modules_type and module_is_essential:
            continue
        print('{module_name}'.format(module_name=module_name))
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


def main():
    """Initialize and start the application"""
    arguments = parse_arguments()

    cfg.read()
    if arguments.develop:
        # Use the config in the current working directory
        cfg.read_file(cfg.get_develop_config_path())

    adapt_config(arguments)

    if arguments.list_dependencies is not False:
        log.default_level = 'ERROR'
        web_framework.init(read_only=True)
        module_loader.include_urls()
        menu.init()
        module_loader.load_modules()
        list_dependencies(arguments.list_dependencies)

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
    frontpage.add_custom_shortcuts()

    if arguments.setup is not False:
        run_setup_and_exit(arguments.setup, allow_install=True)

    if arguments.setup_no_install is not False:
        run_setup_and_exit(arguments.setup_no_install, allow_install=False)

    if arguments.list_modules is not False:
        list_modules(arguments.list_modules)

    setup.run_setup_in_background()

    glib.run()

    web_server.init()
    web_server.run(on_web_server_stop)


if __name__ == '__main__':
    main()
