def load_names(path):
    """Customer names from a text file, one per line, blank lines skipped."""
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]
