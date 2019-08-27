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

from plinth import __version__, actions
from plinth import app as app_module
from plinth import cfg, menu

app = None


class HelpApp(app_module.App):
    """FreedomBox app for showing help."""

    app_id = 'help'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-help', ugettext_lazy('Documentation'),
                              None, 'fa-book', 'help:index',
                              parent_url_name='index')
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-manual', ugettext_lazy('Manual'),
                              None, 'fa-info-circle', 'help:manual',
                              parent_url_name='help:index', order=10)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-download-manual',
                              ugettext_lazy('Download Manual'), None,
                              'fa-download', 'help:download-manual',
                              parent_url_name='help:index', order=15)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-support',
                              ugettext_lazy('Get Support'), None,
                              'fa-life-ring', 'help:support',
                              parent_url_name='help:index', order=20)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-feedback',
                              ugettext_lazy('Submit Feedback'), None,
                              'fa-comments', 'help:feedback',
                              parent_url_name='help:index', order=25)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-about', ugettext_lazy('About'), None,
                              'fa-star', 'help:about',
                              parent_url_name='help:index', order=100)
        self.add(menu_item)


def init():
    """Initialize the Help module"""
    global app
    app = HelpApp()
    app.set_enabled(True)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help_index.html',
                            {'title': _('Documentation and FAQ')})


def feedback(request):
    """Serve the feedback page"""
    return TemplateResponse(request, 'help_feedback.html',
                            {'title': _('Submit Feedback')})


def support(request):
    """Serve the support page"""
    return TemplateResponse(request, 'help_support.html',
                            {'title': _('Get Support')})


def about(request):
    """Serve the about page"""
    cache = Cache()
    freedombox = cache['freedombox']
    context = {
        'title': _('About {box_name}').format(box_name=_(cfg.box_name)),
        'version': __version__,
        'new_version': not freedombox.candidate.is_installed,
        'os_release': get_os_release(),
        'backports_in_use': get_backports_in_use(),
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
    output = actions.superuser_run('help', ['get-logs'])
    context = {'num_lines': 100, 'data': output}
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


def get_backports_in_use():
    """Return whether backports packages are installed."""
    # Only freedombox package is set to be installed from backports currently.
    output = subprocess.check_output(['apt-cache', 'policy', 'freedombox'])
    for line in output.decode().split('\n'):
        if 'Installed:' in line:
            version = line.strip().split(': ')[1]
            if 'bpo' in version:
                return True

    return False
