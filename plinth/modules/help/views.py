# SPDX-License-Identifier: AGPL-3.0-or-later
"""Help app for FreedomBox."""

import gzip
import json
import mimetypes
import os
import pathlib

import apt
import requests
from django.core.files.base import File
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import get_language_from_request
from django.utils.translation import gettext as _

from plinth import __version__, cfg, menu
from plinth.modules.upgrades import views as upgrades_views


def index(request):
    """Serve the index page"""
    menu_items = menu.main_menu.active_item(request).sorted_items()
    return TemplateResponse(request, 'help_index.html', {
        'title': _('Documentation and FAQ'),
        'menu_items': menu_items
    })


def contribute(request):
    """Serve the contribute page"""
    response = requests.get('https://udd.debian.org/how-can-i-help.json.gz')
    data = gzip.decompress(response.content)
    issues = json.loads(data)

    # Split issues according to type and filter for installed packages.
    testing_autorm = []
    no_testing = []
    gift = []
    help_needed = []
    cache = apt.Cache()
    for issue in issues:
        if issue['type'] == 'testing-autorm':
            for package in issue['packages']:
                try:
                    if cache[package].is_installed:
                        testing_autorm.append(issue)
                        break
                except KeyError:
                    pass
        elif issue['type'] == 'no-testing':
            try:
                if cache[issue['package']].is_installed:
                    no_testing.append(issue)
            except KeyError:
                pass
        elif issue['type'] == 'gift':
            try:
                if cache[issue['package']].is_installed:
                    gift.append(issue)
            except KeyError:
                pass
        elif issue['type'] == 'help':
            try:
                if cache[issue['package']].is_installed:
                    help_needed.append(issue)
            except KeyError:
                pass

    return TemplateResponse(
        request, 'help_contribute.html', {
            'title': _('Contribute'),
            'testing_autorm': testing_autorm,
            'no_testing': no_testing,
            'gift': gift,
            'help': help_needed,
        })


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
    context = {'title': _('About {box_name}').format(box_name=_(cfg.box_name))}
    if request.user.is_authenticated:
        context.update({
            'version': __version__,
            'new_version': upgrades_views.is_newer_version_available(),
            'os_release': upgrades_views.get_os_release()
        })

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
