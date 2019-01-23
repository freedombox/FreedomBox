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

from plinth.errors import PlinthError
from plinth.modules import backups, storage

from . import api, forms, SESSION_PATH_VARIABLE, ROOT_REPOSITORY
from .repository import BorgRepository, SshBorgRepository, get_repository, \
        get_ssh_repositories
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

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = backups.name
        context['description'] = backups.description
        root_repository = BorgRepository(ROOT_REPOSITORY)
        context['root_repository'] = root_repository.get_view_content()
        context['ssh_repositories'] = get_ssh_repositories()
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

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        repository = get_repository(form.cleaned_data['repository'],
                                    automount=True)
        name = datetime.now().strftime('%Y-%m-%d:%H:%M')
        repository.create_archive(name, form.cleaned_data['selected_apps'])
        return super().form_valid(form)


class DeleteArchiveView(SuccessMessageMixin, TemplateView):
    """View to delete an archive."""
    template_name = 'backups_delete.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Archive')
        repository = get_repository(self.kwargs['uuid'])
        context['archive'] = repository.get_archive(self.kwargs['name'])
        if context['archive'] is None:
            raise Http404

        return context

    def post(self, request, uuid, name):
        """Delete the archive."""
        repository = get_repository(uuid)
        repository.delete_archive(name)
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
            disk_info = storage.get_disk_info('/')
        except PlinthError as exception:
            logger.exception(
                'Error getting information about root partition: %s',
                exception)
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
        kwargs['apps'] = api.get_apps_in_order(included_apps)
        return kwargs

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Restore')
        context['name'] = self.kwargs.get('name', None)
        context['uuid'] = self.kwargs.get('uuid', None)
        return context


class RestoreFromUploadView(BaseRestoreView):
    """View to restore files from an (uploaded) exported archive."""

    def get(self, *args, **kwargs):
        path = self.request.session.get(SESSION_PATH_VARIABLE)
        if not os.path.isfile(path):
            messages.error(self.request, _('No backup file found.'))
            return redirect(reverse_lazy('backups:index'))

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
        uuid = self.kwargs['uuid']
        repository = get_repository(uuid)
        return repository.get_archive_apps(name)

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        repository = get_repository(self.kwargs['uuid'])
        repository.restore_archive(self.kwargs['name'],
                                   form.cleaned_data['selected_apps'])
        return super().form_valid(form)


class DownloadArchiveView(View):
    """View to export and download an archive as stream."""
    def get(self, request, uuid, name):
        repository = get_repository(uuid)
        filename = "%s.tar.gz" % name

        response = StreamingHttpResponse(repository.get_zipstream(name),
                                         content_type="application/x-gzip")
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            filename
        return response


class AddRepositoryView(SuccessMessageMixin, FormView):
    """View to create a new remote backup repository."""
    form_class = forms.AddRepositoryForm
    prefix = 'backups'
    template_name = 'backups_repository_add.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Added new repository.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create remote backup repository')
        context['subsubmenu'] = subsubmenu
        return context

    def form_valid(self, form):
        """Create and store the repository."""
        try:
            form.repository.get_info()
        except BorgRepositoryDoesNotExistError:
            form.repository.create_repository(form.cleaned_data['encryption'])
        form.repository.save(store_credentials=True)
        return super().form_valid(form)


class RemoveRepositoryView(SuccessMessageMixin, TemplateView):
    """View to delete a repository."""
    template_name = 'backups_repository_remove.html'

    def get_context_data(self, uuid, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Remove Repository')
        context['repository'] = SshBorgRepository(uuid=uuid, automount=False)
        return context

    def post(self, request, uuid):
        """Delete the archive."""
        repository = SshBorgRepository(uuid, automount=False)
        repository.remove_repository()
        messages.success(request, _('Repository removed. The remote backup '
                                    'itself was not deleted.'))
        return redirect('backups:index')


def umount_repository(request, uuid):
    repository = SshBorgRepository(uuid=uuid)
    repository.umount()
    if repository.is_mounted:
        messages.error(request, _('Unmounting failed!'))
    return redirect('backups:index')


def mount_repository(request, uuid):
    repository = SshBorgRepository(uuid=uuid, automount=False)
    try:
        repository.mount()
    except Exception as err:
        msg = "%s: %s" % (_('Mounting failed'), str(err))
        messages.error(request, msg)
    else:
        if not repository.is_mounted:
            messages.error(request, _('Mounting failed'))
    return redirect('backups:index')
