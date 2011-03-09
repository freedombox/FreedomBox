MAKE=make

#TODO: add install target

CSS=$(wildcard *.css)
CSS=$(subst .tiny,,$(shell find themes -type f -name '*.css'))
COMPRESSED_CSS := $(patsubst %.css,%.tiny.css,$(CSS))

## Catch-all tagets
default: template docs css dirs
all: default

dirs:
	mkdir -p data/cherrypy_sessions

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
	@find themes -name "*.tiny.css" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;
	@find . -name ".#*" -exec rm {} \;
	@find . -name "#*" -exec rm {} \;
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*.bak" -exec rm {} \;
	@$(MAKE) -s -C doc clean
	@$(MAKE) -s -C templates clean
