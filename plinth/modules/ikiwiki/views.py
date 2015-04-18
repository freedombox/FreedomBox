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
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from gettext import gettext as _

from .forms import IkiwikiForm, IkiwikiCreateForm
from plinth import actions
from plinth import package


subsubmenu = [{'url': reverse_lazy('ikiwiki:index'),
               'text': _('Configure')},
              {'url': reverse_lazy('ikiwiki:manage'),
               'text': _('Manage')},
              {'url': reverse_lazy('ikiwiki:create'),
               'text': _('Create')}]


def on_install():
    """Enable Ikiwiki on install."""
    actions.superuser_run('ikiwiki', ['setup'])


@login_required
@package.required(['ikiwiki',
                   'libcgi-formbuilder-perl',
                   'libcgi-session-perl'],
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
                            {'title': _('Wiki & Blog'),
                             'status': status,
                             'form': form,
                             'subsubmenu': subsubmenu})


def get_status():
    """Get the current setting."""
    output = actions.run('ikiwiki', ['get-enabled'])
    enabled = (output.strip() == 'yes')
    return {'enabled': enabled}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('ikiwiki', [sub_command])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))


@login_required
def manage(request):
    """Manage existing wikis and blogs."""
    sites = actions.run('ikiwiki', ['get-sites']).split('\n')
    sites = [name for name in sites if name != '']

    return TemplateResponse(request, 'ikiwiki_manage.html',
                            {'title': _('Manage Wikis and Blogs'),
                             'subsubmenu': subsubmenu,
                             'sites': sites})


@login_required
def create(request):
    """Form to create a wiki or blog."""
    form = None

    if request.method == 'POST':
        form = IkiwikiCreateForm(request.POST, prefix='ikiwiki')
        if form.is_valid():
            if form.cleaned_data['type'] == 'wiki':
                _create_wiki(request, form.cleaned_data['name'],
                             form.cleaned_data['admin_name'],
                             form.cleaned_data['admin_password'])
            elif form.cleaned_data['type'] == 'blog':
                _create_blog(request, form.cleaned_data['name'],
                             form.cleaned_data['admin_name'],
                             form.cleaned_data['admin_password'])

            return redirect(reverse_lazy('ikiwiki:manage'))
    else:
        form = IkiwikiCreateForm(prefix='ikiwiki')

    return TemplateResponse(request, 'ikiwiki_create.html',
                            {'title': _('Create Wiki/Blog'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def _create_wiki(request, name, admin_name, admin_password):
    """Create wiki."""
    try:
        actions.superuser_run(
            'ikiwiki',
            ['create-wiki', '--wiki_name', name,
             '--admin_name', admin_name, '--admin_password', admin_password])
        messages.success(request, _('Created wiki %s.') % name)
    except actions.ActionError as err:
        messages.error(request, _('Could not create wiki: %s') % err)


def _create_blog(request, name, admin_name, admin_password):
    """Create blog."""
    try:
        actions.superuser_run(
            'ikiwiki',
            ['create-blog', '--blog_name', name,
             '--admin_name', admin_name, '--admin_password', admin_password])
        messages.success(request, _('Created blog %s.') % name)
    except actions.ActionError as err:
        messages.error(request, _('Could not create blog: %s') % err)


@login_required
def delete(request, name):
    """Handle deleting wikis/blogs, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the wiki/blog.
    """
    if request.method == 'POST':
        try:
            actions.superuser_run('ikiwiki', ['delete', '--name', name])
            messages.success(request, _('%s deleted.') % name)
        except actions.ActionError as err:
            messages.error(request, _('Could not delete %s: %s') % (name, err))

        return redirect(reverse_lazy('ikiwiki:manage'))

    return TemplateResponse(request, 'ikiwiki_delete.html',
                            {'title': _('Delete Wiki/Blog'),
                             'subsubmenu': subsubmenu,
                             'name': name})
