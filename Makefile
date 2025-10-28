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
    mldonkey \
    i2p

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
LIB_DIR := $(DESTDIR)/usr/lib

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
    -not -iname "django-secret.key" \
    -not -iwholename "*/.mypy_cache/*"


ROOT_DATA_FILES := $(shell find data -type f $(FIND_ARGS))
MODULE_DATA_FILES := $(shell find $(wildcard plinth/modules/*/data) -type f $(FIND_ARGS))

update-translations:
	$(DJANGO_ADMIN) makemessages --all --domain django --keep-pot \
		--verbosity=1 --ignore conftest.py --ignore doc --ignore build \
		--ignore htmlcov --ignore screenshots --ignore debian --ignore \
		actions --ignore preseed --ignore static --ignore data \
		--settings plinth.settings --pythonpath .

configure:
	# Nothing to do

build:
	# Compile translations
	$(DJANGO_ADMIN) compilemessages --verbosity=1

	# Build documentation
	$(MAKE) -C doc -j 8

	# Build .whl package
	rm -f dist/plinth-*.whl
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
	$(INSTALL) -D -t $(LIB_DIR)/freedombox bin/freedombox-privileged
	$(INSTALL) -D -t $(BIN_DIR) bin/freedombox-cmd

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

check: check-type check-code check-doc check-tests

# Run the main test suite
check-tests:
	$(PYTHON) -m pytest $(PYTEST_ARGS)

# Tests with coverage report
check-tests-cov:
	$(PYTHON) -m pytest $(PYTEST_ARGS) --cov=plinth \
	    --cov-report=html:./htmlcov --cov-report=term

# Code quality checking using flake8
check-code:
	$(PYTHON) -m flake8 plinth container

# Static type checking using mypy
check-type:
	$(PYTHON) -m mypy .

# Use doctest for check the wikiparser in doc directory
check-doc:
	$(PYTHON) -m doctest doc/scripts/wikiparser.py

clean:
	make -C doc clean
	rm -rf Plinth.egg-info
	find plinth/locale -name *.mo -delete

define DEVELOP_SERVICE_CONF
[Service]
Environment=FREEDOMBOX_DEVELOP=1
Environment=PYTHONPATH=/freedombox/
endef
export DEVELOP_SERVICE_CONF

define DEVELOP_LOGS_SCRIPT
#!/usr/bin/bash

set -e
set -x

journalctl --follow --unit=plinth.service --unit=freedombox-privileged.service
endef
export DEVELOP_LOGS_SCRIPT

# Run basic setup for a developer environment (VM or container)
provision-dev:
	# Install newer build dependencies if any
	apt-get update
	DEBIAN_FRONTEND=noninteractive apt-get build-dep --yes .

	# Install latest code over .deb
	$(MAKE) build install

	# Configure privileged and web daemon for development setup
	mkdir -p /etc/systemd/system/freedombox-privileged.service.d/
	echo "$$DEVELOP_SERVICE_CONF" > /etc/systemd/system/freedombox-privileged.service.d/develop.conf
	mkdir -p /etc/systemd/system/plinth.service.d/
	echo "$$DEVELOP_SERVICE_CONF" > /etc/systemd/system/plinth.service.d/develop.conf

	# Create a command to easily watch service logs
	echo "$$DEVELOP_LOGS_SCRIPT" > /usr/bin/freedombox-logs
	chmod 755 /usr/bin/freedombox-logs

	# Reload newer systemd units, ignore failure
	-systemctl daemon-reload

	# Enable privileged daemon
	-systemctl stop freedombox-privileged.service

	-test -d /run/systemd/system && \
		systemctl enable --now freedombox-privileged.socket

	# Enable and restart plinth service if it is running
	-systemctl enable plinth.service
	-systemctl restart plinth.service

	# Stop any ongoing upgrade, ignore failure
	-killall -9 unattended-upgr

	# Fix any broken packages
	dpkg --configure -a
	apt-get -f install
	apt-get update

	# Install new packages needed by essential apps. Don't uninstall
	# freedombox in case new dependencies conflict with old dependencies
	apt-mark hold freedombox
	DEBIAN_FRONTEND=noninteractive apt-get install --no-upgrade --yes \
	    $$(sudo -u plinth ./run --develop --list-dependencies)
	apt-mark unhold freedombox

	# DNS resolution may be broken by upgrade to systemd-resolved. See
	# #1079819 and ##1032937.
	-systemctl restart systemd-resolved
	-nmcli general reload dns-rc

	# Install additional packages
	DEBIAN_FRONTEND=noninteractive apt-get install --yes ncurses-term \
	    sshpass bash-completion

wait-while-first-setup:
	while [ x$$(curl -k https://localhost/plinth/status/ 2> /dev/null | \
	    json_pp 2> /dev/null | grep 'is_first_setup_running' | \
            tr -d '[:space:]' | cut -d':' -f2 ) != 'xfalse' ] ; do \
	    sleep 1; echo -n .; done

.PHONY: \
    build \
    check \
    check-code \
    check-doc \
    check-type \
    check-tests \
    check-tests-cov \
    clean \
    configure \
    install \
    provision \
    update-translations \
    wait-while-first-setup
