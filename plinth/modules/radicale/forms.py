from plinth.forms import ServiceForm
from django import forms

class RadicaleForm(ServiceForm):
    """Specialized configuration form for radicale service."""
    CHOICES = [('authenticated', 'Authenticated'),
               ('owner_only', 'Owner Only'),
               ('owner_write', 'Owner Write'), ]
    rights = forms.ChoiceField(choices=CHOICES, required=True,
                               widget=forms.RadioSelect())
