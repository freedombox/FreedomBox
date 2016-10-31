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

from django.contrib import messages
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, FormView, TemplateView

from plinth import cfg
from plinth import kvstore
from plinth import network
from plinth.errors import DomainRegistrationError
from .forms import State1Form, State5Form
from .middleware import mark_step_done, next_step


class State0View(TemplateView):
    """Show the welcome screen."""

    template_name = 'firstboot_state0.html'

    def get_context_data(self, **kwargs):
        """Returns the context data"""
        context = super(State0View, self).get_context_data(**kwargs)
        mark_step_done('firstboot_state0')
        context['next_url'] = next_step()
        return context


def state10(request):
    """State 10 is when all firstboot setup is done.

    After viewing this page the firstboot module can't be accessed anymore.
    """
    # Make sure that a user exists before finishing firstboot
    if User.objects.all():
        mark_step_done('firstboot_state')

    connections = network.get_connection_list()

    return render(request, 'firstboot_state10.html',
                  {'title': _('Setup Complete'),
                   'connections': connections})
