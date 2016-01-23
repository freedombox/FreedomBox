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
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _, ugettext_lazy

from .forms import IkiwikiForm, IkiwikiCreateForm
from plinth import actions
from plinth import action_utils
from plinth import package
from plinth.modules import ikiwiki


subsubmenu = [{'url': reverse_lazy('ikiwiki:index'),
               'text': ugettext_lazy('Configure')},
              {'url': reverse_lazy('ikiwiki:manage'),
               'text': ugettext_lazy('Manage')},
              {'url': reverse_lazy('ikiwiki:create'),
               'text': ugettext_lazy('Create')}]


def on_install():
    """Enable ikiwiki on install."""
    actions.superuser_run('ikiwiki', ['setup'])
    ikiwiki.service.notify_enabled(None, True)


@package.required(['ikiwiki',
                   'gcc',
                   'libc6-dev',
                   'libtimedate-perl',
                   'libcgi-formbuilder-perl',
                   'libcgi-session-perl',
                   'libxml-writer-perl'],
                  on_install=on_install)
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = IkiwikiForm(request.POST, prefix='ikiwiki')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = IkiwikiForm(initial=status, prefix='ikiwiki')
    else:
        form = IkiwikiForm(initial=status, prefix='ikiwiki')

    return TemplateResponse(request, 'ikiwiki.html',
                            {'title': _('Wiki and Blog'),
                             'status': status,
                             'form': form,
                             'subsubmenu': subsubmenu})


def get_status():
    """Get the current setting."""
    return {'enabled': ikiwiki.is_enabled()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('ikiwiki', [sub_command])
        ikiwiki.service.notify_enabled(None, new_status['enabled'])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))


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
        except actions.ActionError as error:
            messages.error(request, _('Could not delete {name}: {error}')
                           .format(name=name, error=error))

        return redirect(reverse_lazy('ikiwiki:manage'))

    return TemplateResponse(request, 'ikiwiki_delete.html',
                            {'title': _('Delete Wiki or Blog'),
                             'subsubmenu': subsubmenu,
                             'name': name})
