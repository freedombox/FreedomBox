#
# This file is part of Plinth.
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

import os
from gettext import gettext as _
from django.http import Http404
from django.template.response import TemplateResponse

from plinth import cfg


def init():
    """Initialize the Help module"""
    menu = cfg.main_menu.add_urlname(_('Documentation'), 'glyphicon-book',
                                     'help:index', 101)
    menu.add_urlname(_('Where to Get Help'), 'glyphicon-search',
                     'help:index_explicit', 5)
    menu.add_urlname(_('Developer\'s Manual'), 'glyphicon-info-sign',
                     'help:helppage', 10, url_args=('plinth',))
    menu.add_urlname(_('FAQ'), 'glyphicon-question-sign', 'help:helppage', 20,
                     url_args=('faq',))
    menu.add_item(_('%s Wiki' % cfg.box_name), 'glyphicon-pencil',
                  'http://wiki.debian.org/FreedomBox', 30)
    menu.add_urlname(_('About'), 'glyphicon-star', 'help:about', 100)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help_index.html',
                            {'title': _('Documentation and FAQ')})


def about(request):
    """Serve the about page"""
    title = _('About the {box_name}').format(box_name=cfg.box_name)
    return TemplateResponse(request, 'help_about.html', {'title': title})


def helppage(request, page):
    """Serve a help page from the 'doc' directory"""
    try:
        with open(os.path.join(cfg.doc_dir, '%s.part.html' % page), 'r') \
                as input_file:
            content = input_file.read()
    except IOError:
        raise Http404

    title = _('%s Documentation') % cfg.product_name
    return TemplateResponse(request, 'help_detail.html',
                            {'title': title, 'content': content})
