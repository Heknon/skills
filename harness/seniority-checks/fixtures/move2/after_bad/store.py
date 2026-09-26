def keep(value):
    return value


def load(path):
    try:
        with open(path) as handle:
            return handle.read()
    except OSError:
        return None
