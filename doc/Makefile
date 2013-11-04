DOCDIR=../dist/doc

PANDOC=pandoc
PDFLATEX=pdflatex


# List text files in the order in which you want them to appear in the
# complete manual:
SOURCES=README.mdwn INSTALL.mdwn themes.mdwn hacking.mdwn TODO.mdwn modules.mdwn scripts.mdwn security.mdwn faq.mdwn COPYING.mdwn colophon.mdwn
OTHER=
TODO_SOURCES=$(patsubst TODO.mdwn,,$(SOURCES))
MAN_SOURCES=$(patsubst COPYING.mdwn,copyright_notice00,$(SOURCES))

NEWLINE_SOURCES=$(patsubst %,% oneline.txt,$(SOURCES))
NEWLINE_MAN_SOURCES=$(patsubst %,% oneline.txt,$(MAN_SOURCES))

HTML=plinth.html $(patsubst %.mdwn,%.html,$(SOURCES))
HTML_PART=$(patsubst %.html,%.part.html,$(HTML))
LATEX=plinth.tex $(patsubst %.mdwn,%.tex,$(SOURCES))
PDF=plinth.pdf $(patsubst %.mdwn,%.pdf,$(SOURCES))
MAN=plinth.1

## If you want PDF or Latex files, do them separately.  They're not made by default.

OUTPUTS=$(HTML) $(MAN) $(HTML_PART)
DIST_OUTPUT=$(patsubst %,$(DOCDIR)/%,$(OUTPUTS))

# Yes, do it twice. TODO created during the process requires a second run
default:
	make all
all: oneline.txt $(OUTPUTS) Makefile

$(DOCDIR)/%: %
	cp $< $@
dist: $(DIST_OUTPUT)
###############################################################################
oneline.txt: Makefile
	perl -e 'print "\n"' > oneline.txt

$(SOURCES):
	@rm -f $@
	@ln -s ../$(patsubst %.mdwn,%,$@) $@

../TODO : $(TODO_SOURCES) ../*.py ../modules/*.py ../Makefile Makefile ../templates/Makefile
	grep -ro --exclude=.git* --exclude=plinth.1 --exclude=*.tex --exclude=*.html \
	     --exclude=README.mdwn --exclude=INSTALL.mdwn \
	     --exclude=TODO.mdwn --exclude=COPYING.mdwn \
	     "TODO\:.*" ../* 2>/dev/null | \
	     sed -e "s/TODO\://g" | \
	     sed -e "s/^..\//* /g" | \
	     sed -e 's/"""$$//g' | \
	     sed -e 's/<\/p>$$//g' \
	     > ../TODO
###############################################################################
##
## MAN PAGES
##
$(MAN): $(SOURCES) ../TODO
	@csplit -s -f copyright_notice COPYING.mdwn '/##/'
	cat $(NEWLINE_MAN_SOURCES) | perl -pe 'BEGIN { $$/=undef } $$_ =~ s/\n\n#\s.*/\n/gm; $$_ =~ s/\n\n#/\n\n/gm; $$_ =~ s/(\n\n#\s.*)/uc($$1)/gme' > .make_man
	$(PANDOC) -s -t man -o $@ .make_man
	@rm -f copyright_notice0? .make_man
manpages: $(MAN)
###############################################################################
##
## LaTeX
##
%.tex: %.mdwn
	$(PANDOC) -s --toc -f markdown --standalone -o $@ $<

hacking.tex: hacking.mdwn ../TODO
	$(PANDOC) -s --toc -f markdown -o $@ hacking.mdwn ../TODO

plinth.tex: $(NEWLINE_SOURCES) ../TODO
	$(PANDOC) -s --toc -f markdown -o $@ $(NEWLINE_SOURCES)

latex: $(LATEX)
###############################################################################
##
## HTML
##


# This gets us the html sections complete with TOC, but without the
# HTML and head section boilerplate.  /help/view uses the parts.
%.part.html: %.html
	csplit -s -f $@ $< '%.*<body>%'
	sed '1d' $@00 > $@01
	csplit -s -f $@ $@01 '/<\/body>/'
	mv $@00 $@
	rm $@01
%.html: %.mdwn header.html footer.html style.css Makefile
	$(PANDOC) -s --toc -c style.css -f markdown -o $@ header.html $< footer.html

hacking.html: hacking.mdwn ../TODO style.css Makefile
	$(PANDOC) -s --toc -c style.css -o $@ -f markdown hacking.mdwn ../TODO

#plinth.html: $(NEWLINE_SOURCES) ../TODO style.css Makefile
#	$(PANDOC) -s --toc -c style.css -o $@ -f markdown $(NEWLINE_SOURCES)

plinth.html: $(NEWLINE_SOURCES) ../TODO style.css Makefile
	@csplit -s -f copyright_notice COPYING.mdwn '/##/'
	$(PANDOC) -s --toc -c style.css -o $@ -f markdown $(NEWLINE_MAN_SOURCES)
	@rm -f copyright_notice0? .make_man

html: $(HTML) $(HTML_PART)
###############################################################################
%.pdf: %.tex
	$(PDFLATEX) -interaction=batchmode $< >/dev/null
	$(PDFLATEX) -interaction=batchmode $< >/dev/null  # yes, do it twice so the toc works

pdf: $(PDF)
###############################################################################

clean-latex:
	rm -f *.log *.out *.aux *.toc *.tex

clean: clean-latex
	rm -f $(OUTPUTS) README.mdwn INSTALL.mdwn TODO.mdwn COPYING.mdwn \
	     copyright_notice0? \#*\# ../TODO oneline.txt *.pdf
