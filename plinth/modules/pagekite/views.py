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

from gettext import gettext as _
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.template.response import TemplateResponse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from plinth import package
from .util import get_status
from .forms import ConfigurationForm, CustomServiceForm

subsubmenu = [{'url': reverse_lazy('pagekite:index'),
               'text': _('About PageKite')},
              {'url': reverse_lazy('pagekite:configure'),
               'text': _('Configure PageKite')},
              {'url': reverse_lazy('pagekite:services'),
               'text': _('Custom Services')}]


@login_required
def index(request):
    """Serve introduction page"""
    return TemplateResponse(request, 'pagekite_introduction.html',
                            {'title': _('Public Visibility (PageKite)'),
                             'subsubmenu': subsubmenu})


class ContextMixin(object):
    """Mixin to add 'subsubmenu' and 'title' to the context."""
    def get_context_data(self, **kwargs):
        """Use self.title and the module-level subsubmenu"""
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['title'] = getattr(self, 'title', '')
        context['subsubmenu'] = subsubmenu
        return context


class ServiceView(ContextMixin, TemplateView):
    template_name = 'pagekite_custom_services.html'
    title = 'PageKite Custom Services'


class ConfigurationView(ContextMixin, FormView):
    template_name = 'pagekite_configure.html'
    form_class = ConfigurationForm
    prefix = 'pagekite'
    success_url = reverse_lazy('pagekite:configure')

    def get_initial(self):
        """prepare format as returned by get_status() for the form"""
        return get_status()

    def form_valid(self, form):
        form.save(self.request)
        return super(ConfigurationView, self).form_valid(form)


@login_required
@package.required('pagekite')
def configure(request):
    """Serve the configuration form"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = ConfigurationForm(request.POST, prefix='pagekite')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigurationForm(initial=status, prefix='pagekite')
    else:
        form = ConfigurationForm(initial=status, prefix='pagekite')

    return TemplateResponse(request, 'pagekite_configure.html',
                            {'title': _('Configure PageKite'),
                             'status': status,
                             'form': form,
                             'subsubmenu': subsubmenu})


