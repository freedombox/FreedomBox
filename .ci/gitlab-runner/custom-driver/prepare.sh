#!/usr/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${current_dir}/base.sh # Get variables from base.

set -eo pipefail

# trap any error, and mark it as a system failure.
trap "exit $SYSTEM_FAILURE_EXIT_CODE" ERR

start_container () {
    if podman container exists "$CONTAINER_ID" ; then
        echo 'Found old container, deleting'
        podman container stop "$CONTAINER_ID"
        podman container rm -f "$CONTAINER_ID"
    fi

    podman pull registry.salsa.debian.org/freedombox-team/freedombox:functional-tests-stable
    podman run --name "$CONTAINER_ID" --systemd=always \
           --privileged \
           --cap-add=SYS_ADMIN --cap-add=NET_ADMIN --cap-add=MKNOD \
           --detach registry.salsa.debian.org/freedombox-team/freedombox:functional-tests-stable /sbin/init

    if podman exec "$CONTAINER_ID" systemctl is-system-running --wait; then
        echo 'Container started.'
    else
        echo 'Container started degraded.'
    fi
}

install_dependencies () {
    podman exec "$CONTAINER_ID" /usr/bin/bash <<EOF
set -eo pipefail
echo 'Package: *' > /etc/apt/preferences.d/unstable
echo 'Pin: release a=unstable' >> /etc/apt/preferences.d/unstable
echo 'Pin-Priority: 400'  >> /etc/apt/preferences.d/unstable
echo 'deb http://deb.debian.org/debian unstable main' > /etc/apt/sources.list.d/unstable.list
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y gitlab-runner git-lfs
EOF
}

echo "Running in $CONTAINER_ID"

start_container

install_dependencies
