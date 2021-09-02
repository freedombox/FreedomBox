# SPDX-License-Identifier: AGPL-3.0-or-later

import contextlib
import logging
import os
import uuid

logger = logging.getLogger(__name__)


def log_subprocess(result):
    logger.critical('Subprocess returned %d', result.returncode)
    logger.critical('Stdout: %r', result.stdout)
    logger.critical('Stderr: %r', result.stderr)


@contextlib.contextmanager
def atomically_rewrite(filepath):
    successful = False
    tmp = '%s.%s.plinth-tmp' % (filepath, uuid.uuid4().hex)
    fd = open(tmp, 'x')

    try:
        # Let client write to a temporary file
        yield fd
        successful = True
    finally:
        fd.close()

    try:
        if successful:
            # Invoke rename(2) to atomically replace the original
            os.rename(tmp, filepath)
    finally:
        # Delete temp file
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
