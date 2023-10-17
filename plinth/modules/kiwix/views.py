# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Kiwix module.
"""

import logging
import tempfile

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from plinth import app as app_module
from plinth import views
from plinth.errors import PlinthError
from plinth.modules import storage
from plinth.modules.kiwix import privileged

from . import forms

logger = logging.getLogger(__name__)


class KiwixAppView(views.AppView):
    """Serve configuration form."""

    app_id = 'kiwix'
    template_name = 'kiwix.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['packages'] = privileged.list_packages()
        return context


class AddPackageView(SuccessMessageMixin, FormView):
    """View to add content package in the form of ZIM files."""

    form_class = forms.AddPackageForm
    prefix = 'kiwix'
    template_name = 'kiwix-add-package.html'
    success_url = reverse_lazy('kiwix:index')
    success_message = _('Content package added.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add a new content package')

        # TODO The following is almost duplicated in backups/views.py
        try:
            mount_info = storage.get_mount_info('/')
        except PlinthError as exception:
            logger.exception(
                'Error getting information about root partition: %s',
                exception)
        else:
            context['max_filesize'] = storage.format_bytes(
                mount_info['free_bytes'])

        return context

    def form_valid(self, form):
        """Store the uploaded file."""
        multipart_file = self.request.FILES['kiwix-file']

        with tempfile.TemporaryDirectory() as temp_dir:
            zim_file_name = temp_dir + '/' + multipart_file.name
            with open(zim_file_name, 'wb+') as zim_file:
                for chunk in multipart_file.chunks():
                    zim_file.write(chunk)

            try:
                privileged.add_package(zim_file_name)
            except Exception:
                messages.error(self.request,
                               _('Failed to add content package.'))
                return redirect(reverse_lazy('kiwix:index'))

        return super().form_valid(form)


def delete_package(request, zim_id):
    """View to delete a library."""
    packages = privileged.list_packages()
    if zim_id not in packages:
        raise Http404

    name = packages[zim_id]['title']

    if request.method == 'POST':
        try:
            privileged.delete_package(zim_id)
            messages.success(request, _('{name} deleted.').format(name=name))
        except Exception as error:
            messages.error(
                request,
                _('Could not delete {name}: {error}').format(
                    name=name, error=error))
        return redirect(reverse_lazy('kiwix:index'))

    return TemplateResponse(request, 'kiwix-delete-package.html', {
        'title': app_module.App.get('kiwix').info.name,
        'name': name
    })
