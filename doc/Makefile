#!/usr/bin/make -f
# SPDX-License-Identifier: AGPL-3.0-or-later

MANUAL_LANGUAGES=en es

MANUAL_URL="https://wiki.debian.org/{lang-fragment}FreedomBox/Manual?action=show&mimetype=text%2Fdocbook"
MANUAL_URL_RAW="https://wiki.debian.org/{lang-fragment}FreedomBox/Manual?action=raw"
MANUAL_PAGE_URL_RAW="https://wiki.debian.org/{page}?action=raw"

INSTALL_DIR=$(DESTDIR)/usr/share/freedombox
MAN_INSTALL_DIR=$(DESTDIR)/usr/share/man
SCRIPTS_DIR=scripts

manual-pdfs=$(foreach lang,$(MANUAL_LANGUAGES),manual/$(lang)/freedombox-manual.pdf)
manual-xmls=$(patsubst %.pdf,%.xml,$(manual-pdfs))
OUTPUTS=$(manual-pdfs) plinth.1

INSTALL_OPTS=-D --mode=644

# In order to debug various problems with the documents especially
# intermediate LaTeX state, run make as follows:
#
#   $ make DEBUG=true
#   or
#   $ make DEBUG=true <target>
#
XMLTO_DEBUG_FLAGS=
ifneq ($(DEBUG),)
	XMLTO_DEBUG_FLAGS=--noclean -p '--debug'
endif

.PHONY: all install
all: $(OUTPUTS) manual-pages

install: all
	install $(INSTALL_OPTS) -t $(MAN_INSTALL_DIR)/man1 plinth.1
	for file in $(manual-pages-part-html) $(manual-pdfs); do \
		install $(INSTALL_OPTS) -t $(INSTALL_DIR)/$$(dirname $${file}) \
			$${file} ; \
	done
	for lang in $(MANUAL_LANGUAGES); do \
		install $(INSTALL_OPTS) manual/$${lang}/images/*.png \
			manual/$${lang}/images/*.jpg \
			-t $(INSTALL_DIR)/manual/$${lang}/images ; \
	done

# Do not edit the manual page in this directory.  The manual is
# maintained as separate pages on the FreedomBox wiki and aggregated
# into a single page using the MoinMoin include feature.  Then it is
# exported as Docbook format and kept here.
#
# It is important to keep a copy of the manual in this source tree
# because Debian packages promise an entire source tree including the
# documentation.
#
# Use 'make fetch' to retrieve the latest manual from the wiki and
# commit it to the repository.  The wiki page is already reviewed, so
# commits that update the manual just using the 'fetch' target do not
# require further reviews.
fetch-main-list:=$(foreach lang,$(MANUAL_LANGUAGES),fetch-main-$(lang))
fetch-pages-list:=$(foreach lang,$(MANUAL_LANGUAGES),fetch-pages-$(lang))
fetch-cleanup-list:=$(foreach lang,$(MANUAL_LANGUAGES),fetch-cleanup-$(lang))

.PHONY: fetch $(fetch-main-list) $(fetch-pages-list) $(fetch-cleanup-list)
fetch: $(fetch-main-list) $(fetch-pages-list)

# Remove raw wiki pages and images before fetching to drop items deleted
# upstream.
fetch-cleanup-%: lang = $*
$(fetch-cleanup-list): fetch-cleanup-%:
	rm -f manual/$(lang)/*.raw.wiki
	rm -f manual/$(lang)/images/*.png manual/$(lang)/images/*.jpg

fetch-main-%: lang = $*
fetch-main-%: lang-fragment = $(subst en/,,$*/)
$(fetch-main-list): fetch-main-%: fetch-cleanup-%
	MANUAL_URL_RAW_LANG=$(subst {lang-fragment},$(lang-fragment),$(MANUAL_URL_RAW)) ; \
	wget --quiet --user-agent=Firefox \
	  -O manual/$(lang)/freedombox-manual.raw.wiki $${MANUAL_URL_RAW_LANG}
	MANUAL_URL_LANG=$(subst {lang-fragment},$(lang-fragment),$(MANUAL_URL)) ; \
	wget --quiet --user-agent=Firefox -O - $${MANUAL_URL_LANG} | \
	  xmllint --format --output manual/$(lang)/freedombox-manual.raw.xml -
	mkdir -p manual/$(lang)/images/
	xsltproc $(SCRIPTS_DIR)/fetch-images.xslt manual/$(lang)/freedombox-manual.raw.xml | \
	  sort -u | \
	  awk 'NF {print "wget --quiet -O manual/$(lang)/images/" $$1 " " $$2}' | \
	  sh -e
	rm manual/$(lang)/freedombox-manual.raw.xml

fetch-pages-%: lang = $*
fetch-pages-%: lang-fragment = $(subst en/,,$*/)
$(fetch-pages-list): fetch-pages-%: fetch-cleanup-%
	MANUAL_URL_LANG=$(subst {lang-fragment},$(lang-fragment),$(MANUAL_URL_RAW)) ; \
	PAGES=$$(wget --quiet --user-agent=Firefox -O - $${MANUAL_URL_LANG} | \
	  sed -n -e "s|.*<<Include(\([a-zA-Z0-9_/+-]*\),.*|\1|p" | sort -u) ; \
	for PAGE in $${PAGES} ; do \
	  PAGE_NAME=$$(basename $${PAGE}) ; \
	  echo "Downloading $(lang) $${PAGE}" ; \
	  RAW_FILE="manual/$(lang)/$${PAGE_NAME}.raw.wiki" ; \
	  RAW_URL=$$(echo $(MANUAL_PAGE_URL_RAW) | sed "s|{page}|$${PAGE}|") ; \
	  wget --quiet --user-agent=Firefox -O $${RAW_FILE} $${RAW_URL} ; \
	done

manual-pages-raw-wiki:=$(foreach lang,$(MANUAL_LANGUAGES),$(filter-out manual/%/freedombox-manual.raw.wiki,$(wildcard manual/$(lang)/*.raw.wiki)))
manual-pages-part-html:=$(patsubst %.raw.wiki, %.part.html, $(manual-pages-raw-wiki)) $(foreach lang,$(MANUAL_LANGUAGES),manual/$(lang)/freedombox-manual.part.html)
manual-pages-xml:=$(patsubst %.raw.wiki, %.xml, $(manual-pages-raw-wiki))

.PHONY: manual-pages
manual-pages: $(manual-pages-part-html)

$(manual-pdfs): %.pdf: %.xml
	xmlto $(XMLTO_DEBUG_FLAGS) --with-dblatex pdf -o $(dir $@) $<

$(manual-pages-part-html): %.part.html: %.xml
	xsltproc /usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml5/docbook.xsl $< | \
	perl -pe 'BEGIN {undef $$/} s/.*<body[^>]*>(.*)<\/body\s*>.*/$$1/si' > $@
	@rm -f $(dir $@)docbook.css

$(manual-xmls) $(manual-pages-xml): %.xml: %.raw.wiki $(SCRIPTS_DIR)/wikiparser.py
	$(SCRIPTS_DIR)/wikiparser.py $< | xmllint --format - > $@

%.1: %.xml
	xmlto man $<

.PHONY: clean
clean:
	rm -f $(manual-pages-part-html) $(manual-pages-xml) $(manual-xmls)
	rm -f $(OUTPUTS)
