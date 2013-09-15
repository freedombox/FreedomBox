#!/usr/bin/env python

# This is the fabric file I've been using to deploy things on my box
# and my freedombox.
#
# fab install should take you from base freedom-maker install to
# plinth box

import os,sys, subprocess
try:
    import simplejson as json
except ImportError:
    import json
import fabric.api
from fabric.api import local, env, cd, put, get, task

import cfg

fb_ip = "10.5.53.155"

BINDIR = "/usr/local/bin"

# defaults
env.user = 'root'

@task
def fb():
   "Use this to set host to our freedombox (e.g.: fab fb deploy)"
   env.hosts = [fb_ip]

@task
def all_hosts():
   "Use this to set host to both localhost and freedombox"
   env.hosts = ["localhost", "192.168.2.115"]

def remote_dir():
   if env.host == fb_ip:
      return "/usr/local/share/plinth"
   else:
      return "/home/james/src/plinth"

def run(*args, **kwargs):
   if env.host == "localhost" or env.host=="127.0.0.1":
      return local(*args, **kwargs)
   else:
      return fabric.api.run(*args, **kwargs)

def sudo(*args, **kwargs):
   if env.host == "localhost" or env.host=="127.0.0.1":
      return run("sudo %s" % args[0], *args[1:], **kwargs)
   elif env.user == "root":
      return run(*args, **kwargs)
   else:
      return fabric.api.sudo(*args, **kwargs)

@task
def get_remote_data_dir():
   with cd(remote_dir()):
      data_dir = run('python -c "import cfg; print cfg.data_dir"')
   env.remote_data_dir = os.path.join(remote_dir(), data_dir)
   sudo('mkdir -p %s' % env.remote_data_dir)
   return env.remote_data_dir

@task
def move_data():
   "Move install's data dir to where cfg specifies it should be"
   get_remote_data_dir()
   with cd(remote_dir()):
      sudo('mv data %s' % os.path.split(env.remote_data_dir)[0])

@task
def make():
   "Run the makefile, which generates docs and templates"
   with cd(remote_dir()):
      sudo('make')

def make_link_unless_exists(src, dest):
   sudo('test -f %s || ln -s %s %s' % (dest, src, dest))

def link(src, dest):
   sudo('ln -fs %s %s' % (src, dest))

@task
def santiago():
   "Setup the Santiago port"
   santiago_port = 52854
   sudo('ifconfig lo up') # or else tor start fails
   sudo('apt-get install -y --no-install-recommends tor curl ntp')

   # tor needs accurate clock
   sudo('date -s "%s"' % subprocess.check_output("date").rstrip())

   # create tor hidden service dir
   santiago_dir = os.path.join(get_remote_data_dir(), "santiago", "tor")
   tor_dir = os.path.join(santiago_dir, "general")
   sudo("mkdir -p " + tor_dir)
   sudo("chown debian-tor:debian-tor " + tor_dir)

   # ensure hidden service config is in torrc
   local("rm -rf __fab__torrc")
   get("/etc/tor/torrc", "__fab__torrc")
   with open ("__fab__torrc", 'r') as INF:
      rc = INF.read()
   local("rm -rf __fab__torrc")
   hidden_service_config = "HiddenServiceDir %s\nHiddenServicePort 80 127.0.0.1:%d" %  (tor_dir, santiago_port)
   if not hidden_service_config in rc:
      sudo("echo '%s' >> /etc/tor/torrc" % hidden_service_config)

   sudo('service tor restart')

def backslash_path(f):
   if not f.startswith('/'):
      f = os.path.abs(f)
   if f == '/':
      return ''
   path, ret = os.path.split(f)
   return backslash_path(path) + '\/' + ret

@task
def apache():
   "configure apache to find reverse proxy for plinth"
   sudo('apt-get install --no-install-recommends -y apache2 libapache2-mod-proxy-html apache2-utils openssl ssl-cert')
   sudo('a2enmod proxy_http rewrite ssl')
   sudo('touch /var/log/apache2/rewrite.log')

   ## ssl key and cert
   ssl_target = "/etc/apache2/ssl/apache.pem"
   sudo('mkdir -p %s' % os.path.split(ssl_target)[0])
   sudo('test -f %s || echo "US\nNY\nNYC\nFBox\n\n\n" | openssl req -new -x509 -days 999 -nodes -out %s -keyout %s' % (ssl_target, ssl_target, ssl_target))

   conf_path = os.path.join(remote_dir(), "share/apache2/plinth.conf")
   sudo("mkdir -p " + os.path.split(conf_path)[0])
   sudo("touch "+ conf_path)
   sudo(r"sed -i 's/\(\s*\)DocumentRoot.*/\1DocumentRoot %s/g' %s" % (
         backslash_path(os.path.join(remote_dir(), "static")),
         conf_path))
   link(conf_path, "/etc/apache2/sites-enabled/plinth.conf")
   sudo('rm -f /etc/apache2/sites-enabled/000-default')
   sudo('service apache2 restart')

@task
def deps():
   "Basic plinth dependencies"
   sudo('apt-get install --no-install-recommends -y python make python-cheetah pandoc python-simplejson python-pyme python-augeas python-bjsonrpc')

@task
def update():
   "Copy modified git-tracked files from this branch to remote"

   with cd(remote_dir()):

      ## Get .fab contents
      sudo("touch .fab")
      fab = run("cat .fab")
      if not fab:
         fab = {}

      ## Make list of files to put
      try:
         fab = json.loads(fab)
      except:
         fab={}
         branch = [a[2:] for a in local("git branch", capture=True).split("\n") if a.startswith('*')][0]
         files = local("git ls-tree -r --name-only %s" % branch, capture=True).split("\n")
      else:
         files = local("git diff --stat " + fab['last_update_from_commit'], capture=True).split("\n")[:-1]
         files = [f.lstrip().split("|")[0].rstrip() for f in files]

   ## Put the files, one by one, respecting directories
   dirs = {}
   for pathspec in files:
         d,fname = os.path.split(pathspec)
         if not d in dirs.keys():
            dirs[d]=[]
         dirs[d].append(pathspec)
   if dirs:
      sudo('mkdir -p %s' % ' '.join([os.path.join(remote_dir(), d) for d in dirs.keys()]))
      for d in dirs:
         for f in dirs[d]:
            if os.path.islink(f):
               linked = local("ls -l %s" % f, capture=True).split("-> ")[1]
               #link(os.path.join(remote_dir(), linked), os.path.join(remote_dir(), d, os.path.basename(f)))
            put(f, os.path.join(remote_dir(), d),mirror_local_mode=True)
            if f.endswith(".py"):
               run("rm -f " + os.path.join(remote_dir(), d, os.path.basename)+"c")

   ## restart
   make()
   sudo('/etc/init.d/plinth restart')

   ## Record activity so we only put changed files next time
   commit = local("git log -n 1", capture=True).split("\n")[0].split(" ")[1]
   fab['last_update_from_commit'] = commit
   with open(".fab", 'w') as OUTF:
      OUTF.write(json.dumps(fab))
   put(".fab", os.path.join(remote_dir(),".fab"))
   local("rm -f .fab")

@task
def link_bin():
   "Link executable and init.d script"
   # todo: set daemon to point to currect binary
   sudo('rm -rf ' + os.path.join(BINDIR, 'plinth.py'))
   link(os.path.join(remote_dir(), "plinth.py"),  os.path.join(BINDIR, 'plinth.py'))
   sudo('rm -rf /etc/init.d/plinth')
   link(os.path.join(remote_dir(), "share/init.d/plinth"),  "/etc/init.d/plinth")

@task
def restart():
   "Run plinth"
   run('/etc/init.d/plinth restart')
@task
def stop():
   "Stop plinth"
   run('/etc/init.d/plinth stop')

@task
def proxy():
    put("proxy_up.py", remote_dir())

@task
def deploy():
   "Deploy plinth"
   deps()
   link_bin()
   santiago()
   update()
   apache()
   
