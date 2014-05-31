"""
Controller to provide login and logout actions
"""

import cherrypy
import cfg
from django import forms
from gettext import gettext as _
from plugin_mount import PagePlugin
import auth
import util


class LoginForm(forms.Form):  # pylint: disable-msg=W0232
    """Login form"""
    from_page = forms.CharField(widget=forms.HiddenInput(), required=False)

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


class AuthController(PagePlugin):
    """Login and logout pages"""

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page('auth')

    def on_login(self, username):
        """Called on successful login"""

    def on_logout(self, username):
        """Called on logout"""

    @cherrypy.expose
    def login(self, from_page=cfg.server_dir+"/", **kwargs):
        """Serve the login page"""
        form = None

        if kwargs:
            form = LoginForm(kwargs, prefix='auth')
            # pylint: disable-msg=E1101
            if form.is_valid():
                username = form.cleaned_data['username']
                cherrypy.session[cfg.session_key] = username
                cherrypy.request.login = username
                self.on_login(username)
                raise cherrypy.HTTPRedirect(from_page or
                                            (cfg.server_dir + "/"))
        else:
            form = LoginForm(prefix='auth')

        return util.render_template(template='form', title=_('Login'),
                                    form=form, submit_text=_('Login'))

    @cherrypy.expose
    def logout(self, from_page=cfg.server_dir+"/"):
        sess = cherrypy.session
        username = sess.get(cfg.session_key, None)
        sess[cfg.session_key] = None
        if username:
            cherrypy.request.login = None
            self.on_logout(username)

        raise cherrypy.HTTPRedirect(from_page or (cfg.server_dir + "/"))
