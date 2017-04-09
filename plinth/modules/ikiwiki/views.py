#
# This file is part of Plinth.
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
Plinth module for configuring ikiwiki
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _, ugettext_lazy

from plinth import actions
from plinth import frontpage
from plinth import views
from plinth.modules import ikiwiki

from .forms import IkiwikiCreateForm


subsubmenu = [{'url': reverse_lazy('ikiwiki:index'),
               'text': ugettext_lazy('Configure')},
              {'url': reverse_lazy('ikiwiki:manage'),
               'text': ugettext_lazy('Manage')},
              {'url': reverse_lazy('ikiwiki:create'),
               'text': ugettext_lazy('Create')}]


class IkiwikiServiceView(views.ServiceView):
    """Serve configuration page."""
    service_id = "ikiwiki"
    description = ikiwiki.description
    diagnostics_module_name = "ikiwiki"
    show_status_block = False

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        context['subsubmenu'] = subsubmenu
        return context


def manage(request):
    """Manage existing wikis and blogs."""
    sites = actions.run('ikiwiki', ['get-sites']).split('\n')
    sites = [name for name in sites if name != '']

    return TemplateResponse(request, 'ikiwiki_manage.html',
                            {'title': _('Manage Wikis and Blogs'),
                             'subsubmenu': subsubmenu,
                             'sites': sites})


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

            site = form.cleaned_data['name'].replace(' ', '')
            frontpage.add_shortcut(
                'ikiwiki_' + site, site, url='/ikiwiki/' + site,
                login_required=False, icon='ikiwiki')

            return redirect(reverse_lazy('ikiwiki:manage'))
    else:
        form = IkiwikiCreateForm(prefix='ikiwiki')

    return TemplateResponse(request, 'ikiwiki_create.html',
                            {'title': _('Create Wiki or Blog'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def _create_wiki(request, name, admin_name, admin_password):
    """Create wiki."""
    try:
        actions.superuser_run(
            'ikiwiki',
            ['create-wiki', '--wiki_name', name,
             '--admin_name', admin_name],
            input=admin_password.encode())
        messages.success(request, _('Created wiki {name}.').format(name=name))
    except actions.ActionError as error:
        messages.error(request, _('Could not create wiki: {error}')
                       .format(error=error))


def _create_blog(request, name, admin_name, admin_password):
    """Create blog."""
    try:
        actions.superuser_run(
            'ikiwiki',
            ['create-blog', '--blog_name', name,
             '--admin_name', admin_name],
            input=admin_password.encode())
        messages.success(request, _('Created blog {name}.').format(name=name))
    except actions.ActionError as error:
        messages.error(request, _('Could not create blog: {error}')
                       .format(error=error))


def delete(request, name):
    """Handle deleting wikis/blogs, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the wiki/blog.
    """
    if request.method == 'POST':
        try:
            actions.superuser_run('ikiwiki', ['delete', '--name', name])
            messages.success(request, _('{name} deleted.').format(name=name))
            frontpage.remove_shortcut('ikiwiki_' + name)
        except actions.ActionError as error:
            messages.error(request, _('Could not delete {name}: {error}')
                           .format(name=name, error=error))

        return redirect(reverse_lazy('ikiwiki:manage'))

    return TemplateResponse(request, 'ikiwiki_delete.html',
                            {'title': _('Delete Wiki or Blog'),
                             'subsubmenu': subsubmenu,
                             'name': name})
