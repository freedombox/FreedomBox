DJANGO_ADMIN := django-admin
INSTALL := install
PYTHON := python3
PYTEST_ARGS :=
CP_ARGS := --no-dereference --preserve=mode,timestamps --reflink=auto

ENABLED_APPS_PATH := $(DESTDIR)/usr/share/freedombox/modules-enabled

DISABLED_APPS_TO_REMOVE := \
    apps \
    coquelicot \
    diaspora \
    monkeysphere \
    owncloud \
    system \
    xmpp \
    disks \
    udiskie \
    restore \
    repro \
    tahoe \
    mldonkey

APP_FILES_TO_REMOVE := $(foreach app,$(DISABLED_APPS_TO_REMOVE),$(ENABLED_APPS_PATH)/$(app))

REMOVED_FILES := \
    $(DESTDIR)/etc/apt/preferences.d/50freedombox3.pref \
    $(DESTDIR)/etc/apache2/sites-available/plinth.conf \
    $(DESTDIR)/etc/apache2/sites-available/plinth-ssl.conf \
    $(DESTDIR)/etc/security/access.d/10freedombox-performance.conf \
    $(DESTDIR)/etc/security/access.d/10freedombox-security.conf

DIRECTORIES_TO_CREATE := \
    $(DESTDIR)/var/lib/plinth \
    $(DESTDIR)/var/lib/plinth/sessions

STATIC_FILES_DIRECTORY := $(DESTDIR)/usr/share/plinth/static
BIN_DIR := $(DESTDIR)/usr/bin

FIND_ARGS := \
    -not -iname "*.log" \
    -not -iname "*.pid" \
    -not -iname "*.py.bak" \
    -not -iname "*.pyc" \
    -not -iname "*.pytest_cache" \
    -not -iname "*.sqlite3" \
    -not -iname "*.swp" \
    -not -iname "\#*" \
    -not -iname ".*" \
    -not -iname "sessionid*" \
    -not -iname "~*" \
    -not -iname "django-secret.key"


ROOT_DATA_FILES := $(shell find data -type f $(FIND_ARGS))
MODULE_DATA_FILES := $(shell find $(wildcard plinth/modules/*/data) -type f $(FIND_ARGS))

update-translations:
	cd plinth; $(DJANGO_ADMIN) makemessages --all --domain django --keep-pot --verbosity=1

configure:
	# Nothing to do

build:
	# Compile translations
	$(DJANGO_ADMIN) compilemessages --verbosity=1

	# Build documentation
	$(MAKE) -C doc -j 8

	# Build .whl package
	$(PYTHON) -m build --no-isolation --skip-dependency-check --wheel

install:
	# Drop removed apps
	rm -f $(APP_FILES_TO_REMOVE)

	# Drop removed configuration files
	rm -f $(REMOVED_FILES)

	# Create data directories
	for directory in $(DIRECTORIES_TO_CREATE) ; do \
	    $(INSTALL) -d $$directory ; \
	done

	# Python package
	temp=$$(mktemp -d) && \
        lib_dir=$$($(PYTHON) -c 'import sysconfig; print(sysconfig.get_paths(scheme="deb_system")["purelib"])') && \
	$(PYTHON) -m pip install dist/plinth-*.whl --break-system-packages \
            --no-deps --no-compile --no-warn-script-location \
            --ignore-installed --target=$${temp} && \
        $(INSTALL) -d $(DESTDIR)$${lib_dir} && \
	rm -rf $(DESTDIR)$${lib_dir}/plinth $(DESTDIR)$${lib_dir}/plinth*.dist-info && \
        mv $${temp}/plinth $${temp}/plinth*.dist-info $(DESTDIR)$${lib_dir} && \
	rm -f $(DESTDIR)$${lib_dir}/plinth*.dist-info/COPYING.md && \
	rm -f $(DESTDIR)$${lib_dir}/plinth*.dist-info/direct_url.json && \
        $(INSTALL) -D -t $(BIN_DIR) bin/plinth

	# Actions
	$(INSTALL) -D -t $(DESTDIR)/usr/share/plinth/actions actions/actions

	# Static web server files
	rm -rf $(STATIC_FILES_DIRECTORY)
	$(INSTALL) -d $(STATIC_FILES_DIRECTORY)
	cp $(CP_ARGS) --recursive static/* $(STATIC_FILES_DIRECTORY)

	# System data files
	for file in $(ROOT_DATA_FILES) ; do \
	    target=$$(dirname $(DESTDIR)$$(echo $${file} | sed -e 's|^data||')) ; \
	    $(INSTALL) --directory --mode=755 $${target} ; \
	    cp $(CP_ARGS) $${file} $${target} ; \
	done
	for file in $(MODULE_DATA_FILES) ; do \
	    target=$$(dirname $(DESTDIR)$$(echo $${file} | sed -e 's|^plinth/modules/[^/]*/data||')) ; \
	    $(INSTALL) --directory --mode=755 $${target} ; \
	    cp $(CP_ARGS) $${file} $${target} ; \
	done

	# Documentation
	$(MAKE) -C doc install

check:
	$(PYTHON) -m pytest $(PYTEST_ARGS)

clean:
	make -C doc clean
	rm -rf Plinth.egg-info
	find plinth/locale -name *.mo -delete

.PHONY: update-translations configure build install check clean
