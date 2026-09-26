"""Find what grows: call a function repeatedly and compare two
tracemalloc snapshots, taken after a warm-up call and after the rounds.

Usage (from the project root):
    uv run python mem_diff.py MODULE:FUNCTION [ARG ...] [--rounds N] [--top N] [--frames N]

    MODULE:FUNCTION  the code to repeat, such as profiles.serve:serve
    ARG              arguments for the function, as Python literals (1000, 'x')
    --rounds N       calls between the two snapshots (default 5)
    --top N          lines to print (default 10)
    --frames N       group by the last N frames instead of one line (default 1)

Reading the output: the first lines are the source lines whose memory grew
the most between the snapshots, with the growth and the number of new
blocks. Memory that grows with every round and is still held at the end is
held by something: the line that allocated it is where to look, and the
container it was put into is what holds it.
"""
import argparse
import ast
import importlib
import os
import sys
import tracemalloc


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--frames", type=int, default=1)
    opts = parser.parse_args()

    sys.path.insert(0, os.getcwd())
    module_name, _, func_name = opts.target.partition(":")
    func = getattr(importlib.import_module(module_name), func_name)
    args = [ast.literal_eval(a) for a in opts.args]

    tracemalloc.start(opts.frames)
    func(*args)  # warm-up: imports, first-time caches
    before = tracemalloc.take_snapshot()
    for _ in range(opts.rounds):
        func(*args)
    after = tracemalloc.take_snapshot()

    ignore = [
        tracemalloc.Filter(False, tracemalloc.__file__),
        tracemalloc.Filter(False, __file__),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
    ]
    before = before.filter_traces(ignore)
    after = after.filter_traces(ignore)
    key = "traceback" if opts.frames > 1 else "lineno"
    stats = after.compare_to(before, key)
    grown = sum(s.size_diff for s in stats)
    print(f"{opts.rounds} rounds of {opts.target}{tuple(args)}: {grown / 1024:+.1f} KiB in total")
    for stat in stats[: opts.top]:
        if key == "lineno":
            print(stat)
        else:
            print(f"{stat.size_diff / 1024:+.1f} KiB, {stat.count_diff:+d} blocks")
            for line in stat.traceback.format():
                print("   ", line)
    current, peak = tracemalloc.get_traced_memory()
    print(f"traced now {current / 1024:.1f} KiB, peak {peak / 1024:.1f} KiB")


if __name__ == "__main__":
    main()
