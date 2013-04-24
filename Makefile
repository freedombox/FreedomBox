MAKE=make

CSS=$(wildcard *.css)
CSS=$(subst .tiny,,$(shell find themes -type f -name '*.css'))
COMPRESSED_CSS := $(patsubst %.css,%.tiny.css,$(CSS))
PWD=`pwd`

# hosting variables
SLEEP_TIME=300
EXCLUDE=--exclude=*.tar.gz --exclude=*~ $(EXCLUDE-FILES)
ALL_BUT_GZ=$(subst $(wildcard *.tar.gz),,$(wildcard *))

## Catch-all tagets
default: predepend config dirs template css docs dbs
all: default

predepend:
	sudo sh -c "apt-get install augeas-tools python-bjsonrpc python-augeas python-simplejson pandoc python-cheetah python-cherrypy3"
	git submodule init
	git submodule update
	touch predepend

install: default
	mkdir -p $(DESTDIR)/etc/init.d $(DESTDIR)/etc/plinth
	cp plinth.sample.fhs.config $(DESTDIR)/etc/plinth/plinth.config
	mkdir -p $(DESTDIR)/usr/lib/python2.7/plinth $(DESTDIR)/usr/bin \
		$(DESTDIR)/usr/share/doc/plinth $(DESTDIR)/usr/share/man/man1
	rsync -L doc/* $(DESTDIR)/usr/share/doc/plinth/
	gzip $(DESTDIR)/usr/share/doc/plinth/plinth.1 
	mv $(DESTDIR)/usr/share/doc/plinth/plinth.1.gz $(DESTDIR)/usr/share/man/man1
	rsync -rl *.py modules templates vendor themes static \
		--exclude static/doc --exclude ".git/*" --exclude "*.pyc" \
		$(DESTDIR)/usr/lib/python2.7/plinth
	mkdir -p $(DESTDIR)/usr/lib/python2.7/plinth/static/doc
	cp doc/*.html $(DESTDIR)/usr/lib/python2.7/plinth/static/doc
	rm -f $(DESTDIR)/usr/lib/python2.7/plinth/plinth.config
	ln -s ../../../../etc/plinth/plinth.config $(DESTDIR)/usr/lib/python2.7/plinth/plinth.config
	cp share/init.d/plinth $(DESTDIR)/etc/init.d
	rm -f $(DESTDIR)/usr/bin/plinth
	ln -s ../lib/python2.7/plinth/plinth.py $(DESTDIR)/usr/bin/plinth
	mkdir -p $(DESTDIR)/var/lib/plinth/cherrypy_sessions $(DESTDIR)/var/log/plinth $(DESTDIR)/var/run
	cp -r data/* $(DESTDIR)/var/lib/plinth
	rm -f $(DESTDIR)/var/lib/plinth/users/sqlite3.distrib

uninstall:
	rm -rf $(DESTDIR)/usr/lib/python2.7/plinth $(DESTDIR)/usr/share/plinth/ \
		$(DESTDIR)/etc/plinth $(DESTDIR)/var/lib/plinth $(DESTDIR)/usr/share/doc/plinth/ \
		$(DESTDIR)/var/log/plinth
	rm -f $(DESTDIR)/usr/bin/plinth $(DESTDIR)/etc/init.d/plinth \
		$(DESTDIR)/usr/share/man/man1/plinth.1.gz $(DESTDIR)/var/run/plinth.pid

dbs: data/users.sqlite3

data/users.sqlite3: data/users.sqlite3.distrib
	cp data/users.sqlite3.distrib data/users.sqlite3

dirs:
	@mkdir -p data/cherrypy_sessions

config: Makefile
	@test -f plinth.config || cp plinth.sample.config plinth.config

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

hosting:
	bash start.sh &
	while [ 1 ]; do make current-checkout.tar.gz current-repository.tar.gz; sleep $(SLEEP_TIME); done

current-checkout.tar.gz: $(ALL_BUT_GZ)
	tar cz $(EXCLUDE) * > current-checkout.tar.gz

current-repository.tar.gz: $(ALL_BUT_GZ)
	tar cz $(EXCLUDE) * .git > current-repository.tar.gz
