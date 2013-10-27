import sys
import subprocess
import cfg

def privilegedaction_run(action, options):
    cmd = ['sudo', '-n', "/usr/share/plinth/actions/%s" % action]
    if options:
        cmd.extend(options)
    cfg.log.info('running: %s ' % ' '.join(cmd))

    output, error = \
        subprocess.Popen(cmd,
                         stdout = subprocess.PIPE,
                         stderr= subprocess.PIPE).communicate()
    return output, error
