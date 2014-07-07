"""
Controller to provide login and logout actions
"""

import cfg
from django import forms
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from gettext import gettext as _

from . import auth


class LoginForm(forms.Form):  # pylint: disable-msg=W0232
    """Login form"""
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Passphrase'),
                               widget=forms.PasswordInput())

    def clean(self):
        """Check for valid credentials"""
        # pylint: disable-msg=E1101
        if 'username' in self._errors or 'password' in self._errors:
            return self.cleaned_data

        error_msg = auth.check_credentials(self.cleaned_data['username'],
                                           self.cleaned_data['password'])
        if error_msg:
            raise forms.ValidationError(error_msg, code='invalid_credentials')

        return self.cleaned_data


def login(request):
    """Serve the login page"""
    form = None

    if request.method == 'POST':
        form = LoginForm(request.POST, prefix='auth')
        # pylint: disable-msg=E1101
        if form.is_valid():
            username = form.cleaned_data['username']
            request.session[cfg.session_key] = username
            return HttpResponseRedirect(_get_from_page(request))
    else:
        form = LoginForm(prefix='auth')

    return TemplateResponse(request, 'form.html',
                            {'title': _('Login'),
                             'form': form,
                             'submit_text': _('Login')})


def logout(request):
    """Logout and redirect to origin page"""
    try:
        del request.session[cfg.session_key]
        request.session.flush()
    except KeyError:
        pass

    return HttpResponseRedirect(_get_from_page(request))


def _get_from_page(request):
    """Return the 'from page' of a request"""
    return request.GET.get('from_page', cfg.server_dir + '/')
