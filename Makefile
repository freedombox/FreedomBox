#SHELL := /bin/bash
MAKE=make
BUILDDIR = vendor
DESTDIR = debian

CSS=$(wildcard *.css)
CSS=$(subst .tiny,,$(shell find themes -type f -name '*.css'))
COMPRESSED_CSS := $(patsubst %.css,%.tiny.css,$(CSS))
PWD=`pwd`

## Catch-all tagets
default: predepend config dirs template css docs dbs $(BUILDDIR)/exmachina #$(BUILDDIR)/bjsonrpc
all: default

build:
	@mkdir -p $(BUILDDIR)

predepend:
	sudo sh -c "apt-get install augeas-tools python-bjsonrpc python-augeas python-simplejson pandoc python-cheetah python-cherrypy3"
	touch predepend

$(BUILDDIR)/exmachina: build
	@test -d $@ || git clone git://github.com/tomgalloway/exmachina $@
	#@cd $@; git pull

$(BUILDDIR)/bjsonrpc: build
	@test -d $@ || git clone git://github.com/deavid/bjsonrpc.git $@
	#@cd $@; git pull

$(BUILDDIR)/withsqlite: build
	@test -d $@ || git clone git://github.com/jvasile/withsqlite.git $@
	#@cd $@; git pull

install: default
	mkdir -p $(DESTDIR)/etc/init.d $(DESTDIR)/etc/plinth
	cp plinth.sample.fhs.config $(DESTDIR)/etc/plinth/plinth.config
	mkdir -p $(DESTDIR)/usr/lib/python2.7/plinth $(DESTDIR)/usr/share/plinth/ $(DESTDIR)/usr/bin $(DESTDIR)/usr/share/doc/plinth $(DESTDIR)/usr/share/man/man1
	cp -L doc/* $(DESTDIR)/usr/share/doc/plinth/
	gzip $(DESTDIR)/usr/share/doc/plinth/plinth.1 
	mv $(DESTDIR)/usr/share/doc/plinth/plinth.1.gz $(DESTDIR)/usr/share/man/man1
	cp -r *.py modules templates vendor static $(DESTDIR)/usr/lib/python2.7/plinth
	rm -f $(DESTDIR)/usr/lib/python2.7/plinth/plinth.config
	ln -s ../../../../etc/plinth/plinth.config $(DESTDIR)/usr/lib/python2.7/plinth/plinth.config
	cp -r themes $(DESTDIR)/usr/share/plinth
	cp share/init.d/plinth $(DESTDIR)/etc/init.d
	rm -f $(DESTDIR)/usr/bin/plinth
	ln -s ../lib/python2.7/plinth/plinth.py $(DESTDIR)/usr/bin/plinth
	rm -rf $(DESTDIR)/usr/lib/python2.7/plinth/vendor/*/.git
	cd $(DESTDIR)/usr/lib/python2.7/plinth; find -name '*.pyc' -exec rm {} \;
	rm -rf $(DESTDIR)/usr/lib/python2.7/plinth/vendor/*/.git
	mkdir -p $(DESTDIR)/var/lib/plinth/cherrypy_sessions
	cp -r data/* $(DESTDIR)/var/lib/plinth
	rm -f $(DESTDIR)/var/lib/plinth/users/sqlite3.distrib

uninstall:
	rm -rf $(DESTDIR)/usr/lib/python2.7/plinth $(DESTDIR)/usr/share/plinth/ $(DESTDIR)/etc/plinth $(DESTDIR)/var/lib/plinth $(DESTDIR)/usr/share/doc/plinth/
	rm -f $(DESTDIR)/usr/bin/plinth $(DESTDIR)/etc/init.d/plinth $(DESTDIR)/usr/share/man/man1/plinth.1.gz

dbs: data/users.sqlite3

data/users.sqlite3: data/users.sqlite3.distrib
	cp data/users.sqlite3.distrib data/users.sqlite3

dirs:
	@mkdir -p data/cherrypy_sessions

config: Makefile
	@test -f plinth.config || cp plinth.sample.config plinth.config

cherrypy.config: Makefile
	@echo [global]\\n\
server.socket_host = \'0.0.0.0\'\\n\
server.socket_port = 8000\\n\
server.thread_pool = 10\\n\
tools.staticdir.root = \"$(PWD)\"\\n\
tools.sessions.on = True\\n\
tools.auth.on = True\\n\
tools.sessions.storage_type = \"file\"\\n\
tools.sessions.timeout = 90\\n\
tools.sessions.storage_path = \"$(PWD)/data/cherrypy_sessions\"\\n\
\\n\
[/static]\\n\
tools.staticdir.on = True\\n\
tools.staticdir.dir = \"static\"\\n\
\\n\
[/favicon.ico]\\n\
tools.staticfile.on = True\\n\
tools.staticfile.filename = \"$(PWD)/static/theme/favicon.ico\"\\n\
> cherrypy.config

%.tiny.css: %.css
	@cat $< | python -c 'import re,sys;print re.sub("\s*([{};,:])\s*", "\\1", re.sub("/\*.*?\*/", "", re.sub("\s+", " ", sys.stdin.read())))' > $@
css: $(COMPRESSED_CSS)

template:
	@$(MAKE) -s -C templates
templates: template

docs:
	@$(MAKE) -s -C doc
doc: docs

html:
	@$(MAKE) -s -C doc html

clean:
	@rm -f cherrypy.config data/cherrypy_sessions/*
	@find themes -name "*.tiny.css" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;
	@find . -name ".#*" -exec rm {} \;
	@find . -name "#*" -exec rm {} \;
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*.bak" -exec rm {} \;
	@$(MAKE) -s -C doc clean
	@$(MAKE) -s -C templates clean
	rm -rf $(BUILDDIR) $(DESTDIR)
	rm -f predepend
