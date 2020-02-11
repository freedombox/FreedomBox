#
# This file is part of FreedomBox.
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
Views for the sharing app.
"""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from plinth.modules import sharing

from .forms import AddShareForm


class IndexView(TemplateView):
    """View to show list of shares."""
    template_name = 'sharing.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = sharing.app.info.name
        context['app_info'] = sharing.app.info
        context['shares'] = sharing.list_shares()
        return context


class AddShareView(SuccessMessageMixin, FormView):
    """View to add a new share."""
    form_class = AddShareForm
    prefix = 'sharing'
    template_name = 'sharing_add_edit.html'
    success_url = reverse_lazy('sharing:index')
    success_message = _('Share added.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Share')
        return context

    def form_valid(self, form):
        """Add the share on valid form submission."""
        _add_share(form.cleaned_data)
        return super().form_valid(form)


class EditShareView(SuccessMessageMixin, FormView):
    """View to edit an existing share."""
    form_class = AddShareForm
    prefix = 'sharing'
    template_name = 'sharing_add_edit.html'
    success_url = reverse_lazy('sharing:index')
    success_message = _('Share edited.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Share')
        return context

    def get_initial(self):
        """Load information about share being edited."""
        try:
            return [
                share for share in sharing.list_shares()
                if share['name'] == self.kwargs['name']
            ][0]
        except IndexError:
            raise Http404

    def form_valid(self, form):
        """Add the share on valid form submission."""
        if form.initial != form.cleaned_data:
            sharing.remove_share(form.initial['name'])
            _add_share(form.cleaned_data)

        return super().form_valid(form)


def _add_share(form_data):
    sharing.add_share(form_data['name'], form_data['path'],
                      form_data['groups'], form_data['is_public'])


@require_POST
def remove(request, name):
    """View to remove a share."""
    sharing.remove_share(name)
    messages.success(request, _('Share deleted.'))
    return redirect(reverse_lazy('sharing:index'))
