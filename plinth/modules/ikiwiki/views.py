# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring ikiwiki."""

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from plinth import app as app_module
from plinth import views

from . import privileged
from .forms import IkiwikiCreateForm


class IkiwikiAppView(views.AppView):
    """Serve configuration page."""

    app_id = 'ikiwiki'
    template_name = 'ikiwiki_configure.html'

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        app = app_module.App.get('ikiwiki')
        sites = app.refresh_sites()
        sites = [name for name in sites if name != '']

        context = super().get_context_data(**kwargs)
        context['sites'] = sites
        return context


def create(request):
    """Form to create a wiki or blog."""
    form = None

    app = app_module.App.get('ikiwiki')
    if request.method == 'POST':
        form = IkiwikiCreateForm(request.POST, prefix='ikiwiki')
        if form.is_valid():
            if form.cleaned_data['site_type'] == 'wiki':
                _create_wiki(request, form.cleaned_data['name'],
                             form.cleaned_data['admin_name'],
                             form.cleaned_data['admin_password'])
            elif form.cleaned_data['site_type'] == 'blog':
                _create_blog(request, form.cleaned_data['name'],
                             form.cleaned_data['admin_name'],
                             form.cleaned_data['admin_password'])

            app.refresh_sites()
            if app.is_enabled():
                app.set_enabled(True)

            return redirect(reverse_lazy('ikiwiki:index'))
    else:
        form = IkiwikiCreateForm(prefix='ikiwiki')

    return TemplateResponse(request, 'ikiwiki_create.html', {
        'title': app.info.name,
        'form': form
    })


def _create_wiki(request, name, admin_name, admin_password):
    """Create wiki."""
    try:
        privileged.create_wiki(name, admin_name, admin_password)
        messages.success(request, _('Created wiki {name}.').format(name=name))
    except Exception as error:
        messages.error(request,
                       _('Could not create wiki: {error}').format(error=error))


def _create_blog(request, name, admin_name, admin_password):
    """Create blog."""
    try:
        privileged.create_blog(name, admin_name, admin_password)
        messages.success(request, _('Created blog {name}.').format(name=name))
    except Exception as error:
        messages.error(request,
                       _('Could not create blog: {error}').format(error=error))


def delete(request, name):
    """Handle deleting wikis/blogs, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the wiki/blog.
    """
    app = app_module.App.get('ikiwiki')
    title = app.components['shortcut-ikiwiki-' + name].name
    if request.method == 'POST':
        try:
            privileged.delete(name)
            app.remove_shortcut(name)
            messages.success(request,
                             _('{title} deleted.').format(title=title))
        except Exception as error:
            messages.error(
                request,
                _('Could not delete {title}: {error}').format(
                    title=title, error=error))

        return redirect(reverse_lazy('ikiwiki:index'))

    return TemplateResponse(request, 'ikiwiki_delete.html', {
        'title': app.info.name,
        'name': title
    })
