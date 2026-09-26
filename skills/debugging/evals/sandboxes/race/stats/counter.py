def weight(path):
    """API calls count double in the usage report."""
    return 2 if path.startswith("/api/") else 1


class HitCounter:
    """Hits per path, shared by every request thread."""

    def __init__(self):
        self.hits = {}

    def record(self, path):
        current = self.hits.get(path, 0)
        self.hits[path] = current + weight(path)
