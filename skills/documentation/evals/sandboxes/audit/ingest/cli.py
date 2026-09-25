import argparse

from ingest.runner import run


def main():
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--source", required=True, help="folder to read CSV files from")
    parser.add_argument("--dry-run", action="store_true", help="validate only, write nothing")
    parser.add_argument("--workers", type=int, default=8, help="parallel file readers")
    parser.add_argument("--since", help="only files changed after this date, YYYY-MM-DD")
    args = parser.parse_args()
    run(args.source, dry_run=args.dry_run, workers=args.workers, since=args.since)
