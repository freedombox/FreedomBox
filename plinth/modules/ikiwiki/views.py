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
FreedomBox app for configuring ikiwiki.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import ikiwiki

from .forms import IkiwikiCreateForm


class IkiwikiAppView(views.AppView):
    """Serve configuration page."""
    app_id = 'ikiwiki'
    name = ikiwiki.name
    description = ikiwiki.description
    diagnostics_module_name = 'ikiwiki'
    show_status_block = False
    template_name = 'ikiwiki_configure.html'
    manual_page = ikiwiki.manual_page
    clients = ikiwiki.clients

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        sites = ikiwiki.app.refresh_sites()
        sites = [name for name in sites if name != '']

        context = super().get_context_data(**kwargs)
        context['sites'] = sites
        return context


def create(request):
    """Form to create a wiki or blog."""
    form = None

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

            ikiwiki.app.refresh_sites()
            if ikiwiki.app.is_enabled():
                ikiwiki.app.set_enabled(True)

            return redirect(reverse_lazy('ikiwiki:index'))
    else:
        form = IkiwikiCreateForm(prefix='ikiwiki')

    return TemplateResponse(
        request, 'ikiwiki_create.html', {
            'title': ikiwiki.name,
            'clients': ikiwiki.clients,
            'description': ikiwiki.description,
            'form': form,
            'manual_page': ikiwiki.manual_page,
            'is_enabled': ikiwiki.app.is_enabled(),
        })


def _create_wiki(request, name, admin_name, admin_password):
    """Create wiki."""
    try:
        actions.superuser_run(
            'ikiwiki',
            ['create-wiki', '--wiki_name', name, '--admin_name', admin_name],
            input=admin_password.encode())
        messages.success(request, _('Created wiki {name}.').format(name=name))
    except actions.ActionError as error:
        messages.error(request,
                       _('Could not create wiki: {error}').format(error=error))


def _create_blog(request, name, admin_name, admin_password):
    """Create blog."""
    try:
        actions.superuser_run(
            'ikiwiki',
            ['create-blog', '--blog_name', name, '--admin_name', admin_name],
            input=admin_password.encode())
        messages.success(request, _('Created blog {name}.').format(name=name))
    except actions.ActionError as error:
        messages.error(request,
                       _('Could not create blog: {error}').format(error=error))


def delete(request, name):
    """Handle deleting wikis/blogs, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the wiki/blog.
    """
    title = ikiwiki.app.components['shortcut-ikiwiki-' + name].name
    if request.method == 'POST':
        try:
            actions.superuser_run('ikiwiki', ['delete', '--name', name])
            ikiwiki.app.remove_shortcut(name)
            messages.success(request,
                             _('{title} deleted.').format(title=title))
        except actions.ActionError as error:
            messages.error(
                request,
                _('Could not delete {title}: {error}').format(
                    title=title, error=error))

        return redirect(reverse_lazy('ikiwiki:index'))

    return TemplateResponse(request, 'ikiwiki_delete.html', {
        'title': ikiwiki.name,
        'name': title
    })
