# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Feather Wiki."""

import tempfile

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from plinth import app as app_module
from plinth import views
from plinth.modules import featherwiki

from . import privileged
from .forms import CreateWikiForm, RenameWikiForm, UploadWikiForm

DUPLICATE_FILE_ERROR = _('A wiki file with the given name already exists.')


class FeatherWikiAppView(views.AppView):
    """Serve configuration page."""

    app_id = 'featherwiki'
    template_name = 'featherwiki_configure.html'

    def get_context_data(self, *args, **kwargs):
        """Add wikis to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context['wikis'] = featherwiki.get_wiki_list()
        return context


class CreateWikiView(SuccessMessageMixin, FormView):
    """View to create a new repository."""

    form_class = CreateWikiForm
    prefix = 'featherwiki'
    template_name = 'form.html'
    success_url = reverse_lazy('featherwiki:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Wiki')
        return context

    def form_valid(self, form):
        """Create the repository on valid form submission."""
        try:
            privileged.create_wiki(form.cleaned_data['name'])
            self.success_message = _('Wiki created.')
        except ValueError:
            messages.error(self.request, DUPLICATE_FILE_ERROR)
        except Exception as error:
            messages.error(
                self.request, "{0} {1}".format(
                    _('An error occurred while creating the wiki.'), error))

        return super().form_valid(form)


class RenameWikiView(SuccessMessageMixin, FormView):
    """View to edit an existing repository."""

    form_class = RenameWikiForm
    prefix = 'featherwiki'
    template_name = 'form.html'
    success_url = reverse_lazy('featherwiki:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Rename Wiki')
        return context

    def form_valid(self, form):
        """Rename the wiki on valid form submission."""
        try:
            privileged.rename_wiki(self.kwargs['old_name'],
                                   form.cleaned_data['new_name'])
            self.success_message = _('Wiki renamed.')
        except ValueError:
            messages.error(self.request, DUPLICATE_FILE_ERROR)
        except Exception as error:
            messages.error(
                self.request, "{0} {1}".format(
                    _('An error occurred while renaming the wiki.'), error))

        return super().form_valid(form)


class UploadWikiView(SuccessMessageMixin, FormView):
    """View to upload an existing wiki file."""

    form_class = UploadWikiForm
    prefix = 'featherwiki'
    template_name = 'featherwiki_upload_file.html'
    success_url = reverse_lazy('featherwiki:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload Wiki File')
        return context

    def form_valid(self, form):
        """Add the wiki file on valid form submission."""
        multipart_file = self.request.FILES['featherwiki-file']

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                wiki_file_name = temp_dir + '/' + multipart_file.name
                with open(wiki_file_name, 'wb+') as wiki_file:
                    for chunk in multipart_file.chunks():
                        wiki_file.write(chunk)

                privileged.add_wiki_file(wiki_file_name)

            self.success_message = _('Wiki file added.')
        except ValueError:
            messages.error(self.request, DUPLICATE_FILE_ERROR)
        except Exception as error:
            messages.error(
                self.request, "{0} {1}".format(_('Failed to add wiki file.'),
                                               error))
            return redirect(reverse_lazy('featherwiki:index'))

        return super().form_valid(form)


def delete(request, name):
    """Handle deleting wikis, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the wiki.
    """
    app = app_module.App.get('featherwiki')
    if request.method == 'POST':
        try:
            privileged.delete_wiki(name)
            messages.success(request, _('{name} deleted.').format(name=name))
        except Exception as error:
            messages.error(
                request,
                _('Could not delete {name}: {error}').format(
                    name=name, error=error))

        return redirect(reverse_lazy('featherwiki:index'))

    return TemplateResponse(request, 'featherwiki_delete.html', {
        'title': app.info.name,
        'name': name
    })
