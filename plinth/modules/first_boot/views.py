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
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, FormView, TemplateView

from plinth import cfg
from plinth import kvstore
from plinth import network
from plinth.errors import DomainRegistrationError
from .forms import State1Form, State5Form


class State0View(TemplateView):
    """Show the welcome screen."""
    template_name = 'firstboot_state0.html'


class State1View(CreateView):
    """Create user account and log the user in."""
    template_name = 'firstboot_state1.html'
    form_class = State1Form
    success_url = reverse_lazy('first_boot:state10')

    def __init__(self, *args, **kwargs):
        """Initialize the view object."""
        if cfg.danube_edition:
            self.success_url = reverse_lazy('first_boot:state5')

        return super(State1View, self).__init__(*args, **kwargs)

    def get_form_kwargs(self):
        """Make request available to the form (to insert messages)"""
        kwargs = super(State1View, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


def state10(request):
    """State 10 is when all firstboot setup is done.

    After viewing this page the firstboot module can't be accessed anymore.
    """
    # Make sure that a user exists before finishing firstboot
    if User.objects.all():
        kvstore.set('firstboot_state', 10)

    connections = network.get_connection_list()

    return render_to_response('firstboot_state10.html',
                              {'title': _('Setup Complete'),
                               'connections': connections},
                              context_instance=RequestContext(request))


class State5View(FormView):
    """State 5 is the (optional) setup of the Pagekite subdomain."""
    template_name = 'firstboot_state5.html'
    form_class = State5Form
    success_url = reverse_lazy('first_boot:state10')

    def get(self, *args, **kwargs):
        """Respond to GET request."""
        kvstore.set('firstboot_state', 5)
        return super(State5View, self).get(*args, **kwargs)

    def form_valid(self, form):
        """Act on valid form submission."""
        try:
            form.register_domain()
        except DomainRegistrationError as error:
            messages.error(self.request, error)
            return HttpResponseRedirect(reverse_lazy('first_boot:state5'))
        else:
            form.setup_pagekite()
            message = _('Pagekite setup finished. The HTTP and HTTPS services '
                        'are activated now.')
            messages.success(self.request, message)
            return super(State5View, self).form_valid(form)
