# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Gitweb."""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView

from plinth import app as app_module
from plinth import views
from plinth.modules import gitweb

from . import privileged
from .forms import CreateRepoForm, EditRepoForm


class GitwebAppView(views.AppView):
    """Serve configuration page."""

    app_id = 'gitweb'
    template_name = 'gitweb_configure.html'

    def get_context_data(self, *args, **kwargs):
        """Add repositories to the context data."""
        context = super().get_context_data(*args, **kwargs)
        repos = gitweb.get_repo_list()
        context['repos'] = repos
        context['cloning'] = any('clone_progress' in repo for repo in repos)
        if context['cloning']:
            context['refresh_page_sec'] = 3

        return context


class CreateRepoView(SuccessMessageMixin, FormView):
    """View to create a new repository."""

    form_class = CreateRepoForm
    prefix = 'gitweb'
    template_name = 'form.html'
    success_url = reverse_lazy('gitweb:index')
    success_message = _('Repository created.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Repository')
        return context

    def form_valid(self, form):
        """Create the repository on valid form submission."""
        form_data = {}
        for key, value in form.cleaned_data.items():
            if value is None:
                form_data[key] = ''
            else:
                form_data[key] = value
        try:
            gitweb.create_repo(form_data['name'], form_data['description'],
                               form_data['owner'], form_data['is_private'])
        except Exception as error:
            self.success_message = ''
            messages.error(
                self.request, "{0} {1}".format(
                    _('An error occurred while creating the repository.'),
                    error))
        else:
            app_module.App.get('gitweb').update_service_access()

        return super().form_valid(form)


class EditRepoView(SuccessMessageMixin, FormView):
    """View to edit an existing repository."""

    form_class = EditRepoForm
    prefix = 'gitweb'
    template_name = 'form.html'
    success_url = reverse_lazy('gitweb:index')
    success_message = _('Repository edited.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit repository')
        return context

    def get_initial(self):
        """Load information about repository being edited."""
        name = self.kwargs['name']
        for repo in gitweb.get_repo_list():
            if repo['name'] == name and 'clone_progress' not in repo:
                break
        else:
            raise Http404

        return gitweb.repo_info(name)

    def form_valid(self, form):
        """Edit the repo on valid form submission."""
        if form.initial != form.cleaned_data:
            form_data = {}
            for key, value in form.cleaned_data.items():
                if value is None:
                    form_data[key] = ''
                else:
                    form_data[key] = value

            try:
                gitweb.edit_repo(form.initial, form_data)
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))
        app_module.App.get('gitweb').update_service_access()

        return super().form_valid(form)


def delete(request, name):
    """Handle deleting repositories, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the repository.
    """
    for repo in gitweb.get_repo_list():
        if repo['name'] == name and 'clone_progress' not in repo:
            break
    else:
        raise Http404

    app = app_module.App.get('gitweb')
    if request.method == 'POST':
        try:
            privileged.delete_repo(name)
            messages.success(request, _('{name} deleted.').format(name=name))
        except Exception as error:
            messages.error(
                request,
                _('Could not delete {name}: {error}').format(
                    name=name, error=error),
            )
        app.update_service_access()

        return redirect(reverse_lazy('gitweb:index'))

    return TemplateResponse(request, 'gitweb_delete.html', {
        'title': app.info.name,
        'name': name
    })
