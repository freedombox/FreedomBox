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

from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.views.generic import TemplateView

from .registry import apps, statusline_items


class Index(TemplateView):
    template_name = 'dashboard_index.html'

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        context['apps'] = OrderedDict(sorted(apps.items(),
                                             key=lambda x: x[0].lower()))
        _items = OrderedDict(sorted(statusline_items.items(),
                                    key=lambda x: x[1]['order']))
        context['statusline_items'] = _items
        return context


def enable_app(request, module):
    next = request.GET.get('next', reverse('index'))
    apps[module]['enable']()
    if not apps[module]['synchronous']:
        msg = """Enabling %s. It can take a couple of minutes until all
              changes take place.""" % module
        messages.success(request, msg)
    return HttpResponseRedirect(next)


def disable_app(request, module):
    next = request.GET.get('next', reverse('index'))
    apps[module]['disable']()
    if not apps[module]['synchronous']:
        msg = """Disabling %s. It can take a couple of minutes until all
              changes take place.""" % module
        messages.success(request, msg)
    return HttpResponseRedirect(next)
