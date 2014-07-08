from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth import cfg


def init():
    """Initailize the apps module"""
    cfg.main_menu.add_urlname("Apps", "icon-download-alt", "apps:index", 80)


def index(request):
    """Serve the apps index page"""
    return TemplateResponse(request, 'apps.html', {'title': _('Applications')})
