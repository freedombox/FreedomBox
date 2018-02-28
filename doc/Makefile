#!/usr/bin/make -f
#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

MANUAL_URL="https://wiki.debian.org/FreedomBox/Manual?action=show&mimetype=text%2Fdocbook"

OUTPUTS=freedombox-manual.pdf freedombox-manual.html freedombox-manual.part.html plinth.1

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

all: $(OUTPUTS)

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
.PHONY: fetch
fetch:
	wget --quiet -O - $(MANUAL_URL) | \
	  xmllint --format --output freedombox-manual.raw.xml -
	xsltproc --output freedombox-manual.xml fixes.xslt freedombox-manual.raw.xml
	xsltproc fetch-images.xslt freedombox-manual.raw.xml | sort -u | \
	  awk '{print "wget --quiet -O images/" $$1 " " $$2}' | sh
	rm -f freedombox-manual.raw.xml


%.pdf: %.xml
	xmlto $(XMLTO_DEBUG_FLAGS) --with-dblatex pdf $<


%.part.html: %.html
	perl -pe 'BEGIN {undef $$/} s/.*<body[^>]*>(.*)<\/body\s*>.*/$$1/si' $< > $@


%.html: %.xml
	docbook2html --nochunks $<


%.1: %.xml
	xmlto man $<


.PHONY: clean
clean:
	rm -f $(OUTPUTS)
