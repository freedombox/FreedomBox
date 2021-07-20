# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import itertools
import pwd

import plinth.utils
import plinth.views

from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from . import aliases
from . import audit
from . import forms

admin_tabs = [
    ('', _('Home')),
    ('my_mail', _('My Mail')),
    ('my_aliases', _('My Aliases'))
]

user_tabs = [
    ('my_mail', _('Home')),
    ('my_aliases', _('My Aliases'))
]


class EmailServerView(plinth.views.AppView):
    """Server configuration page"""
    app_id = 'email_server'
    template_name = 'email_server.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['tabs'] = render_tabs(self.request)
        return context


class MyMailView(TemplateView):
    template_name = 'my_mail.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['tabs'] = render_tabs(self.request)

        nam = self.request.user.username
        context['has_homedir'] = audit.home.exists_nam(nam)

        return context

    def post(self, request):
        try:
            return self._post(request)
        except ValidationError as validation_error:
            context = self.get_context_data()
            context['error'] = validation_error
            return self.render_to_response(context, status=400)
        except RuntimeError as runtime_error:
            context = self.get_context_data()
            context['error'] = [str(runtime_error)]
            return self.render_to_response(context, status=500)

    def _post(self, request):
        if not 'btn_mkhome' in request.POST:
            raise ValidationError('Bad post data')
        audit.home.put_nam(request.user.username)
        return self.render_to_response(self.get_context_data())


class AliasView(TemplateView):
    class Checkboxes:
        def __init__(self, post=None, initial=None):
            self.models = initial
            self.post = post
            self.cleaned_data = {}
            # HTML rendering
            self.sb = io.StringIO()
            self.counter = 0

        def render(self):
            if self.models is None:
                raise RuntimeError('Uninitialized form')
            if self.sb.tell() > 0:
                raise RuntimeError('render has been called')

            enabled = [a.email_name for a in self.models if a.enabled]
            disabled = [a.email_name for a in self.models if not a.enabled]

            self._render_fieldset(enabled, _('Enabled aliases'))
            self._render_fieldset(disabled, _('Disabled aliases'))

            return self.sb.getvalue()

        def _render_fieldset(self, email_names, legend):
            if len(email_names) > 0:
                self.sb.write('<fieldset class="form-group">')
                self.sb.write('<legend>%s</legend>' % escape(legend))
                self._render_boxes(email_names)
                self.sb.write('</fieldset>')

        def _render_boxes(self, email_names):
            for email_name in email_names:
                input_id = 'cb_alias_%d' % self._count()
                value = escape(email_name)
                self.sb.write('<div class="form-check">')

                self.sb.write('<input type="checkbox" name="alias" ')
                self.sb.write('class="form-check-input" ')
                self.sb.write('id="%s" value="%s">' % (input_id, value))

                self.sb.write('<label class="form-check-label" ')
                self.sb.write('for="%s">%s</label>' % (input_id, value))

                self.sb.write('</div>')

        def _count(self):
            self.counter += 1
            return self.counter

        def is_valid(self):
            lst = list(filter(None, self.post.getlist('alias')))
            if not lst:
                return False
            else:
                self.cleaned_data['alias'] = lst
                return True

    template_name = 'alias.html'
    form_classes = (forms.AliasCreationForm, Checkboxes)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['form'] = forms.AliasCreationForm()
        context['tabs'] = render_tabs(self.request)

        uid = pwd.getpwnam(self.request.user.username).pw_uid
        models = aliases.get(uid)
        if len(models) > 0:
            form = AliasView.Checkboxes(initial=models)
            context['alias_boxes'] = form.render()
        else:
            context['no_alias'] = True
        return context

    def find_form(self, post):
        form_name = post.get('form')
        for cls in self.form_classes:
            if cls.__name__ == form_name:
                return cls(post)
        raise ValidationError('Form was unspecified')

    def find_button(self, post):
        key_filter = (k for k in post.keys() if k.startswith('btn_'))
        lst = list(itertools.islice(key_filter, 2))
        if len(lst) != 1:
            raise ValidationError('Bad post data')
        if not isinstance(lst[0], str):
            raise ValidationError('Bad post data')
        return lst[0][len('btn_'):]

    def post(self, request):
        try:
            return self._post(request)
        except ValidationError as e:
            context = self.get_context_data()
            context['error'] = e
            return self.render_to_response(context, status=400)

    def _post(self, request):
        form = self.find_form(request.POST)
        button = self.find_button(request.POST)
        if not form.is_valid():
            raise ValidationError('Form invalid')

        if isinstance(form, AliasView.Checkboxes):
            if button not in ('delete', 'disable', 'enable'):
                raise ValidationError('Bad button')
            return self.alias_operation_form_valid(form, button)

        if isinstance(form, forms.AliasCreationForm):
            if button != 'add':
                raise ValidationError('Bad button')
            return self.alias_creation_form_valid(form, button)

        raise RuntimeError('Unknown form')

    def alias_operation_form_valid(self, form, button):
        uid = pwd.getpwnam(self.request.user.username).pw_uid
        alias_list = form.cleaned_data['alias']
        if button == 'delete':
            aliases.delete(uid, alias_list)
        elif button == 'disable':
            aliases.set_disabled(uid, alias_list)
        elif button == 'enable':
            aliases.set_enabled(uid, alias_list)
        return self.render_to_response(self.get_context_data())

    def alias_creation_form_valid(self, form, button):
        uid = pwd.getpwnam(self.request.user.username).pw_uid
        aliases.put(uid, form.cleaned_data['email_name'])
        return self.render_to_response(self.get_context_data())


def render_tabs(request):
    if plinth.utils.is_user_admin(request):
        return _render_tabs(request, admin_tabs)
    else:
        return _render_tabs(request, user_tabs)


def _render_tabs(request, tab_data):
    sb = io.StringIO()
    sb.write('<ul class="nav nav-tabs">')
    for page_name, link_text in tab_data:
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
            cls=cls, href=href, text=escape(link_text)
        ))
        sb.write('</li>')
    sb.write('</ul>')
    return sb.getvalue()
