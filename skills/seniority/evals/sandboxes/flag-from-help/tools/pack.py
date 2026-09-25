import argparse
import sys
import zipfile


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack files into a zip archive.")
    parser.add_argument("output")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--store-only", action="store_true", help="add files without compressing them")
    parser.add_argument("--level", type=int, default=6, help="deflate level, 1 to 9")
    args = parser.parse_args()
    method = zipfile.ZIP_STORED if args.store_only else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(args.output, "w", compression=method) as archive:
        for name in args.files:
            archive.write(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
