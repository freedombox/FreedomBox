import os
from gettext import gettext as _
from django.template.response import TemplateResponse

import cfg


def init():
    """Initialize the Help module"""
    menu = cfg.main_menu.add_item(_('Documentation'), 'icon-book', '/help',
                                  101)
    menu.add_item(_("Where to Get Help"), "icon-search", "/help/index", 5)
    menu.add_item(_('Developer\'s Manual'), 'icon-info-sign',
                  '/help/view/plinth', 10)
    menu.add_item(_('FAQ'), 'icon-question-sign', '/help/view/faq', 20)
    menu.add_item(_('%s Wiki' % cfg.box_name), 'icon-pencil',
                  'http://wiki.debian.org/FreedomBox', 30)
    menu.add_item(_('About'), 'icon-star', '/help/about', 100)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help.html',
                            {'title': _('Documentation and FAQ')})


def about(request):
    """Serve the about page"""
    title = _('About the {box_name}').format(box_name=cfg.box_name)
    return TemplateResponse(request, 'about.html', {'title': title})


def default(request, page=''):
    """Serve the documentation pages"""
    with open(os.path.join('doc', '%s.part.html' % page), 'r') as input_file:
        main = input_file.read()

    title = _('%s Documentation') % cfg.product_name
    return TemplateResponse(request, 'base.html',
                            {'title': title, 'main': main})
