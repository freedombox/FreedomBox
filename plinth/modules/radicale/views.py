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

import augeas

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth.views import ServiceView
from plinth import cfg
from plinth.utils import format_lazy
from plinth import actions

from .forms import RadicaleForm

CONFIG_FILE = '/etc/radicale/config'
DEFAULT_FILE = '/etc/default/radicale'

description = [
    format_lazy(
        _('Radicale is a CalDAV and CardDAV server. It allows synchronization '
          'and sharing of scheduling and contact data. To use Radicale, a '
          '<a href="http://radicale.org/user_documentation/'
          '#idcaldav-and-carddav-clients"> supported client application</a> '
          'is needed. Radicale can be accessed by any user with a {box_name} '
          'login.'), box_name=_(cfg.box_name)),
]


def load_augeas():
    """Prepares the augeas"""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                              augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', DEFAULT_FILE)

    # INI file lens
    aug.set('/augeas/load/Puppet/lens', 'Puppet.lns')
    aug.set('/augeas/load/Puppet/incl[last() + 1]', CONFIG_FILE)
    aug.load()
    return aug


def get_rights_value():
    """Returns the current Rights value"""
    aug = load_augeas()
    value = aug.get('/files' + CONFIG_FILE + '/rights/type')
    return value


class RadicaleServiceView(ServiceView):
    """A specialized view for configuring radicale service."""
    service_id = 'radicale'
    form_class = RadicaleForm
    diagnostics_module_name = 'radicale'
    description = description

    def get_initial(self):
        """Return the values to fill in the form"""
        initial = super().get_initial()
        initial['rights'] = get_rights_value()
        return initial

    def form_valid(self, form):
        """Change the access control of Radicale service."""
        data = form.cleaned_data
        if get_rights_value() != data['rights']:
            actions.superuser_run('radicale', ['configure', '--rights_type', data['rights']])
            messages.success(self.request, _('Status Changed'))
        return super().form_valid(form)
