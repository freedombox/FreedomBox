import logging
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect

from withsqlite.withsqlite import sqlite_db
import cfg


LOGGER = logging.getLogger(__name__)


class FirstBootMiddleware:
    """ Forward to firstboot page if firstboot isn't finished yet """
    def process_request(self, request):
        with sqlite_db(cfg.store_file, table='firstboot') as database:
            if not 'state' in database:
                # Permanent redirect causes the browser to cache the redirect,
                # preventing the user from navigating to /plinth until the
                # browser is restarted.
                return HttpResponseRedirect(reverse('first_boot:index'))

            if database['state'] < 5:
                LOGGER.info('First boot state - %d', database['state'])
                return HttpResponseRedirect(reverse('first_boot:state%d' %
                                                    database['state']))
