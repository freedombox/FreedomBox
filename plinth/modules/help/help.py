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

"""
Help module for Plinth.
"""

import os
from gettext import gettext as _
from django.http import Http404
from django.template.response import TemplateResponse
from stronghold.decorators import public

from plinth import cfg, __version__


def init():
    """Initialize the Help module"""
    menu = cfg.main_menu.add_urlname(_('Documentation'), 'glyphicon-book',
                                     'help:index', 101)
    menu.add_urlname(_('Where to Get Help'), 'glyphicon-search',
                     'help:index_explicit', 5)
    menu.add_urlname(_('FreedomBox Manual'), 'glyphicon-info-sign',
                     'help:manual', 10)
    menu.add_urlname(_('About'), 'glyphicon-star', 'help:about', 100)


@public
def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help_index.html',
                            {'title': _('Documentation and FAQ')})


@public
def about(request):
    """Serve the about page"""
    context = {
        'title': _('About the {box_name}').format(box_name=cfg.box_name),
        'version': __version__
    }
    return TemplateResponse(request, 'help_about.html', context)


@public
def manual(request):
    """Serve the manual page from the 'doc' directory"""
    try:
        with open(os.path.join(cfg.doc_dir, 'freedombox-manual.part.html'), 'r') \
             as input_file:
            content = input_file.read()
    except IOError:
        raise Http404

    return TemplateResponse(request, 'help_manual.html',
                            {'title': _('FreedomBox Manual'),
                             'content': content})
