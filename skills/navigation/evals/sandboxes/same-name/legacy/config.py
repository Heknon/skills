"""Old settings loader, kept for the nightly export script."""
import configparser


def load_settings(path="legacy.ini"):
    parser = configparser.ConfigParser()
    parser.read(path)
    return dict(parser["main"])
