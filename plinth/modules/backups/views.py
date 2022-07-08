# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the backups app.
"""

import logging
import os
import tempfile
from datetime import datetime
from urllib.parse import unquote

import paramiko
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import FormView, TemplateView, View

from plinth.errors import PlinthError
from plinth.modules import backups, storage

from . import (SESSION_PATH_VARIABLE, api, forms, get_known_hosts_path,
               is_ssh_hostkey_verified)
from .decorators import delete_tmp_backup_file
from .repository import (BorgRepository, SshBorgRepository, get_instance,
                         get_repositories)

logger = logging.getLogger(__name__)


@method_decorator(delete_tmp_backup_file, name='dispatch')
class IndexView(TemplateView):
    """View to show list of archives."""
    template_name = 'backups.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['app_info'] = backups.app.info
        context['repositories'] = [
            repository.get_view_content() for repository in get_repositories()
        ]
        return context


class ScheduleView(SuccessMessageMixin, FormView):
    form_class = forms.ScheduleForm
    prefix = 'backups_schedule'
    template_name = 'backups_schedule.html'
    success_url = reverse_lazy('backups:index')
    success_message = gettext_lazy('Backup schedule updated.')

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        schedule = get_instance(self.kwargs['uuid']).schedule
        initial.update({
            'enabled': schedule.enabled,
            'daily_to_keep': schedule.daily_to_keep,
            'weekly_to_keep': schedule.weekly_to_keep,
            'monthly_to_keep': schedule.monthly_to_keep,
            'run_at_hour': schedule.run_at_hour,
            'unselected_apps': schedule.unselected_apps,
        })
        return initial

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Schedule Backups')
        return context

    def form_valid(self, form):
        """Update backup schedule."""
        repository = get_instance(self.kwargs['uuid'])
        schedule = repository.schedule
        data = form.cleaned_data
        schedule.enabled = data['enabled']
        schedule.daily_to_keep = data['daily_to_keep']
        schedule.weekly_to_keep = data['weekly_to_keep']
        schedule.monthly_to_keep = data['monthly_to_keep']
        schedule.run_at_hour = data['run_at_hour']

        components = api.get_all_components_for_backup()
        unselected_apps = [
            component.app_id for component in components
            if component.app_id not in data['selected_apps']
        ]
        schedule.unselected_apps = unselected_apps

        repository.save()
        backups.on_schedule_save(repository)
        return super().form_valid(form)


class CreateArchiveView(SuccessMessageMixin, FormView):
    """View to create a new archive."""
    form_class = forms.CreateArchiveForm
    prefix = 'backups'
    template_name = 'backups_form.html'
    success_url = reverse_lazy('backups:index')
    success_message = gettext_lazy('Archive created.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create a new backup')
        return context

    def form_valid(self, form):
        """Create the archive on valid form submission."""
        repository = get_instance(form.cleaned_data['repository'])
        if repository.flags.get('mountable'):
            repository.mount()

        name = form.cleaned_data['name'] or datetime.now().strftime(
            '%Y-%m-%d:%H:%M')
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
        repository = get_instance(self.kwargs['uuid'])
        context['archive'] = repository.get_archive(self.kwargs['name'])
        if context['archive'] is None:
            raise Http404

        return context

    def post(self, request, uuid, name):
        """Delete the archive."""
        repository = get_instance(uuid)
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
            mount_info = storage.get_mount_info('/')
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
                mount_info['free_bytes'] / 2)

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
    success_message = gettext_lazy('Restored files from backup.')

    def get_form_kwargs(self):
        """Pass additional keyword args for instantiating the form."""
        kwargs = super().get_form_kwargs()
        included_apps = self._get_included_apps()
        kwargs['components'] = api.get_components_in_order(included_apps)
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
        repository = get_instance(uuid)
        return repository.get_archive_apps(name)

    def form_valid(self, form):
        """Restore files from the archive on valid form submission."""
        repository = get_instance(self.kwargs['uuid'])
        selected_apps = form.cleaned_data['selected_apps']
        repository.restore_archive(self.kwargs['name'], selected_apps)
        return super().form_valid(form)


class DownloadArchiveView(View):
    """View to export and download an archive as stream."""

    def get(self, request, uuid, name):
        repository = get_instance(uuid)
        filename = f'{name}.tar.gz'

        response = StreamingHttpResponse(repository.get_download_stream(name),
                                         content_type='application/gzip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            filename
        return response


class AddRepositoryView(SuccessMessageMixin, FormView):
    """View to create a new backup repository."""
    form_class = forms.AddRepositoryForm
    template_name = 'backups_add_repository.html'
    success_url = reverse_lazy('backups:index')

    def get(self, request, *args, **kwargs):
        """If there are no disks available for adding, throw error."""
        if not forms.get_disk_choices():
            messages.error(
                request,
                _('No additional disks available to add a repository.'))
            return redirect(reverse_lazy('backups:index'))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create backup repository')
        return context

    def form_valid(self, form):
        """Create and save a Borg repository."""
        path = os.path.join(form.cleaned_data.get('disk'), 'FreedomBoxBackups')
        encryption = form.cleaned_data.get('encryption')
        encryption_passphrase = form.cleaned_data.get('encryption_passphrase')
        if encryption == 'none':
            encryption_passphrase = None

        credentials = {'encryption_passphrase': encryption_passphrase}
        repository = BorgRepository(path, credentials)
        if _save_repository(self.request, repository):
            return super().form_valid(form)

        return redirect(reverse_lazy('backups:add-repository'))


class AddRemoteRepositoryView(SuccessMessageMixin, FormView):
    """View to create a new remote backup repository."""
    form_class = forms.AddRemoteRepositoryForm
    template_name = 'backups_add_remote_repository.html'

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
        repository = SshBorgRepository(path, credentials)
        repository.verfied = False
        repository.save()
        messages.success(self.request, _('Added new remote SSH repository.'))

        url = reverse('backups:verify-ssh-hostkey', args=[repository.uuid])
        return redirect(url)


class VerifySshHostkeyView(SuccessMessageMixin, FormView):
    """View to verify SSH Hostkey of the remote repository."""
    form_class = forms.VerifySshHostkeyForm
    template_name = 'verify_ssh_hostkey.html'
    success_url = reverse_lazy('backups:index')
    repository = None

    def get_form_kwargs(self):
        """Pass additional keyword args for instantiating the form."""
        kwargs = super().get_form_kwargs()
        kwargs['hostname'] = self._get_repository().hostname
        return kwargs

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Verify SSH hostkey')
        context['hostname'] = self._get_repository().hostname
        return context

    def _get_repository(self):
        """Fetch the repository data from DB only once."""
        if not self.repository:
            self.repository = get_instance(self.kwargs['uuid'])

        return self.repository

    @staticmethod
    def _add_ssh_hostkey(ssh_public_key):
        """Add the given SSH key to known_hosts."""
        known_hosts_path = get_known_hosts_path()
        known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
        known_hosts_path.touch()

        with known_hosts_path.open('a', encoding='utf-8') as known_hosts_file:
            known_hosts_file.write(ssh_public_key + '\n')

    def get(self, *args, **kwargs):
        """Skip this view if host is already verified."""
        if not is_ssh_hostkey_verified(self._get_repository().hostname):
            return super().get(*args, **kwargs)

        messages.success(self.request, _('SSH host already verified.'))
        if _save_repository(self.request, self._get_repository()):
            return redirect(reverse_lazy('backups:index'))

        return redirect(reverse_lazy('backups:add-remote-repository'))

    def form_valid(self, form):
        """Create and store the repository."""
        ssh_public_key = form.cleaned_data['ssh_public_key']
        self._add_ssh_hostkey(ssh_public_key)
        messages.success(self.request, _('SSH host verified.'))
        if _save_repository(self.request, self._get_repository()):
            return redirect(reverse_lazy('backups:index'))

        return redirect(reverse_lazy('backups:add-remote-repository'))


def _save_repository(request, repository):
    """Initialize and save a repository. Convert errors to messages."""
    try:
        repository.initialize()
        repository.verified = True
        repository.save()
        return True
    except paramiko.BadHostKeyException:
        message = _('SSH host public key could not be verified.')
    except paramiko.AuthenticationException:
        message = _('Authentication to remote server failed.')
    except paramiko.SSHException as exception:
        message = _('Error establishing connection to server: {}').format(
            str(exception))
    except Exception as exception:
        message = str(exception)
        logger.exception('Error adding repository: %s', exception)

    messages.error(request, message)
    # Remove the repository so that the user can have another go at
    # creating it.
    try:
        repository.remove()
        messages.error(request, _('Repository removed.'))
    except KeyError:
        pass

    return False


class RemoveRepositoryView(SuccessMessageMixin, TemplateView):
    """View to delete a repository."""
    template_name = 'backups_repository_remove.html'

    def get_context_data(self, uuid, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Remove Repository')
        context['repository'] = get_instance(uuid)
        return context

    def post(self, request, uuid):
        """Delete the repository on confirmation."""
        repository = get_instance(uuid)
        repository.remove()
        messages.success(request,
                         _('Repository removed. Backups were not deleted.'))

        return redirect('backups:index')


def umount_repository(request, uuid):
    """View to unmount a remote SSH repository."""
    repository = SshBorgRepository.load(uuid)
    repository.umount()
    if repository.is_mounted:
        messages.error(request, _('Unmounting failed!'))

    return redirect('backups:index')


def mount_repository(request, uuid):
    """View to mount a remote SSH repository."""
    # Do not mount unverified ssh repositories. Prompt for verification.
    if not get_instance(uuid).is_usable():
        return redirect('backups:verify-ssh-hostkey', uuid=uuid)

    repository = SshBorgRepository.load(uuid)
    try:
        repository.mount()
    except Exception as err:
        msg = "%s: %s" % (_('Mounting failed'), str(err))
        messages.error(request, msg)
    else:
        if not repository.is_mounted:
            messages.error(request, _('Mounting failed'))

    return redirect('backups:index')
