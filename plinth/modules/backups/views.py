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
Views for the backups app.
"""

import mimetypes
from datetime import datetime
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, FileResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import View, FormView, TemplateView

from plinth.modules import backups

from . import api, find_exported_archive, forms


subsubmenu = [{
    'url': reverse_lazy('backups:index'),
    'text': ugettext_lazy('Backups')
}, {
    'url': reverse_lazy('backups:upload'),
    'text': ugettext_lazy('Upload backup')
}]


class IndexView(TemplateView):
    """View to show list of archives."""
    template_name = 'backups.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = backups.name
        context['description'] = backups.description
        context['info'] = backups.get_info()
        context['archives'] = backups.list_archives()
        context['exports'] = backups.get_export_files()
        context['subsubmenu'] = subsubmenu
        apps = api.get_all_apps_for_backup()
        context['available_apps'] = [app.name for app in apps]
        return context


class CreateArchiveView(SuccessMessageMixin, FormView):
    """View to create a new archive."""
    form_class = forms.CreateArchiveForm
    prefix = 'backups'
    template_name = 'backups_form.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Archive created.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('New Backup')
        context['subsubmenu'] = subsubmenu
        return context

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = super().get_initial()
        initial['name'] = 'FreedomBox_backup_' + datetime.now().strftime(
            '%Y-%m-%d:%H:%M')
        return initial

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        backups.create_archive(form.cleaned_data['name'],
                               form.cleaned_data['selected_apps'])
        return super().form_valid(form)


class DeleteArchiveView(SuccessMessageMixin, TemplateView):
    """View to delete an archive."""
    template_name = 'backups_delete.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Archive')
        context['archive'] = backups.get_archive(self.kwargs['name'])
        if context['archive'] is None:
            raise Http404

        return context

    def post(self, request, name):
        """Delete the archive."""
        backups.delete_archive(name)
        messages.success(request, _('Archive deleted.'))
        return redirect(reverse_lazy('backups:index'))


class DownloadArchiveView(View):
    """View to download an archive."""
    def get(self, request, device, name):
        device = unquote(device)
        name = unquote(name)
        filepath = find_exported_archive(device, name)
        return _get_file_response(filepath, name)


def _get_file_response(path, filename):
    """Read and return a downloadable file"""
    (content_type, encoding) = mimetypes.guess_type(filename)
    response = FileResponse(open(path, 'rb'), content_type=content_type)
    content_disposition = 'attachment; filename="%s"' % filename
    response['Content-Disposition'] = content_disposition
    return response


class UploadArchiveView(SuccessMessageMixin, FormView):
    form_class = forms.UploadForm
    prefix = 'backups'
    template_name = 'backups_upload.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Backup file uploaded.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload Backup File')
        context['subsubmenu'] = subsubmenu
        return context

    def form_valid(self, form):
        """store uploaded file."""
        with open(form.cleaned_data['filepath'], 'wb+') as destination:
            for chunk in self.request.FILES['backups-file'].chunks():
                destination.write(chunk)
        return super().form_valid(form)


class ExportArchiveView(SuccessMessageMixin, FormView):
    """View to export an archive."""
    form_class = forms.ExportArchiveForm
    prefix = 'backups'
    template_name = 'backups_form.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Archive exported.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Export Archive')
        context['archive'] = backups.get_archive(self.kwargs['name'])
        if context['archive'] is None:
            raise Http404

        return context

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        backups.export_archive(self.kwargs['name'], form.cleaned_data['disk'])
        return super().form_valid(form)


class RestoreView(SuccessMessageMixin, FormView):
    """View to restore files from an exported archive."""
    form_class = forms.RestoreForm
    prefix = 'backups'
    template_name = 'backups_restore.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Restored files from backup.')

    def _get_included_apps(self):
        """Save some data used to instantiate the form."""
        device = unquote(self.kwargs['device'])
        name = unquote(self.kwargs['name'])
        filename = backups.find_exported_archive(device, name)
        return backups.get_export_apps(filename)

    def get_form_kwargs(self):
        """Pass additional keyword args for instantiating the form."""
        kwargs = super().get_form_kwargs()
        included_apps = self._get_included_apps()
        installed_apps = api.get_all_apps_for_backup()
        kwargs['apps'] = [
            app for app in installed_apps if app.name in included_apps
        ]
        return kwargs

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Restore from backup')
        context['device'] = unquote(self.kwargs['device'])
        context['name'] = self.kwargs['name']
        return context

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        backups.restore_exported(
            unquote(self.kwargs['device']), self.kwargs['name'],
            form.cleaned_data['selected_apps'])
        return super().form_valid(form)
