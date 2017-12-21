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
Plinth module to configure sharing.
"""
import os

from django import forms
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _, ugettext_lazy

from plinth import actions
from plinth.menu import main_menu
from plinth.modules.users import groups

version = 1

name = _('Sharing')

short_description = _('File Sharing')

description = [
    _('Sharing allows you to share your content over web with a group of '
      'users. Add the content you would like to share in the sharing app.'),

    _('Sharing app will be available from <a href="/plinth/apps/add_share">'
      '/sharing</a> path on the web server.'),
]

subsubmenu = [{'url': reverse_lazy('sharing:about'),
               'text': ugettext_lazy('About')},
              {'url': reverse_lazy('sharing:add_share'),
               'text': ugettext_lazy('Add share')}]


def init():
    """Initialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-share', 'sharing:about')


def index(request):
    return TemplateResponse(request, 'about.html',
                            {'title': name,
                             'description': description,
                             'subsubmenu': subsubmenu})


# TODO: handle the error case
def add_path_to_share(url, path, user_group):
    if os.path.exists(path):
        actions.superuser_run('sharing', options=['add', url, path, user_group])
    else:
        pass


def share(request):
    if request.method == 'POST':
        form = AddShareForm(request.POST)

        if form.is_valid():
            path = form.cleaned_data['share_path']
            user_group = form.cleaned_data['user_group']
            share_url = 'share_' + path.split("/")[len(path.split("/")) - 1]
            add_path_to_share(share_url, path, user_group)

            form = AddShareForm()

    else:
        form = AddShareForm()

    return TemplateResponse(request, 'share.html',
                            {'title': name,
                             'subsubmenu': subsubmenu,
                             'form': form})


class AddShareForm(forms.Form):
    share_path = forms.CharField(
        label=_('Add path'),
        help_text=_('Add the path to the folder you want to share'))

    user_group = forms.ChoiceField(
        required=False,
        choices=groups,
        label=_('User-group'),
        initial=None)

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        return
