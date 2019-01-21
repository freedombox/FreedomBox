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
Help app for FreedomBox.
"""

import mimetypes
import os
import subprocess

from apt.cache import Cache
from django.core.files.base import File
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from plinth import __version__, cfg
from plinth.menu import main_menu


def init():
    """Initialize the Help module"""
    menu = main_menu.add_urlname(
        ugettext_lazy('Documentation'), 'fa-book', 'help:index')
    menu.add_urlname(
        ugettext_lazy('Manual'), 'fa-info-circle', 'help:manual', order=10)
    menu.add_urlname(
        ugettext_lazy('Download Manual'), 'fa-download',
        'help:download-manual', order=15)
    menu.add_urlname(
        ugettext_lazy('About'), 'fa-star', 'help:about', order=100)


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


def manual(request, page='freedombox-manual.part.html'):
    """Serve the manual page from the 'doc' directory"""
    try:
        page = '{}.part.html'.format(
            page) if not page.endswith('html') else page
        with open(os.path.join(cfg.doc_dir, page), 'r',
                  encoding='utf-8') as input_file:
            content = input_file.read()
    except IOError:
        raise Http404

    return TemplateResponse(
        request, 'help_manual.html', {
            'title': _('{box_name} Manual').format(box_name=_(cfg.box_name)),
            'content': content
        })


def download_manual(request):
    """Serve the PDF version of the manual from the 'doc' directory"""
    files = [
        os.path.join(cfg.doc_dir, file_name)
        for file_name in ['freedombox-manual.pdf.gz', 'freedombox-manual.pdf']
        if os.path.isfile(os.path.join(cfg.doc_dir, file_name))
    ]

    if not files:
        raise Http404

    (content_type, encoding) = mimetypes.guess_type(files[0])
    with open(files[0], 'rb') as file_handle:
        response = HttpResponse(File(file_handle), content_type=content_type)
        if encoding:
            response['Content-Encoding'] = encoding

        return response


def status_log(request):
    """Serve the last 100 lines of plinth's status log"""
    num_lines = 100
    command = [
        'journalctl', '--no-pager', '-n',
        str(num_lines), '-u', 'plinth'
    ]
    process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    data = process.stdout.decode()

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
