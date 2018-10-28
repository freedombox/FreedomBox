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

import gzip
import mimetypes
from datetime import datetime
import os
from io import BytesIO
import time
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, FileResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import View, FormView, TemplateView

from plinth.modules import backups
from plinth import actions

from . import api, forms, SESSION_BACKUP_VARIABLE, delete_upload_backup_file

# number of seconds an uploaded backup file should be kept/stored
KEEP_UPLOADED_BACKUP_FOR = 60*10

subsubmenu = [{
    'url': reverse_lazy('backups:index'),
    'text': ugettext_lazy('Backups')
}, {
    'url': reverse_lazy('backups:upload'),
    'text': ugettext_lazy('Upload backup')
}, {
    'url': reverse_lazy('backups:create'),
    'text': ugettext_lazy('Create backup')
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


def _get_file_response(path, filename):
    """Read and return a downloadable file"""
    (content_type, encoding) = mimetypes.guess_type(filename)
    response = FileResponse(open(path, 'rb'), content_type=content_type)
    content_disposition = 'attachment; filename="%s"' % filename
    response['Content-Disposition'] = content_disposition
    return response


class create_temporary_backup_file:
    """Create a temporary backup file that gets deleted after using it"""
    # TODO: try using export-tar with FILE parameter '-' and reading stdout:
    # https://borgbackup.readthedocs.io/en/stable/usage/tar.html

    def __init__(self, name):
        self.name = name
        self.path = UPLOAD_BACKUP_PATH

    def __enter__(self):
        backups.export_archive(self.name, self.path)
        return self.path

    def __exit__(self, type, value, traceback):
        delete_upload_backup_file(self.path)


class UploadArchiveView(SuccessMessageMixin, FormView):
    form_class = forms.UploadForm
    prefix = 'backups'
    template_name = 'backups_upload.html'
    success_url = reverse_lazy('backups:restore-from-upload')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload and restore a backup file')
        context['subsubmenu'] = subsubmenu
        return context

    def form_valid(self, form):
        """store uploaded file."""
        with open(UPLOAD_BACKUP_PATH, 'wb+') as destination:
            for chunk in self.request.FILES['backups-file'].chunks():
                destination.write(chunk)
        self.request.session[SESSION_BACKUP_VARIABLE] = time.time() + \
                KEEP_UPLOADED_BACKUP_FOR
        return super().form_valid(form)


class BaseRestoreView(SuccessMessageMixin, FormView):
    """View to restore files from an archive."""
    form_class = forms.RestoreForm
    prefix = 'backups'
    template_name = 'backups_restore.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Restored files from backup.')

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
        context['title'] = _('Restore')
        context['name'] = self.kwargs.get('name', None)
        return context


class RestoreFromUploadView(BaseRestoreView):
    """View to restore files from an (uploaded) exported archive."""

    def get(self, *args, **kwargs):
        if not os.path.isfile(UPLOAD_BACKUP_PATH):
            messages.error(self.request, _('No backup file found.'))
            return redirect(reverse_lazy('backups:index'))
        else:
            return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Restore from uploaded file')
        return context

    def _get_included_apps(self):
        """Save some data used to instantiate the form."""
        return backups.get_exported_archive_apps(UPLOAD_BACKUP_PATH)

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        backups.restore_from_upload(form.cleaned_data['selected_apps'])
        return super().form_valid(form)


class RestoreArchiveView(BaseRestoreView):
    """View to restore files from an archive."""

    def _get_included_apps(self):
        """Save some data used to instantiate the form."""
        name = unquote(self.kwargs['name'])
        archive_path = backups.get_archive_path(name)
        return backups.get_archive_apps(archive_path)

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        archive_path = backups.get_archive_path(self.kwargs['name'])
        backups.restore(archive_path, form.cleaned_data['selected_apps'])
        return super().form_valid(form)


class ZipStream(object):
    """Zip a stream that yields binary data"""

    def __init__(self, stream, get_chunk_method):
        """
        - stream: the input stream
        - get_chunk_method: name of the method that yields chunks
        """
        self.stream = stream
        self.buffer = BytesIO()
        self.zipfile = gzip.GzipFile(mode='wb', fileobj=self.buffer)
        self.get_chunk = getattr(self.stream, get_chunk_method)

    def __next__(self):
        line = self.get_chunk()
        if not len(line):
            raise StopIteration
        self.zipfile.write(line)
        self.zipfile.flush()
        zipped = self.buffer.getvalue()
        self.buffer.truncate(0)
        self.buffer.seek(0)
        return zipped

    def __iter__(self):
        return self


class ExportAndDownloadView(View):
    """View to export and download an archive as stream."""
    def get(self, request, name):
        name = unquote(name)
        filename = "%s.tar.gz" % name
        args = ['export-stream', '--name', name]
        proc = actions.superuser_run('backups', args, run_in_background=True,
                bufsize=1)
        zipStream = ZipStream(proc.stdout, 'readline')
        response = StreamingHttpResponse(zipStream,
                content_type="application/x-gzip")
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response
