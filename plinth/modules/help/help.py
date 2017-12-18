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

import gzip
import mimetypes
import os

from apt.cache import Cache
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from plinth import __version__, cfg
from plinth.menu import main_menu


def init():
    """Initialize the Help module"""
    menu = main_menu.add_urlname(
        ugettext_lazy('Documentation'), 'glyphicon-book', 'help:index')
    menu.add_urlname(
        ugettext_lazy('Where to Get Help'), 'glyphicon-search',
        'help:index-explicit', order=5)
    menu.add_urlname(
        ugettext_lazy('Manual'), 'glyphicon-info-sign', 'help:manual',
        order=10)
    menu.add_urlname(
        ugettext_lazy('Download Manual'), 'glyphicon-download-alt',
        'help:download-manual', order=15)
    menu.add_urlname(
        ugettext_lazy('About'), 'glyphicon-star', 'help:about', order=100)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help_index.html',
                            {'title': _('Documentation and FAQ')})


def about(request):
    """Serve the about page"""
    cache = Cache()
    plinth = cache['plinth']
    context = {
        'title': _('About {box_name}').format(box_name=_(cfg.box_name)),
        'version': __version__,
        'new_version': not plinth.candidate.is_installed,
        'os_release': get_os_release()
    }
    return TemplateResponse(request, 'help_about.html', context)


def manual(request):
    """Serve the manual page from the 'doc' directory"""
    try:
        with open(
                os.path.join(cfg.doc_dir, 'freedombox-manual.part.html'), 'r',
                encoding='utf-8') as input_file:
            content = input_file.read()
    except IOError:
        raise Http404

    return TemplateResponse(request, 'help_manual.html', {
        'title': _('{box_name} Manual').format(box_name=_(cfg.box_name)),
        'content': content
    })


def download_manual(request):
    """Serve the PDF version of the manual from the 'doc' directory"""
    manual_name = 'freedombox-manual.pdf.gz'
    try:
        with gzip.open(os.path.join(cfg.doc_dir, manual_name), 'rb') as f:
            content = f.read()
    except IOError:
        try:
            # pdf.gz doesn't exist. Try with .pdf
            manual_name = manual_name.rpartition('.')[0]
            with open(os.path.join(cfg.doc_dir, manual_name), 'rb') as f:
                content = f.read()
        except IOError:
            raise Http404('File {} does not exist.'.format(manual_name))

    return HttpResponse(
        ContentFile(content),
        content_type=mimetypes.guess_type(manual_name)[0])


def status_log(request):
    """Serve the last 100 lines of plinth's status log"""
    num_lines = 100
    with open(cfg.status_log_file, 'r') as log_file:
        data = log_file.readlines()

    data = ''.join(data[-num_lines:])
    context = {'num_lines': num_lines, 'data': data}
    return TemplateResponse(request, 'statuslog.html', context)


def get_os_release():
    """Returns the Debian release number and name"""
    output = 'Error: Cannot read PRETTY_NAME in /etc/os-release.'
    with open('/etc/os-release', 'r') as release_file:
        for line in release_file:
            if 'PRETTY_NAME=' in line:
                line = line.replace('"', '').strip()
                line = line.split('=')
                output = line[1]
    return output
