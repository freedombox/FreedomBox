import os
from gettext import gettext as _
from django.http import Http404
from django.template.response import TemplateResponse

from plinth import cfg


def init():
    """Initialize the Help module"""
    menu = cfg.main_menu.add_urlname(_('Documentation'), 'glyphicon-book',
                                     'help:index', 110)
    menu.add_urlname(_("Where to Get Help"), "glyphicon-search",
                     "help:index_explicit", 5)
    menu.add_urlname(_('Developer\'s Manual'), 'glyphicon-info-sign',
                     'help:helppage', 10, url_args=('plinth',))
    menu.add_urlname(_('FAQ'), 'glyphicon-question-sign', 'help:helppage', 20,
                     url_args=('faq',))
    menu.add_item(_('%s Wiki' % cfg.box_name), 'glyphicon-pencil',
                  'http://wiki.debian.org/FreedomBox', 30)
    menu.add_urlname(_('About'), 'glyphicon-star', 'help:about', 100)


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
        with open(os.path.join(cfg.doc_dir, '%s.part.html' % page), 'r') \
                as input_file:
            main = input_file.read()
    except IOError:
        raise Http404

    title = _('%s Documentation') % cfg.product_name
    return TemplateResponse(request, 'base.html',
                            {'title': title, 'main': main})
