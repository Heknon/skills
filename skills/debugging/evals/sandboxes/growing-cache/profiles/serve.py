"""Simulate the service: N requests spread over 50 users."""
import itertools
import sys

from profiles.render import render_profile

_request_ids = itertools.count(1)


def handle(user_id):
    return render_profile(user_id, next(_request_ids))


def serve(requests):
    for n in range(requests):
        handle(n % 50)


if __name__ == "__main__":
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 10_000)
    print("served")
