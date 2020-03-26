#! /bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later

# Provide your Salsa credentials here
docker login registry.salsa.debian.org

# This might need 20 minutes to run
docker build -t registry.salsa.debian.org/freedombox-team/plinth:gitlabci -f Dockerfile.gitlabci .
docker push registry.salsa.debian.org/freedombox-team/plinth:gitlabci
