#!/usr/bin/python3
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

import argparse
import importlib
import logging
import sys

from . import (__version__, cfg, dbus, frontpage, log, menu, module_loader,
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
    parser.add_argument('--diagnose', action='store_true', default=False,
                        help='run diagnostic tests and exit')
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


def run_diagnostics_and_exit():
    """Run diagostics on all modules and exit."""
    module = importlib.import_module('plinth.modules.diagnostics.diagnostics')
    error_code = 0
    try:
        module.run_on_all_modules()
    except Exception as exception:
        logger.exception('Error running diagnostics - %s', exception)
        error_code = 2

    for module, results in module.current_results['results'].items():
        for test, result_value in results:
            print('{result_value}: {module}: {test}'.format(
                result_value=result_value, test=test, module=module))
            if result_value != 'passed':
                error_code = 1

    sys.exit(error_code)


def adapt_config(arguments):
    """Give commandline arguments precedence over plinth.config entries"""
    for argument_name in precedence_commandline_arguments:
        argument_value = getattr(arguments, argument_name)
        if argument_value is not None:
            setattr(cfg, argument_name, argument_value)


def on_web_server_stop():
    """Stop all other threads since web server is trying to exit."""
    setup.stop()
    dbus.stop()


def main():
    """Intialize and start the application"""
    arguments = parse_arguments()

    if arguments.develop:
        # use the root and plinth.config of the current working directory
        config_path, root_directory = cfg.get_fallback_config_paths()
        cfg.read(config_path, root_directory)
    else:
        cfg.read()

    adapt_config(arguments)

    log.init()

    web_framework.init()

    logger.info('FreedomBox Service (Plinth) version - %s', __version__)
    logger.info('Configuration loaded from file - %s', cfg.config_file)
    logger.info('Script prefix - %s', cfg.server_dir)

    module_loader.include_urls()

    menu.init()

    module_loader.load_modules()
    frontpage.add_custom_shortcuts()

    if arguments.setup is not False:
        run_setup_and_exit(arguments.setup, allow_install=True)

    if arguments.setup_no_install is not False:
        run_setup_and_exit(arguments.setup_no_install, allow_install=False)

    if arguments.list_dependencies is not False:
        list_dependencies(arguments.list_dependencies)

    if arguments.list_modules is not False:
        list_modules(arguments.list_modules)

    if arguments.diagnose:
        run_diagnostics_and_exit()

    setup.run_setup_in_background()

    dbus.run()

    web_server.init()
    web_server.run(on_web_server_stop)


if __name__ == '__main__':
    main()
