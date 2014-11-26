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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.edit import CreateView
from gettext import gettext as _

from plinth import kvstore
from plinth.modules.config import config
from .forms import State0Form


class State0View(CreateView):
    """Setup hostname and create user account"""
    template_name = 'firstboot_state0.html'
    form_class = State0Form
    success_url = reverse_lazy('first_boot:state10')

    def get_initial(self):
        initial = super(State0View, self).get_initial()
        initial['hostname'] = config.get_hostname()
        return initial

    def get_form_kwargs(self):
        """Make request available to the form (to insert messages)"""
        kwargs = super(State0View, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


def state10(request):
    """State 10 is when all firstboot setup is done.

    After viewing this page the firstboot module can't be accessed anymore.
    """
    # Make sure that a user exists before finishing firstboot
    if User.objects.all():
        kvstore.set('firstboot_state', 10)

    return render_to_response('firstboot_state10.html',
                              {'title': _('Setup Complete')},
                              context_instance=RequestContext(request))
