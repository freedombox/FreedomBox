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

import logging
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import unquote

import paramiko
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import FormView, TemplateView, View

from plinth.errors import PlinthError
from plinth.modules import backups, storage

from . import (ROOT_REPOSITORY, SESSION_PATH_VARIABLE, api, forms,
               get_known_hosts_path, is_ssh_hostkey_verified, network_storage,
               split_path)
from .decorators import delete_tmp_backup_file
from .errors import BorgRepositoryDoesNotExistError
from .repository import (BorgRepository, SshBorgRepository, get_repository,
                         get_ssh_repositories)

logger = logging.getLogger(__name__)


@method_decorator(delete_tmp_backup_file, name='dispatch')
class IndexView(TemplateView):
    """View to show list of archives."""
    template_name = 'backups.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = backups.name
        context['description'] = backups.description
        context['manual_page'] = backups.manual_page
        root_repository = BorgRepository(ROOT_REPOSITORY)
        context['root_repository'] = root_repository.get_view_content()
        context['ssh_repositories'] = get_ssh_repositories()
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
        context['title'] = _('Create a new backup')
        return context

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        repository = get_repository(form.cleaned_data['repository'])
        if hasattr(repository, 'mount'):
            repository.mount()

        name = datetime.now().strftime('%Y-%m-%d:%H:%M')
        selected_apps = form.cleaned_data['selected_apps']
        repository.create_archive(name, selected_apps)
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


class UploadArchiveView(SuccessMessageMixin, FormView):
    form_class = forms.UploadForm
    prefix = 'backups'
    template_name = 'backups_upload.html'
    success_url = reverse_lazy('backups:restore-from-upload')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload and restore a backup')
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
                disk_info['free_bytes'] / 2)

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

    def _get_included_apps(self):
        """To be overridden."""
        raise NotImplementedError


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
        selected_apps = form.cleaned_data['selected_apps']
        backups.restore_from_upload(path, selected_apps)
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
        selected_apps = form.cleaned_data['selected_apps']
        repository.restore_archive(self.kwargs['name'], selected_apps)
        return super().form_valid(form)


class DownloadArchiveView(View):
    """View to export and download an archive as stream."""

    def get(self, request, uuid, name):
        repository = get_repository(uuid)
        filename = '%s.tar.gz' % name

        response = StreamingHttpResponse(
            repository.get_download_stream(name),
            content_type='application/gzip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            filename
        return response


class AddRepositoryView(SuccessMessageMixin, FormView):
    """View to create a new remote backup repository."""
    form_class = forms.AddRepositoryForm
    template_name = 'backups_repository_add.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create remote backup repository')
        return context

    def form_valid(self, form):
        """Create and save Borg repository.

        Present the Host key verification form if necessary.
        """
        path = form.cleaned_data.get('repository')
        encryption_passphrase = form.cleaned_data.get('encryption_passphrase')
        if form.cleaned_data.get('encryption') == 'none':
            encryption_passphrase = None

        credentials = {
            'ssh_password': form.cleaned_data.get('ssh_password'),
            'encryption_passphrase': encryption_passphrase
        }
        repository = SshBorgRepository(path=path, credentials=credentials)
        repository.save(verified=False)
        messages.success(self.request, _('Added new remote SSH repository.'))

        url = reverse('backups:verify-ssh-hostkey', args=[repository.uuid])
        return redirect(url)


class VerifySshHostkeyView(SuccessMessageMixin, FormView):
    """View to verify SSH Hostkey of the remote repository."""
    form_class = forms.VerifySshHostkeyForm
    template_name = 'verify_ssh_hostkey.html'
    success_url = reverse_lazy('backups:index')
    repo_data = {}

    def get_form_kwargs(self):
        """Pass additional keyword args for instantiating the form."""
        kwargs = super().get_form_kwargs()
        hostname = self._get_hostname()
        kwargs['hostname'] = hostname
        return kwargs

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Verify SSH hostkey')
        context['hostname'] = self._get_hostname()
        return context

    def _get_repo_data(self):
        """Fetch the repository data from DB only once."""
        if not self.repo_data:
            uuid = self.kwargs['uuid']
            self.repo_data = network_storage.get(uuid)

        return self.repo_data

    def _get_hostname(self):
        """Get the hostname of the repository.

        Network interface information is stripped out.
        """
        _, hostname, _ = split_path(self._get_repo_data()['path'])
        return hostname.split('%')[0]  # XXX: Likely incorrect to split

    @staticmethod
    def _add_ssh_hostkey(ssh_public_key):
        """Add the given SSH key to known_hosts."""
        known_hosts_path = get_known_hosts_path()
        known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
        known_hosts_path.touch()

        with known_hosts_path.open('a') as known_hosts_file:
            known_hosts_file.write(ssh_public_key + '\n')

    def get(self, *args, **kwargs):
        """Skip this view if host is already verified."""
        if is_ssh_hostkey_verified(self._get_hostname()):
            messages.success(self.request, _('SSH host already verified.'))
            return self._add_remote_repository()

        return super().get(*args, **kwargs)

    def form_valid(self, form):
        """Create and store the repository."""
        ssh_public_key = form.cleaned_data['ssh_public_key']
        self._add_ssh_hostkey(ssh_public_key)
        messages.success(self.request, _('SSH host verified.'))
        return self._add_remote_repository()

    def _add_remote_repository(self):
        """On successful verification of host, add repository."""
        repo_data = self._get_repo_data()
        path = repo_data['path']
        credentials = repo_data['credentials']
        uuid = self.kwargs['uuid']
        encryption = 'none'
        if 'encryption_passphrase' in credentials and \
           credentials['encryption_passphrase']:
            encryption = 'repokey'

        try:
            dir_contents = _list_remote_directory(path, credentials)
            repository = SshBorgRepository(uuid=uuid, path=path,
                                           credentials=credentials)
            repository.mount()
            repository = _create_remote_repository(repository, encryption,
                                                   dir_contents)
            repository.save(verified=True)
            return redirect(reverse_lazy('backups:index'))
        except paramiko.BadHostKeyException:
            message = _('SSH host public key could not be verified.')
        except paramiko.AuthenticationException:
            message = _('Authentication to remote server failed.')
        except paramiko.SSHException as exception:
            message = _('Error establishing connection to server: {}').format(
                str(exception))
        except BorgRepositoryDoesNotExistError:
            message = _('Repository path is neither empty nor '
                        'is an existing backups repository.')
        except Exception as exception:
            message = str(exception)
            logger.exception('Error adding repository: %s', exception)

        messages.error(self.request, message)
        messages.error(self.request, _('Repository removed.'))
        # Delete the repository so that the user can have another go at
        # creating it.
        network_storage.delete(uuid)
        return redirect(reverse_lazy('backups:repository-add'))


def _list_remote_directory(path, credentials):
    """List a SSH remote directory. Create if it does not exist. """
    username, hostname, dir_path = split_path(path)
    if dir_path == '':
        dir_path = '.'

    if dir_path[0] == '~':
        dir_path = '.' + dir_path[1:]

    password = credentials['ssh_password']

    # Ensure remote directory exists, check contents
    dir_contents = None
    # TODO Test with IPv6 connection
    with _ssh_connection(hostname, username, password) as ssh_client:
        with ssh_client.open_sftp() as sftp_client:
            try:
                dir_contents = sftp_client.listdir(dir_path)
            except FileNotFoundError:
                logger.info('Directory %s does not exist, creating.', dir_path)
                sftp_client.mkdir(dir_path)

    return dir_contents


def _create_remote_repository(repository, encryption, dir_contents):
    """Create a Borg repository on remote server if necessary."""
    try:
        repository.get_info()
    except BorgRepositoryDoesNotExistError:
        if dir_contents:
            raise

        repository.create_repository(encryption)

    return repository


@contextmanager
def _ssh_connection(hostname, username, password):
    """Context manager to create and close an SSH connection."""
    ssh_client = paramiko.SSHClient()
    ssh_client.load_host_keys(str(get_known_hosts_path()))

    try:
        ssh_client.connect(hostname, username=username, password=password)
        yield ssh_client
    finally:
        ssh_client.close()


class RemoveRepositoryView(SuccessMessageMixin, TemplateView):
    """View to delete a repository."""
    template_name = 'backups_repository_remove.html'

    def get_context_data(self, uuid, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Remove Repository')
        context['repository'] = SshBorgRepository(uuid=uuid)
        return context

    def post(self, request, uuid):
        """Delete the archive."""
        repository = SshBorgRepository(uuid)
        repository.remove_repository()
        messages.success(
            request,
            _('Repository removed. The remote backup itself was not deleted.'))

        return redirect('backups:index')


def umount_repository(request, uuid):
    """View to unmount a remote SSH repository."""
    repository = SshBorgRepository(uuid=uuid)
    repository.umount()
    if repository.is_mounted:
        messages.error(request, _('Unmounting failed!'))

    return redirect('backups:index')


def mount_repository(request, uuid):
    """View to mount a remote SSH repository."""
    # Do not mount unverified ssh repositories. Prompt for verification.
    if not network_storage.get(uuid).get('verified'):
        return redirect('backups:verify-ssh-hostkey', uuid=uuid)

    repository = SshBorgRepository(uuid=uuid)
    try:
        repository.mount()
    except Exception as err:
        msg = "%s: %s" % (_('Mounting failed'), str(err))
        messages.error(request, msg)
    else:
        if not repository.is_mounted:
            messages.error(request, _('Mounting failed'))

    return redirect('backups:index')
