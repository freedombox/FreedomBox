from django import forms
from django.contrib import auth, messages
from django.core import validators
from gettext import gettext as _

from plinth.modules.config import config


class State0Form(forms.ModelForm):
    """Firstboot state 0: Set hostname and create a new user"""
    hostname = forms.CharField(
        label=_('Name of your FreedomBox'),
        help_text=_('For convenience, your FreedomBox needs a name.  It \
should be something short that does not contain spaces or punctuation. \
"Willard" would be a good name while "Freestyle McFreedomBox!!!" would \
not. It must be alphanumeric, start with an alphabet and must not be greater \
than 63 characters in length.'),
        validators=[
            validators.RegexValidator(r'^[a-zA-Z][a-zA-Z0-9]{,62}$',
                                      _('Invalid hostname'))])

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(State0Form, self).__init__(*args, **kwargs)

    class Meta:
        model = auth.models.User
        fields = ('hostname', 'username', 'password')
        widgets = {
            'password': forms.PasswordInput,
        }
        help_texts = {
            'username': _('Choose a username and password to access this web\
 interface. The password can be changed and other users can be added later.'),
        }

    def save(self, commit=True):
        """Set hostname, create and login the user"""
        config.set_hostname(self.cleaned_data['hostname'])
        user = super(State0Form, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_expert = True
        if commit:
            user.save()
            self.login_user()

        return user

    def login_user(self):
        """Try to login the user with the credentials provided"""
        try:
            user = auth.authenticate(username=self.request.POST['username'],
                                     password=self.request.POST['password'])
            auth.login(self.request, user)
        except Exception:
            pass
        else:
            message = _('User account created, you are now logged in')
            messages.success(self.request, message)
