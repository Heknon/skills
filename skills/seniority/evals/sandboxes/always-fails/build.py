"""Build the site bundle into dist/."""
import argparse
import os
import shutil
import sys
import urllib.request

ASSET_URL = "http://assets.internal.example:8081/bundle.tar"


def fetch_assets(offline: bool) -> str:
    if offline:
        return os.path.join("vendor", "assets")
    urllib.request.urlopen(ASSET_URL, timeout=3)
    return "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the site bundle into dist/.")
    parser.add_argument("--offline", action="store_true", help="use the vendored assets in vendor/assets instead of downloading them")
    args = parser.parse_args()
    source = fetch_assets(args.offline)
    os.makedirs("dist", exist_ok=True)
    for name in os.listdir("src"):
        shutil.copy(os.path.join("src", name), os.path.join("dist", name))
    for name in os.listdir(source):
        shutil.copy(os.path.join(source, name), os.path.join("dist", name))
    print(f"built dist/ with {len(os.listdir('dist'))} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
