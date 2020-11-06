#! /bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later

docker login registry.salsa.debian.org

# Build and upload a new image to the container registry
DOCKER_BUILDKIT=1 docker build -t registry.salsa.debian.org/freedombox-team/freedombox:gitlabci -f .ci/Dockerfile.gitlabci .
docker push registry.salsa.debian.org/freedombox-team/freedombox:gitlabci
