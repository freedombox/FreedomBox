from django.template.response import TemplateResponse
from gettext import gettext as _

import cfg


def init():
    """Initailize the apps module"""
    cfg.main_menu.add_item("Apps", "icon-download-alt", "/apps", 80)


def index(request):
    """Serve the apps index page"""
    return TemplateResponse(request, 'apps.html', {'title': _('Applications')})
