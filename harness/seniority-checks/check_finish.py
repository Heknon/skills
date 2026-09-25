#!/usr/bin/env python3
"""The one check to run before the final message.

Usage: check_finish.py [--dir .] [--json]

Run it from the working directory. It reads what gate 1 and gate 3 of
SKILL.md put under .ledger/:

  .ledger/ledger.md   the ledger                       always
  .ledger/answer.md   the final message, written first always
  .ledger/before/     the snapshot of each edited file when anything was edited
  .ledger/probe.py    the behaviour probe              when behaviour must stay unchanged

and runs four parts: the ledger rules (check_ledger.py), the change rules
(check_change.py) when the kind is change or a snapshot exists, the probe
when one is required or present, and the answer rules. Each part prints
its results and one line starting "ledger:", "change:" or "probe:"; the
answer's Checks section must quote those lines exactly. The last line
starts FINISH OK or FINISH NOT OK. Send the answer only after FINISH OK.

Exit 0 when no rule is FAIL, 1 when any is, 2 on an argument error.
Standard library only, Python 3.8 or later.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_change  # noqa: E402
import check_ledger  # noqa: E402
from check_ledger import FAIL, INFO, PASS, SKIP, WARN, Result, verdict  # noqa: E402

ANSWER_HEADINGS = ("Done when", "Not done", "Unverified", "Checks")
VAGUE_GOAL_RE = re.compile(r"\b(clean\s*up|cleanup|refactor\w*|tidy|improve|modernis\w*|moderniz\w*|simplif\w*|restructur\w*|reorganis\w*|reorganiz\w*)\b", re.I)
COPY_IGNORE = shutil.ignore_patterns(".ledger", ".git", "__pycache__", "node_modules", "*.pyc")
PROBE_TIMEOUT_SECONDS = 60


def read(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


def probe_required(ledger) -> bool:
    if ledger.header.get("kind", "").lower() != "change":
        return False
    return bool(VAGUE_GOAL_RE.search(ledger.header.get("goal", ""))) or "unchanged" in ledger.header.get("done when", "").lower()


def run_probe(probe: str, tree: str, workdir: str) -> Tuple[int, str]:
    """Run the probe against one tree. A probe that names the working directory by its absolute
    path would import the changed code in both runs, so that path is rewritten to the tree's."""
    text = read(probe) or ""
    copy = os.path.join(tree, ".check_finish_probe.py")
    with open(copy, "w", encoding="utf-8") as handle:
        handle.write(text.replace(workdir.rstrip(os.sep), tree))
    env = dict(os.environ)
    env["PYTHONPATH"] = tree + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        done = subprocess.run([sys.executable, copy], cwd=tree, env=env, capture_output=True,
                              text=True, timeout=PROBE_TIMEOUT_SECONDS)
        return done.returncode, done.stdout + (("\n[stderr]\n" + done.stderr) if done.returncode else "")
    except subprocess.TimeoutExpired:
        return -1, f"timed out after {PROBE_TIMEOUT_SECONDS} s"


def probe_part(workdir: str, before: str, probe: str, required: bool) -> List[Result]:
    if not os.path.isfile(probe):
        if required:
            return [Result("probe-present", FAIL, 1, [f"no {probe}"],
                           "the goal asks for behaviour to stay the same; before the first edit write .ledger/probe.py, which imports the code you will change and prints each public function's result on edge inputs (SKILL.md gate 1)")]
        return [Result("probe-present", SKIP, 0, [], "no probe, and the goal does not require one")]
    results = [Result("probe-present", PASS, 0, [], probe)]
    if not required:
        scratch = tempfile.mkdtemp(prefix="check_finish_")
        try:
            tree = os.path.join(scratch, "after")
            shutil.copytree(workdir, tree, ignore=COPY_IGNORE)
            code, out = run_probe(probe, tree, workdir)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        if code != 0:
            results.append(Result("probe-runs", FAIL, 1, [f"exit {code} on the changed code: {out.strip()[-200:]!r}"], "the probe must run"))
        else:
            results.append(Result("probe-runs", PASS, 0, [], "exit 0 on the changed code"))
        results.append(Result("behaviour-unchanged", INFO, 0, [], "not compared: the goal does not ask for behaviour to stay the same, so a fix may change results"))
        return results
    if not os.path.isdir(before) or not check_change.snapshot_files(before):
        results.append(Result("behaviour-unchanged", FAIL, 1, ["no snapshot to run the probe against"], "take the snapshot before the first edit"))
        return results
    scratch = tempfile.mkdtemp(prefix="check_finish_")
    try:
        old_tree, new_tree = os.path.join(scratch, "before"), os.path.join(scratch, "after")
        shutil.copytree(workdir, new_tree, ignore=COPY_IGNORE)
        shutil.copytree(workdir, old_tree, ignore=COPY_IGNORE)
        for path in check_change.snapshot_files(before):
            target = os.path.join(old_tree, path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(os.path.join(before, path), target)
        old_code, old_out = run_probe(probe, old_tree, workdir)
        new_code, new_out = run_probe(probe, new_tree, workdir)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if old_code != 0:
        results.append(Result("probe-runs", FAIL, 1, [f"exit {old_code} on the code before the change: {old_out.strip()[-200:]!r}"], "the probe must run on the old code too; call only what existed before"))
        return results
    if new_code != 0:
        results.append(Result("probe-runs", FAIL, 1, [f"exit {new_code} on the changed code: {new_out.strip()[-200:]!r}"], "the change broke something the probe calls"))
        return results
    results.append(Result("probe-runs", PASS, 0, [], "exit 0 on the old and the new code"))
    old_lines, new_lines = old_out.splitlines(), new_out.splitlines()
    differences = [f"line {index + 1}: before {old!r}, after {new!r}" for index, (old, new) in enumerate(zip(old_lines, new_lines)) if old != new]
    if len(old_lines) != len(new_lines):
        differences.append(f"before printed {len(old_lines)} lines, after {len(new_lines)}")
    if not old_lines:
        results.append(Result("behaviour-unchanged", FAIL, 1, ["the probe printed nothing"], "print the result of every call, one per line"))
    else:
        results.append(verdict("behaviour-unchanged", differences, note="the same call now gives a different result: revert that change, or list it under Not done as a proposal",
                               passing_note=f"{len(old_lines)} probe lines identical"))
    return results


MAX_NEIGHBOURS = 20


def untouched_neighbours(workdir: str, before: str) -> List[Tuple[str, List[str]]]:
    """For each changed Python file, the public top-level functions the change did not touch."""
    found = []
    for path in check_change.snapshot_files(before):
        if not path.endswith(".py") or check_change.TEST_PATH_RE.search(path):
            continue
        old, new = read(os.path.join(before, path)), read(os.path.join(workdir, path))
        if old is None or new is None or old == new:
            continue
        try:
            old_tree, new_tree = ast.parse(old), ast.parse(new)
        except SyntaxError:
            continue
        old_bodies = {node.name: ast.dump(node) for node in old_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        names = [node.name for node in new_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and not node.name.startswith("_") and old_bodies.get(node.name) == ast.dump(node)]
        if names and len(names) <= MAX_NEIGHBOURS:
            found.append((path, names))
    return found


def sections(text: str) -> List[Tuple[str, str]]:
    found, current, lines = [], None, []
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            if current is not None:
                found.append((current, "\n".join(lines).strip()))
            current, lines = heading.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        found.append((current, "\n".join(lines).strip()))
    return found


def answer_part(answer_path: str, ledger, quoted: List[str], neighbours: Optional[List[Tuple[str, List[str]]]] = None) -> List[Result]:
    text = read(answer_path)
    if not text or not text.strip():
        return [Result("answer-present", FAIL, 1, [f"no {answer_path}"], "write the final message to .ledger/answer.md first, then run this check (SKILL.md gate 3)")]
    results = [Result("answer-present", PASS, 0, [], answer_path)]
    found = sections(text)
    names = [name for name, _ in found]
    tail = names[-len(ANSWER_HEADINGS):]
    if [name.lower() for name in tail] != [name.lower() for name in ANSWER_HEADINGS]:
        results.append(Result("answer-headings", FAIL, 1, [f"the last headings are {tail}, not {list(ANSWER_HEADINGS)}"],
                              "end the message with ## Done when, ## Not done, ## Unverified, ## Checks, in this order, and nothing after them"))
        return results
    body = {name.lower(): content for name, content in found[-len(ANSWER_HEADINGS):]}
    empty = [f"## {name} is empty; write `none` if there is nothing" for name in ANSWER_HEADINGS if not body[name.lower()]]
    results.append(verdict("answer-headings", empty, passing_note="the four closing headings, in order, each filled"))

    state = check_ledger.done_state(ledger)
    done_text = body["done when"]
    if not state:
        results.append(Result("answer-done-matches-ledger", FAIL, 1, ["the ledger's Done section is still 'not yet' or malformed"], "finish the ledger first (core/done.md)"))
    elif state[0] == "observed" and not re.search(rf"\bstep\s+{state[1]}\b", done_text, re.I):
        results.append(Result("answer-done-matches-ledger", FAIL, 1, [f"the ledger says observed at step {state[1]}; the answer's Done when does not name step {state[1]}"], "copy the ledger's Done line"))
    elif state[0] == "stopped" and not re.search(r"\b(stopped|not observed)\b", done_text, re.I):
        results.append(Result("answer-done-matches-ledger", FAIL, 1, [f"the ledger says stopped at step {state[1]}; the answer's Done when does not say stopped or not observed"], "copy the ledger's Done line"))
    else:
        results.append(Result("answer-done-matches-ledger", PASS, 0, [], f"{state[0]} at step {state[1]}"))

    statuses = {number: status.lower() for number, status, _, _ in ledger.assumptions if number != "?"}
    listed = set(re.findall(r"\bA(\d+)\b", body["unverified"]))
    offenders = [f"A{number} is [unverified] in the ledger and missing from ## Unverified" for number, status in statuses.items() if status == "unverified" and number not in listed]
    offenders += [f"A{number} is listed but the ledger says '{statuses[number]}'; update the answer or the ledger" for number in sorted(listed) if number in statuses and statuses[number] != "unverified"]
    results.append(verdict("answer-unverified-matches", offenders, note="## Unverified lists exactly the assumptions whose ledger status is still [unverified]"))

    if neighbours is not None:
        unnamed = [f"{path}: {name}" for path, names in neighbours for name in names if not re.search(rf"\b{re.escape(name)}\b", body["not done"])]
        results.append(verdict("neighbours-reviewed", unnamed,
                               note="core/done.md question 3: read the rest of every file you changed; under ## Not done name each function listed here, with the defect you saw or 'reviewed, fine'",
                               passing_note="every untouched function in the changed files is named under Not done"))

    missing = [f"## Checks does not contain the line {line!r}" for line in quoted if line not in body["checks"]]
    results.append(verdict("answer-quotes-checks", missing, note="copy each 'ledger:', 'change:' and 'probe:' line this check printed, exactly, into ## Checks",
                           passing_note="every part's line is quoted"))
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=".", help="the working directory (default: the current one)")
    parser.add_argument("--ledger", help="default: <dir>/.ledger/ledger.md")
    parser.add_argument("--answer", help="default: <dir>/.ledger/answer.md")
    parser.add_argument("--before", help="default: <dir>/.ledger/before")
    parser.add_argument("--probe", help="default: <dir>/.ledger/probe.py")
    parser.add_argument("--no-change-check", action="store_true", help="skip the change and probe parts; for the worked examples, which carry no snapshot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    workdir = os.path.abspath(args.dir)
    ledger_path = args.ledger or os.path.join(workdir, ".ledger", "ledger.md")
    answer_path = args.answer or os.path.join(workdir, ".ledger", "answer.md")
    before = args.before or os.path.join(workdir, ".ledger", "before")
    probe = args.probe or os.path.join(workdir, ".ledger", "probe.py")

    ledger_text = read(ledger_path)
    if ledger_text is None:
        print(f"check_finish: cannot read {ledger_path}; the ledger is written at gate 1", file=sys.stderr)
        return 2
    ledger, ledger_results, _ = check_ledger.evaluate(ledger_text)
    parts = [("ledger", ledger_results)]

    kind = ledger.header.get("kind", "").lower()
    has_snapshot = os.path.isdir(before) and bool(check_change.snapshot_files(before))
    if not args.no_change_check and (kind == "change" or has_snapshot):
        change_results, _ = check_change.evaluate(before, workdir)
        parts.append(("change", change_results))
        required = probe_required(ledger)
        if required or os.path.isfile(probe):
            parts.append(("probe", probe_part(workdir, before, probe, required)))

    quoted = [f"{name}: {check_ledger.summary_line(results)}" for name, results in parts]
    neighbours = untouched_neighbours(workdir, before) if (not args.no_change_check and has_snapshot) else None
    answer_results = answer_part(answer_path, ledger, quoted, neighbours)
    all_results = [result for _, results in parts for result in results] + answer_results
    exit_code = 1 if any(result.status == FAIL for result in all_results) else 0

    if args.json:
        print(json.dumps({"tool": "check_finish", "dir": workdir, "quote": quoted,
                          "parts": {name: [r.to_dict() for r in results] for name, results in parts + [("answer", answer_results)]},
                          "exit_code": exit_code}, indent=2))
        return exit_code
    for (name, results), line in zip(parts, quoted):
        print(f"== {name}")
        check_ledger.print_results(results)
        print(line)
    print("== answer")
    check_ledger.print_results(answer_results)
    print(f"answer: {check_ledger.summary_line(answer_results)}")
    failing = sorted({name for name, results in parts + [("answer", answer_results)] if any(r.status == FAIL for r in results)})
    if exit_code == 0:
        print("FINISH OK: send .ledger/answer.md as your final message, unchanged; exit 0")
    else:
        print(f"FINISH NOT OK: fix {', '.join(failing)}, then run this again; do not send the answer yet; exit 1")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
