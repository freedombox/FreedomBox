#SHELL := /bin/bash
MAKE=make
BUILD_DIR = build

#TODO: add install target

CSS=$(wildcard *.css)
CSS=$(subst .tiny,,$(shell find themes -type f -name '*.css'))
COMPRESSED_CSS := $(patsubst %.css,%.tiny.css,$(CSS))
PWD=`pwd`

## Catch-all tagets
default: predepend cfg cherrypy.config dirs template css docs dbs $(BUILD_DIR)/exmachina #$(BUILD_DIR)/bjsonrpc
all: default

build:
	mkdir -p $(BUILD_DIR)

predepend:
	sudo sh -c "apt-get install augeas-tools python-bjsonrpc python-augeas python-simplejson pandoc python-cheetah"
	touch predepend

$(BUILD_DIR)/exmachina: build
	git clone git://github.com/tomgalloway/exmachina $(BUILD_DIR)/exmachina

$(BUILD_DIR)/bjsonrpc: build
	git clone git://github.com/deavid/bjsonrpc.git $(BUILD_DIR)/bjsonrpc

dbs: data/users.sqlite3

data/users.sqlite3: data/users.sqlite3.distrib
	cp data/users.sqlite3.distrib data/users.sqlite3

dirs:
	@mkdir -p data/cherrypy_sessions

cfg: Makefile
	test -f cfg.py || cp cfg.sample.py cfg.py

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
	rm -rf $(BUILD_DIR)
	rm -f predepend
