# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for help pages.
"""

import os

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu, web_server

version = 1

is_essential = True
app = None


class HelpApp(app_module.App):
    """FreedomBox app for showing help."""

    app_id = 'help'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential)
        self.add(info)

        menu_item = menu.Menu('menu-help', _('Documentation'), None, 'fa-book',
                              'help:index', parent_url_name='index')
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-manual', _('Manual'), None,
                              'fa-info-circle', 'help:manual',
                              parent_url_name='help:index', order=10)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-support', _('Get Support'), None,
                              'fa-life-ring', 'help:support',
                              parent_url_name='help:index', order=20)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-feedback', _('Submit Feedback'), None,
                              'fa-comments', 'help:feedback',
                              parent_url_name='help:index', order=25)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-contribute', _('Contribute'), None,
                              'fa-wrench', 'help:contribute',
                              parent_url_name='help:index', order=30)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-about', _('About'), None, 'fa-star',
                              'help:about', parent_url_name='help:index',
                              order=100)
        self.add(menu_item)

        directory_map = {}
        langs = os.listdir(os.path.join(cfg.doc_dir, 'manual'))
        for lang in langs:
            manual_dir = os.path.join(cfg.doc_dir, 'manual', lang, 'images')
            manual_url = f'/help/manual/{lang}/images'
            directory_map[manual_url] = manual_dir

        static_files = web_server.StaticFiles('static-files-help',
                                              directory_map)
        self.add(static_files)


def init():
    """Initialize the Help module"""
    global app
    app = HelpApp()
    app.set_enabled(True)
