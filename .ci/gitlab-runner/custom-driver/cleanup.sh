#!/usr/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${current_dir}/base.sh # Get variables from base.

echo "Deleting container $CONTAINER_ID"

podman container stop "$CONTAINER_ID"
podman container rm -f "$CONTAINER_ID"
