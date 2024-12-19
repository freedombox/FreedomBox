# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Setup CherryPy web server.
"""

import logging
import os
import pathlib
import sys
import warnings
from typing import ClassVar

import cherrypy

from . import app as app_module
from . import cfg, log, web_framework

logger = logging.getLogger(__name__)

# When an app installs a python module as a dependency and imports it. CherryPy
# will start monitoring it for changes. When the app is uninstalled, the module
# is removed from the system leading to change detected by CherryPy. The entire
# service is then restarted if it is in development mode. This could cause a
# temporary failure in requests served leading to failures in functional tests.
# Workaround this by preventing auto-reloading for some python modules.
MODULES_EXCLUDED_FROM_AUTORELOAD = [
    'iso3166',
    'psycopg2',
]

_CUSTOM_STATIC_URL = '/custom/static'

_USER_CSS_PATH = 'css/user.css'


def get_custom_static_url():
    """Return the URL path fragment for custom static URL."""
    return f'{cfg.server_dir}{_CUSTOM_STATIC_URL}'


def get_user_css():
    """Return the URL path fragement for user CSS if it exists else None."""
    user_css_path = pathlib.Path(cfg.custom_static_dir) / _USER_CSS_PATH
    if not user_css_path.exists():
        return None

    return get_custom_static_url() + '/' + _USER_CSS_PATH


def _mount_static_directory(static_dir, static_url):
    config = {
        '/': {
            'tools.staticdir.root': static_dir,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
        }
    }
    app = cherrypy.tree.mount(None, static_url, config)
    log.setup_cherrypy_static_directory(app)


def init():
    """Setup CherryPy server"""
    logger.info('Setting up CherryPy server')

    exclude_modules = '|'.join(MODULES_EXCLUDED_FROM_AUTORELOAD)
    autoreload_regex = rf'^(?!(?:{exclude_modules})).+'
    # Configure default server
    cherrypy.config.update({
        'server.max_request_body_size': 0,
        'server.socket_host': cfg.host,
        'server.socket_port': cfg.port,
        'server.thread_pool': 10,
        # Avoid stating files once per second in production
        'engine.autoreload.on': cfg.develop,
        'engine.autoreload.match': autoreload_regex,
    })

    application = web_framework.get_wsgi_application()
    cherrypy.tree.graft(application, cfg.server_dir)

    static_dir = os.path.join(cfg.file_root, 'static')
    _mount_static_directory(static_dir, web_framework.get_static_url())

    custom_static_dir = cfg.custom_static_dir
    custom_static_url = get_custom_static_url()
    if os.path.exists(custom_static_dir):
        _mount_static_directory(custom_static_dir, custom_static_url)
    else:
        logger.debug(
            'Not serving custom static directory %s on %s, '
            'directory does not exist', custom_static_dir, custom_static_url)

    _mount_static_directory('/usr/share/javascript', '/javascript')

    for app in app_module.App.list():
        module = sys.modules[app.__module__]
        module_path = os.path.dirname(module.__file__)
        static_dir = os.path.join(module_path, 'static')
        if not os.path.isdir(static_dir):
            continue

        urlprefix = "%s%s" % (web_framework.get_static_url(), app.app_id)
        _mount_static_directory(static_dir, urlprefix)

    for component in StaticFiles.list():
        component.mount()

    cherrypy.engine.signal_handler.subscribe()


def run(on_web_server_stop):
    """Start the web server and block it until exit."""
    with warnings.catch_warnings():
        # Suppress warning that some of the static directories don't exist.
        # Since there is no way to add/remove those tree mounts at will, we
        # need to add them all before hand even if they don't exist now. If the
        # directories becomes available later, CherryPy serves them just fine.
        warnings.filterwarnings(
            'ignore', '(.|\n)*is not an existing filesystem path(.|\n)*',
            UserWarning)
        cherrypy.engine.start()

    cherrypy.engine.subscribe('stop', on_web_server_stop)
    cherrypy.engine.block()


class StaticFiles(app_module.FollowerComponent):
    """Component to serve static files shipped with an app.

    Any files in <app>/static directory will be automatically served on
    /static/<app>/ directory by FreedomBox. This allows each app to ship custom
    static files that are served by the web server.

    However, in some rare circumstances, a system folder will need to be served
    on a path for the app to work. This component allows declaring such
    directories and the web paths they should be served on.

    """

    _all_instances: ClassVar[dict[str, 'StaticFiles']] = {}

    def __init__(self, component_id, directory_map=None):
        """Initialize the component.

        component_id should be a unique ID across all components of an app and
        across all components.

        directory_map should be a dictionary with keys to be web paths and
        values to be absolute path of the directory on disk to serve. The
        static files from the directory are served over the given web path. The
        web path will be prepended with the FreedomBox's configured base web
        path. For example, {'/foo': '/usr/share/foo'} means that
        '/usr/share/foo/bar.png' will be served over '/plinth/foo/bar.png' if
        FreedomBox is configured to be served on '/plinth'.

        """
        super().__init__(component_id)
        self.directory_map = directory_map
        self._all_instances[component_id] = self

    @classmethod
    def list(cls):
        """Return a list of all instances."""
        return cls._all_instances.values()

    def mount(self):
        """Perform configuration of the web server to handle static files.

        Called by web server abstraction layer after web server has been setup.

        """
        if self.directory_map:
            for web_path, file_path in self.directory_map.items():
                web_path = '%s%s' % (cfg.server_dir, web_path)
                _mount_static_directory(file_path, web_path)
