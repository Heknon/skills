class Router:
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.routes = []

    def post(self, path):
        def register(fn):
            self.routes.append(("POST", self.prefix + path, fn))
            return fn
        return register

    def get(self, path):
        def register(fn):
            self.routes.append(("GET", self.prefix + path, fn))
            return fn
        return register


class App:
    def __init__(self):
        self.routes = []

    def include(self, router, prefix=""):
        for method, path, fn in router.routes:
            self.routes.append((method, prefix + path, fn))
