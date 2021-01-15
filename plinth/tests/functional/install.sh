#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "Installing requirements"
sudo apt-get install -yq --no-install-recommends \
    python3-pytest python3-pytest-django python3-pytest-xdist \
    python3-pip python3-wheel firefox-esr git smbclient\
    xvfb

if [ $(lsb_release --release --short) == '10' ]
then
    pip3 install pytest-bdd==3.2.1
else
    pip3 install pytest-bdd
fi

pip3 install splinter pytest-splinter pytest-xvfb

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
