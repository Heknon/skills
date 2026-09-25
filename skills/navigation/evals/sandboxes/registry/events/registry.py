HANDLERS = {}


def handler(kind):
    def register(fn):
        HANDLERS[kind] = fn
        return fn
    return register
