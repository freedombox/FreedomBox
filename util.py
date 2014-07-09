import os
from django.http.response import HttpResponseRedirect
import cfg


class PlinthRedirect(HttpResponseRedirect):
    """
    We do not fully use django and thus cannot use its named URLs to construct
    links/redirects, so we have to take care of cfg.server_dir manually.
    This temporary helper class makes sure that plinth-internal redirects
    have the correct server_dir prefix.
    """
    def __init__(self, redirect_to, *args, **kwargs):
        if not redirect_to.startswith(cfg.server_dir):
            redirect_to = rel_urljoin([cfg.server_dir, redirect_to])
        return super(PlinthRedirect, self).__init__(redirect_to,
                                                    *args, **kwargs)


def rel_urljoin(parts, prepend_slash=True):
    """
    urllibs' urljoin joins ("foo", "/bar") to "/bar".
    Instead concatenate the parts with "/" to i.e. /foo/bar
    """
    url =  '/'.join(s.strip('/') for s in parts)
    if prepend_slash and not url.startswith('/'):
        url = '/' + url
    return url


def mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir(head)
        #print "mkdir %s" % repr(newdir)
        if tail:
            os.mkdir(newdir)


def slurp(filespec):
    with open(filespec) as x: f = x.read()
    return f


def unslurp(filespec, msg):
    with open(filespec, 'w') as x:
        x.write(msg)
