# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Help app for FreedomBox.
"""

import mimetypes
import os
import pathlib
import subprocess

from apt.cache import Cache
from django.core.files.base import File
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext as _

from plinth import __version__, actions, cfg


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help_index.html',
                            {'title': _('Documentation and FAQ')})


def contribute(request):
    """Serve the contribute page"""
    return TemplateResponse(request, 'help_contribute.html',
                            {'title': _('Contribute')})


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


def manual(request, lang=None, page=None):
    """Serve the manual page from the 'doc' directory"""
    if not lang or lang == '-':
        kwargs = {'lang': get_language_from_request(request)}
        if page:
            return HttpResponseRedirect(
                reverse('help:manual-page', kwargs=dict(kwargs, page=page)))

        return HttpResponseRedirect(reverse('help:manual', kwargs=kwargs))

    def read_file(lang, file_name):
        """Read the page from disk and return contents or None."""
        page_file = pathlib.Path(cfg.doc_dir) / 'manual' / lang / file_name
        return page_file.read_text() if page_file.exists() else None

    page = page or 'freedombox-manual'
    content = read_file(lang, f'{page}.part.html')
    if not content:
        if lang != 'en':
            return HttpResponseRedirect(
                reverse('help:manual-page', kwargs=dict(lang='en', page=page)))

        raise Http404

    return TemplateResponse(
        request, 'help_manual.html', {
            'title': _('{box_name} Manual').format(box_name=_(cfg.box_name)),
            'content': content
        })


def download_manual(request):
    """Serve the PDF version of the manual from the 'doc' directory"""
    language_code = get_language_from_request(request)

    def get_manual_file_name(language_code):
        for file_name in ['freedombox-manual.pdf.gz', 'freedombox-manual.pdf']:
            name = os.path.join(cfg.doc_dir, 'manual', language_code,
                                file_name)
            if os.path.isfile(name):
                return name

        return None

    manual_file_name = get_manual_file_name(
        language_code) or get_manual_file_name('en')

    if not manual_file_name:
        raise Http404

    (content_type, encoding) = mimetypes.guess_type(manual_file_name)

    with open(manual_file_name, 'rb') as file_handle:
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
