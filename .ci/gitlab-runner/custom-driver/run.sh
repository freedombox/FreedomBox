#!/usr/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later

set -eo pipefail

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${current_dir}/base.sh # Get variables from base.

podman exec --interactive "$CONTAINER_ID" /bin/bash < "${1}"
if [ $? -ne 0 ]; then
    # Exit using the variable, to make the build as failure in GitLab
    # CI.
    exit $BUILD_FAILURE_EXIT_CODE
fi
