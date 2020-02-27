# SPDX-License-Identifier: AGPL-3.0-or-later

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.modules import first_boot


class FirstbootWizardSecretForm(forms.Form):
    """Form to collect and validate the first boot wizard secret."""
    secret = forms.CharField(
        label='', help_text=_(
            'Enter the secret generated during FreedomBox installation. '
            'This secret can also be obtained by running the command "sudo '
            'cat /var/lib/plinth/firstboot-wizard-secret" on your {box_name}'.
            format(box_name=_(cfg.box_name))), required=False,
        widget=forms.PasswordInput(
            attrs={'placeholder': _('Firstboot Wizard Secret')}))

    def validate_secret(self, secret):
        """Match the secret provided by the user with the one
        generated during installation.
        """
        secret_file_path = first_boot.get_secret_file_path()
        with open(secret_file_path) as secret_file:
            if secret != secret_file.read().strip():
                self.add_error('secret', 'Invalid secret')

    def clean(self):
        """Override clean to add form validation logic."""
        cleaned_data = super().clean()
        if first_boot.firstboot_wizard_secret_exists():
            self.validate_secret(cleaned_data.get("secret"))
        return cleaned_data
