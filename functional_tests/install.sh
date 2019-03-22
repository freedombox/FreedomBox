#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "Installing requirements"
sudo apt-get install -yq --no-install-recommends \
    python3-pytest \
    python3-pip firefox \
    xvfb
pip3 install splinter pytest-splinter pytest-bdd pytest-xvfb

echo "Installing geckodriver"
(
    DL_DIR=/tmp/gecko
    GECKO_VERSION="v0.24.0"
    FILENAME="geckodriver-${GECKO_VERSION}-linux64.tar.gz"
    GECKO_URL="https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/$FILENAME"

    test -e /usr/local/bin/geckodriver &&  echo "geckodriver already installed" && exit 0

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
