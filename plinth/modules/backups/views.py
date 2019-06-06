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

import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import unquote

import paramiko
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import ValidationError
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import FormView, TemplateView, View
from paramiko.hostkeys import HostKeys

from plinth import cfg
from plinth.errors import PlinthError
from plinth.modules import backups, storage

from . import (ROOT_REPOSITORY, SESSION_PATH_VARIABLE, api, forms,
               network_storage)
from .decorators import delete_tmp_backup_file
from .errors import BorgRepositoryDoesNotExistError
from .repository import (BorgRepository, SshBorgRepository, get_repository,
                         get_ssh_repositories)

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
        context['subsubmenu'] = subsubmenu
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
        context['title'] = backups.name
        context['description'] = backups.description
        context['subsubmenu'] = subsubmenu
        context['manual_page'] = backups.manual_page
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


class UploadArchiveView(SuccessMessageMixin, FormView):
    form_class = forms.UploadForm
    prefix = 'backups'
    template_name = 'backups_upload.html'
    success_url = reverse_lazy('backups:restore-from-upload')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = backups.name
        context['description'] = backups.description
        context['subsubmenu'] = subsubmenu
        context['manual_page'] = backups.manual_page
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
        filename = '%s.tar.gz' % name

        response = StreamingHttpResponse(
            repository.get_download_stream(name),
            content_type='application/gzip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            filename
        return response


class AddRepositoryView(SuccessMessageMixin, FormView):
    """View to verify the SSH Hostkey of the server and save the
    new SSH repository."""
    form_class = forms.AddRepositoryForm
    template_name = 'backups_repository_add.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Added new remote ssh repository.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create remote backup repository')
        context['subsubmenu'] = subsubmenu
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        repository = None
        if form.is_valid():
            path = form.cleaned_data.get("repository")
            _, hostname, _ = re.split('[@:]', path)
            credentials = _get_credentials(form.cleaned_data)
            if not self._is_ssh_hostkey_verified(hostname):
                repository = SshBorgRepository(path=path,
                                               credentials=credentials)
                repository.save(verified=False)
                uuid = repository.uuid
                url = reverse('backups:verify-ssh-hostkey', args=[uuid])
                return redirect(url)
            else:
                try:
                    repository = _validate_remote_repository(path, credentials)
                except ValidationError as err:
                    messages.error(request, err.message)
                    context_data = self.get_context_data()
                    context_data['form'] = form
                    return render(request, self.template_name, context_data)
                try:
                    repository.get_info()
                except BorgRepositoryDoesNotExistError:
                    repository.create_repository(
                        form.cleaned_data['encryption'])
                repository.save()
                return redirect(self.success_url)
        else:
            context_data = self.get_context_data()
            context_data['form'] = form
            return render(request, self.template_name, context_data)

    def _is_ssh_hostkey_verified(self, hostname):
        """Check whether SSH Hostkey has already been verified.
        hostname: Domain name or IP address of the host
        """
        KNOWN_HOSTS = os.path.join(cfg.data_dir, '.ssh', 'known_hosts')
        if os.path.exists(KNOWN_HOSTS):
            known_hosts = HostKeys(KNOWN_HOSTS)
            host_keys = known_hosts.lookup(hostname)
            return host_keys is not None
        else:
            return False


class VerifySshHostkeyView(SuccessMessageMixin, FormView):
    """View to verify SSH Hostkey of the remote repository."""
    form_class = forms.VerifySshHostkeyForm
    template_name = 'verify_ssh_hostkey.html'
    success_url = reverse_lazy('backups:index')
    success_message = _('Added new remote ssh repository.')
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
        context['subsubmenu'] = subsubmenu
        context['hostname'] = self._get_hostname()
        return context

    def _get_repo_data(self):
        """Fetch the repository data from DB only once."""
        if not self.repo_data:
            uuid = self.kwargs['uuid']
            self.repo_data = network_storage.get(uuid)
        return self.repo_data

    def _get_hostname(self):
        _, hostname, _ = re.split('[@:]', self._get_repo_data()['path'])
        return hostname

    def _add_ssh_hostkey(self, hostname, key_type):
        """Add the given SSH key to known_hosts."""
        KNOWN_HOSTS = os.path.join(cfg.data_dir, '.ssh', 'known_hosts')
        if not os.path.exists(KNOWN_HOSTS):
            os.makedirs(KNOWN_HOSTS.rsplit('/', maxsplit=1)[0])
            open(KNOWN_HOSTS, 'w').close()
        with open(KNOWN_HOSTS, 'a') as known_hosts_file:
            key_line = subprocess.run(
                ['ssh-keyscan', '-t', key_type, hostname],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                check=True).stdout.decode().strip()
            known_hosts_file.write('\n')
            known_hosts_file.write(key_line)

    def form_valid(self, form):
        """Create and store the repository."""
        key_type = form.cleaned_data['ssh_public_key']
        self._add_ssh_hostkey(self._get_hostname(), key_type)
        repo_data = self._get_repo_data()
        path = repo_data.get("path")
        credentials = repo_data['credentials']
        uuid = self.kwargs['uuid']
        try:
            repository = _validate_remote_repository(path, credentials,
                                                     uuid=uuid)
        except ValidationError as err:
            messages.error(self.request, err.message)
            network_storage.delete(uuid)
            return redirect(reverse_lazy('backups:repository-add'))
        try:
            repository.get_info()
        except BorgRepositoryDoesNotExistError:
            repository.create_repository(repo_data.get('encryption', 'none'))
        repository.save()
        return super().form_valid(form)


def _get_credentials(data):
    credentials = {}
    for field_name in ["ssh_password", "encryption_passphrase"]:
        field_value = data.get(field_name, None)
        if field_value:
            credentials[field_name] = field_value

    return credentials


def _validate_remote_repository(path, credentials, uuid=None):
    """
    Validation of SSH remote

      * Create empty directory if not exists
      * Check if the directory is empty
        - if not empty, check if it's an existing backup repository
        - else throw an error
    """
    KNOWN_HOSTS = os.path.join(cfg.data_dir, '.ssh', 'known_hosts')
    username, hostname, dir_path = re.split('[@:]', path)
    dir_path = dir_path.replace('~', f'/home/{username}')
    password = credentials['ssh_password']
    ssh_client = paramiko.SSHClient()
    ssh_client.load_host_keys(KNOWN_HOSTS)
    repository = None
    try:
        ssh_client.connect(hostname, username=username, password=password)
    except Exception as err:
        msg = _('Accessing the remote repository failed. Details: %(err)s')
        raise ValidationError(msg, params={'err': str(err)})
    else:
        sftp_client = ssh_client.open_sftp()
        try:
            dir_contents = sftp_client.listdir(dir_path)
        except FileNotFoundError:
            logger.info(_(f"Directory {dir_path} doesn't exist. Creating ..."))
            sftp_client.mkdir(dir_path)
            repository = SshBorgRepository(uuid=uuid, path=path,
                                           credentials=credentials)
        else:
            if dir_contents:
                try:
                    repository = SshBorgRepository(uuid=uuid, path=path,
                                                   credentials=credentials)
                    repository.get_info()
                except BorgRepositoryDoesNotExistError:
                    msg = _(f'Directory {dir_path} is neither empty nor '
                            'is an existing backups repository.')
                    raise ValidationError(msg)
            else:
                repository = SshBorgRepository(uuid=uuid, path=path,
                                               credentials=credentials)
        finally:
            sftp_client.close()
    finally:
        ssh_client.close()

    return repository


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
        messages.success(
            request,
            _('Repository removed. The remote backup itself was not deleted.'))
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
