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

from datetime import datetime
import gzip
from io import BytesIO
import logging
import mimetypes
import os
import tempfile
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, FileResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import View, FormView, TemplateView

from plinth import actions
from plinth.errors import PlinthError, ActionError
from plinth.modules import backups, storage

from . import api, forms, SESSION_PATH_VARIABLE, REPOSITORY, remote_locations
from .decorators import delete_tmp_backup_file
from .errors import BorgRepositoryDoesNotExistError

logger = logging.getLogger(__name__)

subsubmenu = [{
    'url': reverse_lazy('backups:index'),
    'text': ugettext_lazy('Backups')
}, {
    'url': reverse_lazy('backups:upload'),
    'text': ugettext_lazy('Upload')
}, {
    'url': reverse_lazy('backups:create'),
    'text': ugettext_lazy('Create')
}]


@method_decorator(delete_tmp_backup_file, name='dispatch')
class IndexView(TemplateView):
    """View to show list of archives."""
    template_name = 'backups.html'

    def get_remote_archives(self):
        return {}  # uuid --> archive list

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = backups.name
        context['description'] = backups.description
        context['info'] = backups.get_info(REPOSITORY)
        context['root_location'] = backups.get_root_location_content()
        context['remote_locations'] = remote_locations.get_locations_content()
        context['subsubmenu'] = subsubmenu
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
        return redirect('backups:index')


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
    success_url = reverse_lazy('backups:restore-from-upload')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload and restore a backup file')
        context['subsubmenu'] = subsubmenu
        try:
            disk_info = storage.get_disk_info('/', self.request)
        except (PlinthError, PermissionError):
            logger.error('Error getting information about root partition.')
        else:
            # The maximum file size that can be uploaded and restored is at
            # most half of the available disk space:
            # - Django stores uploaded files that do not fit into memory to
            #   disk (/tmp/). These are only copied by form_valid() after
            #   the upload is finished.
            # - For restoring it's highly advisable to have at least as much
            #   free disk space as the file size.
            context['max_filesize'] = storage.format_bytes(
                    disk_info["free_bytes"] / 2)
        return context

    def form_valid(self, form):
        """store uploaded file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            self.request.session[SESSION_PATH_VARIABLE] = tmp_file.name
            for chunk in self.request.FILES['backups-file'].chunks():
                tmp_file.write(chunk)
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
        path = self.request.session.get(SESSION_PATH_VARIABLE)
        if not os.path.isfile(path):
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
        path = self.request.session.get(SESSION_PATH_VARIABLE)
        return backups.get_exported_archive_apps(path)

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        path = self.request.session.get(SESSION_PATH_VARIABLE)
        backups.restore_from_upload(path, form.cleaned_data['selected_apps'])
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
        - get_chunk_method: name of the method to get a chunk of the stream
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
    def get(self, request, uuid, name):
        # The uuid is 'root' for the root repository
        name = unquote(name)
        filename = "%s.tar.gz" % name
        args = ['export-tar', '--name', name]
        proc = actions.superuser_run('backups', args, run_in_background=True,
                                     bufsize=1)
        zipStream = ZipStream(proc.stdout, 'readline')
        response = StreamingHttpResponse(zipStream,
                                         content_type="application/x-gzip")
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            filename
        return response


class AddLocationView(SuccessMessageMixin, FormView):
    """View to create a new remote backup location."""
    form_class = forms.AddRepositoryForm
    prefix = 'backups'
    template_name = 'backups_add_location.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Added new location.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create remote backup repository')
        context['subsubmenu'] = subsubmenu
        return context

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        repository = form.cleaned_data['repository']
        encryption = form.cleaned_data['encryption']
        encryption_passphrase = form.cleaned_data['encryption_passphrase']
        ssh_password = form.cleaned_data['ssh_password']
        store_passwords = form.cleaned_data['store_passwords']
        # TODO: add ssh_keyfile
        # ssh_keyfile = form.cleaned_data['ssh_keyfile']

        access_params = {}
        if encryption_passphrase:
            access_params['encryption_passphrase'] = encryption_passphrase
        if ssh_password:
            access_params['ssh_password'] = ssh_password
        """
        if ssh_keyfile:
            access_params['ssh_keyfile'] = ssh_keyfile
        """
        remote_locations.add(repository, 'ssh', encryption, access_params,
                             store_passwords, 'backups')
        # Create the borg repository if it doesn't exist
        try:
            backups.test_connection(repository, access_params)
        except BorgRepositoryDoesNotExistError:
            backups.create_repository(repository, encryption,
                                      access_params=access_params)
        return super().form_valid(form)


class TestLocationView(TemplateView):
    """View to create a new repository."""
    template_name = 'backups_test_location.html'

    def post(self, request):
        # TODO: add support for borg encryption and ssh keyfile
        context = self.get_context_data()
        repository = request.POST['backups-repository']
        access_params = {
            'ssh_password': request.POST['backups-ssh_password'],
        }
        try:
            repo_info = backups.test_connection(repository, access_params)
            context["message"] = repo_info
        except ActionError as err:
            context["error"] = str(err)

        return self.render_to_response(context)


class RemoveLocationView(SuccessMessageMixin, TemplateView):
    """View to delete an archive."""
    template_name = 'backups_remove_repository.html'

    def get_context_data(self, uuid, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Remove Repository')
        context['location'] = remote_locations.get_location(uuid)
        return context

    def post(self, request, uuid):
        """Delete the archive."""
        remote_locations.delete(uuid)
        messages.success(request, _('Repository removed. The remote backup '
                                    'itself was not deleted.'))
        return redirect('backups:index')


def umount_location(request, uuid):
    remote_locations.umount_uuid(uuid)
    if remote_locations.uuid_is_mounted(uuid):
        messages.error(request, _('Unmounting failed!'))
    return redirect('backups:index')


def mount_location(request, uuid):
    try:
        remote_locations.mount_uuid(uuid)
    except Exception as err:
        msg = "%s: %s" % (_('Mounting failed'), str(err))
        messages.error(request, msg)
    else:
        if not remote_locations.uuid_is_mounted(uuid):
            messages.error(request, _('Mounting failed'))
    return redirect('backups:index')
