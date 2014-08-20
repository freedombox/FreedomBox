import os
from gettext import gettext as _
from django.http import Http404
from django.template.response import TemplateResponse

import cfg


def init():
    """Initialize the Help module"""
    menu = cfg.main_menu.add_urlname(_('Documentation'), 'icon-book',
                                     'help:index', 101)
    menu.add_urlname(_('Where to Get Help'), 'icon-search',
                     'help:index_explicit', 5)
    menu.add_urlname(_('Developer\'s Manual'), 'icon-info-sign',
                     'help:helppage', 10, url_args=('plinth',))
    menu.add_urlname(_('FAQ'), 'icon-question-sign', 'help:helppage', 20,
                     url_args=('faq',))
    menu.add_item(_('%s Wiki' % cfg.box_name), 'icon-pencil',
                  'http://wiki.debian.org/FreedomBox', 30)
    menu.add_urlname(_('About'), 'icon-star', 'help:about', 100)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'help.html',
                            {'title': _('Documentation and FAQ')})


def about(request):
    """Serve the about page"""
    title = _('About the {box_name}').format(box_name=cfg.box_name)
    return TemplateResponse(request, 'about.html', {'title': title})


def helppage(request, page):
    """Serve a help page from the 'doc' directory"""
    try:
        with open(os.path.join('doc', '%s.part.html' % page), 'r') \
                as input_file:
            main = input_file.read()
    except IOError:
        raise Http404

    title = _('%s Documentation') % cfg.product_name
    return TemplateResponse(request, 'base.html',
                            {'title': title, 'main': main})
