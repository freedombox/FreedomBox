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
from django.template.response import TemplateResponse
from gettext import gettext as _

from .forms import IkiwikiForm, IkiwikiCreateForm
from plinth import actions
from plinth import package
from plinth.modules import ikiwiki


subsubmenu = [{'url': reverse_lazy('ikiwiki:index'),
               'text': _('Configure')},
              {'url': reverse_lazy('ikiwiki:manage'),
               'text': _('Manage')},
              {'url': reverse_lazy('ikiwiki:create'),
               'text': _('Create')}]


@login_required
@package.required(['ikiwiki', 'libcgi-formbuilder-perl', 'libcgi-session-perl'])
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
                _create_wiki(request, form.cleaned_data['name'])
            elif form.cleaned_data['type'] == 'blog':
                _create_blog(request, form.cleaned_data['name'])
            form = IkiwikiCreateForm(prefix='ikiwiki')
    else:
        form = IkiwikiCreateForm(prefix='ikiwiki')

    return TemplateResponse(request, 'ikiwiki_create.html',
                            {'title': _('Create Wiki/Blog'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def _create_wiki(request, name):
    """Create wiki."""
    actions.superuser_run('ikiwiki', ['create-wiki', '--name', name])


def _create_blog(request, name):
    """Create blog."""
    actions.superuser_run('ikiwiki', ['create-blog', '--name', name])
