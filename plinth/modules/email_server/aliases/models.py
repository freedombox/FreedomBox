import re
from dataclasses import InitVar, dataclass, field

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

email_positive_pattern = re.compile('^[a-zA-Z0-9-_\\.]+')


def sanitize_email_name(email_name):
    email_name = email_name.strip().lower()
    if len(email_name) < 2:
        raise ValidationError(_('Must be at least 2 characters long'))
    if not re.match('^[a-z0-9-_\\.]+$', email_name):
        raise ValidationError(_('Contains illegal characters'))
    if not re.match('^[a-z0-9].*[a-z0-9]$', email_name):
        raise ValidationError(_('Must start and end with a-z or 0-9'))
    if re.match('^[0-9]+$', email_name):
        raise ValidationError(_('Cannot be a number'))
    return email_name


@dataclass
class Alias:
    uid_number: int
    email_name: str
    enabled: bool = field(init=False)
    status: InitVar[int]

    def __post_init__(self, status):
        self.enabled = (status != 0)
