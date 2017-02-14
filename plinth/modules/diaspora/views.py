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

from .forms import DiasporaForm
from plinth.modules import diaspora
from plinth import actions, package

from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from django.contrib import messages

def get_status():
    """Get the current status"""
    return {'enabled': diaspora.is_enabled()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('diaspora', [sub_command])
        modified = True

    if modified:
        messages.success(request, 'Configuration updated')
    else:
        messages.info(request, 'Setting unchanged')


# TODO
# If there are configuration tasks to be performed immediately before or after the package installation, Plinth provides hooks for it. The before_install= and
# on_install= parameters to the @package.required decorator take a callback methods that are called before installation of packages and after installation of
# packages respectively. See the reference section of this manual or the plinth.package module for details. Other modules in Plinth that use this feature provided
# example usage.
@package.required(['diaspora'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = DiasporaForm(request.POST, prefix='diaspora')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = DiasporaForm(initial=status, prefix='diaspora')
    else:
        form = DiasporaForm(initial=status, prefix='diaspora')

    return TemplateResponse(request, 'diaspora.html',
                            {'title': _(diaspora.title_en),
                             'status': status,
                             'form': form})

