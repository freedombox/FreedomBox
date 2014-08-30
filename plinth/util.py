def slurp(filespec):
    with open(filespec) as x: f = x.read()
    return f


def unslurp(filespec, msg):
    with open(filespec, 'w') as x:
        x.write(msg)
