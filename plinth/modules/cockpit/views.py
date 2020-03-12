# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Cockpit module
"""
from plinth.modules.cockpit.utils import get_origin_domains, load_augeas
from plinth.views import AppView


class CockpitAppView(AppView):
    app_id = 'cockpit'
    template_name = 'cockpit.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        urls = get_origin_domains(load_augeas())
        context['urls'] = [url for url in urls if 'localhost' not in url]

        return context
