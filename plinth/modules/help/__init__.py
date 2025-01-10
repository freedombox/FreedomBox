# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for help pages.
"""

import logging
import os

from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from plinth import app as app_module
from plinth import cfg, menu, web_server

logger = logging.getLogger(__name__)


class HelpApp(app_module.App):
    """FreedomBox app for showing help."""

    app_id = 'help'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True)
        self.add(info)

        menu_item = menu.Menu('menu-help', _('Help'), None, 'fa-book',
                              'help:index', parent_url_name='index')
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-manual',
                              pgettext_lazy('User guide', 'Manual'), None,
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

    def post_init(self):
        """Perform post initialization operations."""
        directory_map = {}
        try:
            langs = os.listdir(os.path.join(cfg.doc_dir, 'manual'))
            for lang in langs:
                manual_dir = os.path.join(cfg.doc_dir, 'manual', lang,
                                          'images')
                manual_url = f'/help/manual/{lang}/images'
                directory_map[manual_url] = manual_dir
        except FileNotFoundError:
            logger.error('Unable to find manual directory. Ensure that '
                         'freedombox-doc-* packages are installed')

        static_files = web_server.StaticFiles('static-files-help',
                                              directory_map)
        self.add(static_files)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()
