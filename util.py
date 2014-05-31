import os
import sys
import cherrypy
import cfg
import sqlite3

from django.template.loader import render_to_string
from filedict import FileDict


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
def is_string(obj):
    isinstance(obj, basestring)
def is_ascii(s):
    return all(ord(c) < 128 for c in s)
def is_alphanumeric(string):
    for c in string:
        o = ord(c)
        if not o in range(48, 58) + range(41, 91) + [95] + range(97, 123):
            return False
    return True

def slurp(filespec):
    with open(filespec) as x: f = x.read()
    return f

def unslurp(filespec, msg):
    with open(filespec, 'w') as x:
        x.write(msg)

def find_in_seq(func, seq):
  "Return first item in seq for which func(item) returns True."
  for i in seq:
    if func(i):
      return i

def find_keys(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.iteritems() if v == val]

class Message():
    def __init__(self, msg=''):
        self.text = msg
    def add(self, text):
        self.text += "<br />%s" % text


def render_template(template='login_nav', **kwargs):
    for key in ['sidebar_left', 'sidebar_right', 'main', 'js', 'nav', 'css',
                'title', 'basehref']:
        if not key in kwargs:
            kwargs[key] = ''

    if kwargs['basehref'] == '':
        kwargs['basehref'] = cfg.server_dir

    kwargs['template'] = template
    kwargs['main_menu'] = cfg.main_menu
    kwargs['submenu'] = cfg.main_menu.active_item()
    kwargs['current_url'] = cherrypy.url()
    kwargs['username'] = cherrypy.session.get(cfg.session_key)
    kwargs['cfg'] = cfg

    return render_to_string(template + '.html', kwargs)


def filedict_con(filespec=None, table='dict'):
    """TODO: better error handling in filedict_con"""
    try:
        return FileDict(connection=sqlite3.connect(filespec), table=table)
    except IOError as (errno, strerror):
        cfg.log.critical("I/O error({0}): {1}".format(errno, strerror))
        sys.exit(-1)
