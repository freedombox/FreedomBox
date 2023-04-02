#!/bin/bash
set -xeuo pipefail
IFS=$'\n\t'

echo "Installing requirements"
sudo apt-get install -yq --no-install-recommends \
    python3-pytest python3-pytest-django python3-pytest-xdist \
    python3-pip python3-wheel firefox-esr git smbclient

# Use compatible versions of Splinter and Selenium
PIP_VERSION=$(dpkg-query -W -f '${Version}' python3-pip)
PIP_OPTIONS=
dpkg --compare-versions 23 \<= $PIP_VERSION && PIP_OPTIONS=--break-system-packages
pip3 install $PIP_OPTIONS selenium==4.2.0 splinter==0.17.0 pytest-splinter pytest-reporter-html1

echo "Installing geckodriver"
(
    DL_DIR=/tmp/gecko
    GECKO_VERSION=$(curl --silent "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep -Po '"tag_name":\s*"\K.*?(?=")')
    FILENAME="geckodriver-${GECKO_VERSION}-linux64.tar.gz"
    GECKO_URL="https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/$FILENAME"

    test -e /usr/local/bin/geckodriver && \
        test "$GECKO_VERSION" = "v$(geckodriver --version | head -1 | awk '{ print $2 }')" && \
        echo "geckodriver already installed" && \
        exit 0

    mkdir -p $DL_DIR
    cd $DL_DIR
    if ! [[ -e $FILENAME ]] ; then
        wget --no-clobber \
            --continue \
            --no-verbose \
            "$GECKO_URL"
    fi
    tar xf $FILENAME
    sudo mv geckodriver /usr/local/bin/geckodriver
    echo "Done"
)
