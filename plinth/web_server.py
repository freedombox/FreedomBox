# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Setup CherryPy web server.
"""

import logging
import os

import cherrypy

from . import cfg, log, module_loader, web_framework

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

    langs = os.listdir(os.path.join(cfg.doc_dir, 'manual'))
    for lang in langs:
        manual_dir = os.path.join(cfg.doc_dir, 'manual', lang, 'images')
        manual_url = '/'.join([cfg.server_dir, f'help/manual/{lang}/images']) \
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


def run(on_web_server_stop):
    """Start the web server and block it until exit."""
    cherrypy.engine.start()
    cherrypy.engine.subscribe('stop', on_web_server_stop)
    cherrypy.engine.block()
