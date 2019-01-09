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
"""
Setup CherryPy web server.
"""

import logging
import os

import cherrypy

from . import cfg, log, module_loader, setup, web_framework

logger = logging.getLogger(__name__)


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
    logger.debug('Serving static directory %s on %s', static_dir, static_url)


def init():
    """Setup CherryPy server"""
    logger.info('Setting up CherryPy server')

    # Configure default server
    cherrypy.config.update({
        'server.max_request_body_size': 0,
        'server.socket_host': cfg.host,
        'server.socket_port': cfg.port,
        'server.thread_pool': 10,
        # Avoid stating files once per second in production
        'engine.autoreload.on': cfg.develop,
    })

    application = web_framework.get_wsgi_application()
    cherrypy.tree.graft(application, cfg.server_dir)

    static_dir = os.path.join(cfg.file_root, 'static')
    _mount_static_directory(static_dir, web_framework.get_static_url())

    custom_static_dir = cfg.custom_static_dir
    custom_static_url = '/plinth/custom/static'
    if os.path.exists(custom_static_dir):
        _mount_static_directory(custom_static_dir, custom_static_url)
    else:
        logger.debug(
            'Not serving custom static directory %s on %s, '
            'directory does not exist', custom_static_dir, custom_static_url)

    _mount_static_directory('/usr/share/javascript', '/javascript')

    manual_dir = os.path.join(cfg.doc_dir, 'images')
    manual_url = '/'.join([cfg.server_dir, 'help/manual/images']) \
        .replace('//', '/')
    _mount_static_directory(manual_dir, manual_url)

    for module_name, module in module_loader.loaded_modules.items():
        module_path = os.path.dirname(module.__file__)
        static_dir = os.path.join(module_path, 'static')
        if not os.path.isdir(static_dir):
            continue

        urlprefix = "%s%s" % (web_framework.get_static_url(), module_name)
        _mount_static_directory(static_dir, urlprefix)

    cherrypy.engine.signal_handler.subscribe()


def on_server_stop():
    """Stop all other threads since web server is trying to exit."""
    setup.stop()


def run():
    """Start the web server and block it until exit."""
    cherrypy.engine.start()
    cherrypy.engine.subscribe('stop', on_server_stop)
    cherrypy.engine.block()
