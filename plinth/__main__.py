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
import os
import stat
import sys
import warnings

import axes
import cherrypy
import django.conf
import django.core.management
import django.core.wsgi
from django.contrib.messages import constants as message_constants

from plinth import cfg, frontpage, menu, module_loader, service, setup

axes.default_app_config = "plinth.axes_app_config.AppConfig"
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


def setup_logging():
    """Setup logging framework"""
    # Don't propagate cherrypy log messages to root logger
    logging.getLogger('cherrypy').propagate = False

    cherrypy.log.error_file = cfg.status_log_file
    cherrypy.log.access_file = cfg.access_log_file

    # Capture all Python warnings such as deprecation warnings
    logging.captureWarnings(True)

    # Log all deprecation warnings when in develop mode
    if cfg.develop:
        warnings.filterwarnings('default', '', DeprecationWarning)
        warnings.filterwarnings('default', '', PendingDeprecationWarning)
        warnings.filterwarnings('default', '', ImportWarning)


def setup_server():
    """Setup CherryPy server"""
    logger.info('Setting up CherryPy server')

    # Configure default server
    cherrypy.config.update({
        'server.socket_host': cfg.host,
        'server.socket_port': cfg.port,
        'server.thread_pool': 10,
        # Avoid stating files once per second in production
        'engine.autoreload.on': cfg.develop,
    })

    application = django.core.wsgi.get_wsgi_application()
    cherrypy.tree.graft(application, cfg.server_dir)

    static_dir = os.path.join(cfg.file_root, 'static')
    config = {
        '/': {
            'tools.staticdir.root': static_dir,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
        }
    }
    cherrypy.tree.mount(None, django.conf.settings.STATIC_URL, config)
    logger.debug('Serving static directory %s on %s', static_dir,
                 django.conf.settings.STATIC_URL)

    custom_static_dir = cfg.custom_static_dir
    custom_static_url = '/plinth/custom/static'
    config = {
        '/': {
            'tools.staticdir.root': custom_static_dir,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
        }
    }
    cherrypy.tree.mount(None, custom_static_url, config)
    logger.debug('Serving custom static directory %s on %s', custom_static_dir,
                 custom_static_url)

    js_dir = '/usr/share/javascript'
    js_url = '/javascript'
    config = {
        '/': {
            'tools.staticdir.root': js_dir,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
        }
    }
    cherrypy.tree.mount(None, js_url, config)
    logger.debug('Serving javascript directory %s on %s', js_dir, js_url)

    manual_dir = os.path.join(cfg.doc_dir, 'images')
    manual_url = '/'.join([cfg.server_dir, 'help/manual/images']) \
        .replace('//', '/')
    config = {
        '/': {
            'tools.staticdir.root': manual_dir,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
        }
    }
    cherrypy.tree.mount(None, manual_url, config)
    logger.debug('Serving manual images %s on %s', manual_dir, manual_url)

    for module_name, module in module_loader.loaded_modules.items():
        module_path = os.path.dirname(module.__file__)
        static_dir = os.path.join(module_path, 'static')
        if not os.path.isdir(static_dir):
            continue

        config = {
            '/': {
                'tools.staticdir.root': static_dir,
                'tools.staticdir.on': True,
                'tools.staticdir.dir': '.'
            }
        }
        urlprefix = "%s%s" % (django.conf.settings.STATIC_URL, module_name)
        cherrypy.tree.mount(None, urlprefix, config)
        logger.debug('Serving static directory %s on %s', static_dir,
                     urlprefix)

    cherrypy.engine.signal_handler.subscribe()


def on_server_stop():
    """Stop all other threads since web server is trying to exit."""
    setup.stop()


def configure_django():
    """Setup Django configuration in the absence of .settings file"""
    logging_configuration = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format':
                    '[%(asctime)s] %(name)-14s %(levelname)-8s %(message)s',
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': cfg.status_log_file,
                'formatter': 'default'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            }
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if cfg.develop else 'INFO'
        }
    }

    templates = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.request',
                    'django.template.context_processors.static',
                    'django.template.context_processors.tz',
                    'django.contrib.messages.context_processors.messages',
                    'plinth.context_processors.common',
                ],
            },
        },
    ]

    applications = [
        'axes',
        'captcha',
        'bootstrapform',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.messages',
        'stronghold',
        'plinth',
    ]
    applications += module_loader.get_modules_to_load()
    sessions_directory = os.path.join(cfg.data_dir, 'sessions')

    secure_proxy_ssl_header = None
    if cfg.secure_proxy_ssl_header:
        secure_proxy_ssl_header = (cfg.secure_proxy_ssl_header, 'https')

    pwd = 'django.contrib.auth.password_validation'

    django.conf.settings.configure(
        ALLOWED_HOSTS=['*'],
        AUTH_PASSWORD_VALIDATORS=[
            {
                'NAME': '{}.UserAttributeSimilarityValidator'.format(pwd),
            },
            {
                'NAME': '{}.MinimumLengthValidator'.format(pwd),
                'OPTIONS': {
                    'min_length': 8,
                }
            },
            {
                'NAME': '{}.CommonPasswordValidator'.format(pwd),
            },
            {
                'NAME': '{}.NumericPasswordValidator'.format(pwd),
            },
        ],
        AXES_LOCKOUT_URL='locked/',
        AXES_BEHIND_REVERSE_PROXY=True,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
            }
        },
        CAPTCHA_FONT_PATH=[
            '/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf'
        ],
        CAPTCHA_LENGTH=6,
        CAPTCHA_FLITE_PATH='/usr/bin/flite',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': cfg.store_file
            }
        },
        DEBUG=cfg.develop,
        FORCE_SCRIPT_NAME=cfg.server_dir,
        INSTALLED_APPS=applications,
        IPWARE_META_PRECEDENCE_ORDER=('HTTP_X_FORWARDED_FOR', ),
        LOGGING=logging_configuration,
        LOGIN_URL='users:login',
        LOGIN_REDIRECT_URL='index',
        MESSAGE_TAGS={message_constants.ERROR: 'danger'},
        MIDDLEWARE=(
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'stronghold.middleware.LoginRequiredMiddleware',
            'plinth.middleware.AdminRequiredMiddleware',
            'plinth.middleware.FirstSetupMiddleware',
            'plinth.modules.first_boot.middleware.FirstBootMiddleware',
            'plinth.middleware.SetupMiddleware',
        ),
        ROOT_URLCONF='plinth.urls',
        SECURE_BROWSER_XSS_FILTER=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        SECURE_PROXY_SSL_HEADER=secure_proxy_ssl_header,
        SESSION_ENGINE='django.contrib.sessions.backends.file',
        SESSION_FILE_PATH=sessions_directory,
        STATIC_URL='/'.join([cfg.server_dir, 'static/']).replace('//', '/'),
        # STRONGHOLD_PUBLIC_URLS=(r'^captcha/', ),
        STRONGHOLD_PUBLIC_NAMED_URLS=(
            'captcha-image',
            'captcha-image-2x',
            'captcha-audio',
            'captcha-refresh',
        ),
        TEMPLATES=templates,
        USE_L10N=True,
        USE_X_FORWARDED_HOST=cfg.use_x_forwarded_host)
    django.setup(set_prefix=True)

    logger.debug('Configured Django with applications - %s', applications)

    logger.debug('Creating or adding new tables to data file')
    verbosity = 1 if cfg.develop else 0
    django.core.management.call_command('migrate', '--fake-initial',
                                        interactive=False, verbosity=verbosity)
    os.chmod(cfg.store_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)


def run_setup_and_exit(module_list, allow_install=True):
    """Run setup on all essential modules and exit."""
    error_code = 0
    try:
        setup.run_setup_on_modules(module_list, allow_install)
    except Exception as exception:
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

    setup_logging()

    service.init()

    configure_django()

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
    setup_server()

    cherrypy.engine.start()
    cherrypy.engine.subscribe('stop', on_server_stop)
    cherrypy.engine.block()


if __name__ == '__main__':
    main()
