from gettext import gettext as _
from django.template.response import TemplateResponse

import cfg


def init():
    """Initialize the system module"""
    cfg.main_menu.add_item(_('System'), 'icon-cog', '/sys', 100)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'system.html',
                            {'title': _('System Configuration')})
