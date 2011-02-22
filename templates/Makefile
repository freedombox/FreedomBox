CHEETAH=cheetah
TEMPLATES=$(wildcard *.tmpl)
TEMPLATE_PYFILES := $(patsubst %.tmpl,%.py,$(TEMPLATES))

## Catch-all tagets
default: $(TEMPLATE_PYFILES)

%.py: %.tmpl
	$(CHEETAH) c $<
templates: $(TEMPLATE_PYFILES)
template: templates

clean:
	rm -rf .\#* \#* *.pyz *.bak
	@rm -f $(TEMPLATE_PYFILES)
