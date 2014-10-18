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
