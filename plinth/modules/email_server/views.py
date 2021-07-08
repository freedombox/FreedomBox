# SPDX-License-Identifier: AGPL-3.0-or-later
import io

import plinth.views
from django.shortcuts import render
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from . import forms

tabs = [
    ('', 'Home'),
    ('alias', 'Alias'),
    ('relay', 'Relay'),
    ('security', 'Security')
]


class EmailServerView(plinth.views.AppView):
    """Server configuration page"""
    app_id = 'email_server'
    form_class = forms.EmailServerForm
    template_name = 'email_server.html'

    def form_valid(self, form):
        # old_settings = form.initial
        # new_status = form.cleaned_data
        # plinth.actions.superuser_run('email_server', ['--help'])
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['tabs'] = render_tabs(self.request)
        return context


def render_tabs(request):
    sb = io.StringIO()
    sb.write('<ul class="nav nav-tabs">')
    for page_name, link_text in tabs:
        if request.path.endswith('/' + page_name):
            cls = 'active'
        else:
            cls = ''
        if cls == 'active':
            href = '#'
        else:
            href = escape('./' + page_name)

        sb.write('<li class="nav-item">')
        sb.write('<a class="nav-link {cls}" href="{href}">{text}</a>'.format(
            cls=cls, href=href, text=escape(_(link_text))
        ))
        sb.write('</li>')
    sb.write('</ul>')
    return sb.getvalue()
