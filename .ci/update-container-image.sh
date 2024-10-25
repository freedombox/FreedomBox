#! /bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later

CONTAINER=$1
CONTAINER="${CONTAINER:-gitlabci}"

podman login registry.salsa.debian.org

# Build and upload a new image to the container registry
podman build -t registry.salsa.debian.org/freedombox-team/freedombox:${CONTAINER} -f .ci/Containerfile.${CONTAINER} .
podman push registry.salsa.debian.org/freedombox-team/freedombox:${CONTAINER}
