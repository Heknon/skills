#!/usr/bin/env python3
"""Judge a task ledger against the rules in core/ledger.md.

Usage: check_ledger.py --ledger FILE [--json]

Every rule prints PASS, FAIL, WARN, SKIP or INFO, a count, up to five
offenders and a note. Exit 0 when no rule is FAIL, 1 when any is, 2 on an
argument or read error. Standard library only, Python 3.8 or later.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

PASS, FAIL, WARN, SKIP, INFO = "PASS", "FAIL", "WARN", "SKIP", "INFO"
MAX_EXAMPLES = 5

HEADER_KEYS = ("goal", "done when", "budget", "scope out")
VAGUE_DONE = re.compile(r"\b(works?|working|fixed|correct(ly)?|clean|good|better|properly|done)\b", re.I)
CONCRETE_DONE = re.compile(r"`|\d|\bexits?\b|\bprints?\b|\bshows?\b|\bexists?\b|\bcontains?\b|\banswered\b|\bnamed\b")
STEP_RE = re.compile(r"^(\d+)\.\s+(.*)$")
STEP_FIELDS_RE = re.compile(
    r"^action:\s*(?P<action>.*?)\s*\|\s*result:\s*(?P<result>.*?)\s*\|\s*new fact:\s*(?P<fact>.*?)\s*$",
    re.I,
)
CONTINUATION_RE = re.compile(r"^\s+(stuck|budget extended to (\d+)|verdict [\w-]+)\s*:\s*(.*)$", re.I)
ASSUMPTION_RE = re.compile(r"^-\s*A(\d+)\s*\[(?P<status>[^\]]*)\]\s*(?P<text>.*)$")
ASSUMPTION_STATUS_RE = re.compile(r"^(unverified|verified at step (\d+)|false at step (\d+))$", re.I)
HYPOTHESIS_RE = re.compile(r"^-\s*H(\d+)\s*\[(?P<status>[^\]]*)\]\s*(?P<text>.*)$")
HYPOTHESIS_STATUS_RE = re.compile(r"^(open|confirmed at step (\d+)|ruled out at step (\d+))$", re.I)
DONE_RE = re.compile(r"^(observed|stopped) at step (\d+)\s*:\s*(.+)$", re.I)
BUDGET_RE = re.compile(r"^(\d+)\s+steps?$", re.I)
BACKTICK_RE = re.compile(r"`([^`]+)`")
RISKY_RE = re.compile(
    r"(?<![\w/.-])(prod|production|deploy|publish|truncate)(?![\w/.-])"
    r"|\bgit\s+push\b|\brm\s+-\w*r|--force\b|\bdrop\s+(table|database|column|schema)\b"
    r"|\bkubectl\s+(delete|apply)\b|\bterraform\s+(apply|destroy)\b|\bhelm\s+(install|upgrade|uninstall)\b",
    re.I,
)


@dataclass
class Result:
    name: str
    status: str
    count: int = 0
    examples: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "rule": self.name,
            "status": self.status,
            "count": self.count,
            "examples": self.examples[:MAX_EXAMPLES],
            "note": self.note,
        }


def verdict(name: str, offenders: List[str], failing: str = FAIL, note: str = "", passing_note: str = "") -> Result:
    if offenders:
        return Result(name, failing, len(offenders), offenders, note)
    return Result(name, PASS, 0, [], passing_note)


@dataclass
class Step:
    number: int
    line: int
    action: str = ""
    result: str = ""
    fact: str = ""
    malformed: bool = False
    stuck: List[str] = field(default_factory=list)
    verdicts: List[str] = field(default_factory=list)
    budget_extended_to: Optional[int] = None

    @property
    def signature(self) -> str:
        return normalise(self.action)

    @property
    def outcome(self) -> str:
        return normalise(self.result)

    @property
    def no_fact(self) -> bool:
        return normalise(self.fact).rstrip(".") == "none"


@dataclass
class Ledger:
    header: Dict[str, str] = field(default_factory=dict)
    assumptions: List[tuple] = field(default_factory=list)
    hypotheses: List[tuple] = field(default_factory=list)
    hypotheses_none: bool = False
    steps: List[Step] = field(default_factory=list)
    done_lines: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def parse(text: str) -> Ledger:
    ledger = Ledger()
    section = "header"
    in_fence = False
    for number, raw in enumerate(text.splitlines(), start=1):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = raw.rstrip()
        if not line.strip():
            continue
        heading = re.match(r"^##\s+(.*)$", line)
        if heading:
            section = heading.group(1).strip().lower()
            ledger.sections.append(section)
            continue
        if line.startswith("# "):
            continue
        if section == "header":
            match = re.match(r"^([a-z ]+):\s*(.*)$", line.strip(), re.I)
            if match and match.group(1).strip().lower() in HEADER_KEYS:
                ledger.header[match.group(1).strip().lower()] = match.group(2).strip()
        elif section == "assumptions":
            match = ASSUMPTION_RE.match(line.strip())
            if match:
                ledger.assumptions.append((match.group(1), match.group("status").strip(), match.group("text").strip(), number))
            elif line.strip().lower() != "none":
                ledger.assumptions.append(("?", "", line.strip(), number))
        elif section == "hypotheses":
            if line.strip().lower() == "none":
                ledger.hypotheses_none = True
                continue
            match = HYPOTHESIS_RE.match(line.strip())
            if match:
                ledger.hypotheses.append((match.group(1), match.group("status").strip(), match.group("text").strip(), number))
            else:
                ledger.hypotheses.append(("?", "", line.strip(), number))
        elif section == "steps":
            continuation = CONTINUATION_RE.match(raw)
            if continuation and raw[:1].isspace() and ledger.steps:
                kind = continuation.group(1).lower()
                if kind == "stuck":
                    ledger.steps[-1].stuck.append(continuation.group(3).strip())
                elif kind.startswith("budget extended"):
                    ledger.steps[-1].budget_extended_to = int(continuation.group(2))
                else:
                    ledger.steps[-1].verdicts.append(kind.split(" ", 1)[1] + ": " + continuation.group(3).strip())
                continue
            if raw[:1].isspace() and ledger.steps:
                continue
            match = STEP_RE.match(line.strip())
            if not match:
                ledger.steps.append(Step(number=-1, line=number, action=line.strip(), malformed=True))
                continue
            step = Step(number=int(match.group(1)), line=number)
            fields = STEP_FIELDS_RE.match(match.group(2))
            if fields:
                step.action, step.result, step.fact = fields.group("action"), fields.group("result"), fields.group("fact")
                step.malformed = not (step.action and step.result and step.fact)
            else:
                step.action = match.group(2)
                step.malformed = True
            ledger.steps.append(step)
        elif section == "done":
            ledger.done_lines.append(line.strip())
    return ledger


def rule_header(ledger: Ledger) -> Result:
    offenders = []
    for key in HEADER_KEYS:
        value = ledger.header.get(key)
        if value is None:
            offenders.append(f"missing '{key}:' line")
        elif not value or re.search(r"<[A-Za-z][^<>]*>", re.sub(r"`[^`]*`", "", value)):
            offenders.append(f"'{key}:' still holds a placeholder: {value!r}")
    budget = ledger.header.get("budget", "")
    if budget and not BUDGET_RE.match(budget):
        offenders.append(f"'budget:' must be '<n> steps', found {budget!r}")
    for section in ("assumptions", "hypotheses", "steps", "done"):
        if section not in ledger.sections:
            offenders.append(f"missing '## {section.capitalize()}' section")
    return verdict("header", offenders, note="core/ledger.md: The template", passing_note="goal, done when, budget, scope out and all four sections present")


def rule_done_when(ledger: Ledger) -> Result:
    value = ledger.header.get("done when", "")
    if not value:
        return Result("done-when-observable", SKIP, 0, [], "no 'done when' line; see rule header")
    if VAGUE_DONE.search(value) and not CONCRETE_DONE.search(value):
        return Result("done-when-observable", WARN, 1, [value], "reads like a prediction; name a command and its result, a file, or a sourced answer (core/scope.md question 3)")
    return Result("done-when-observable", PASS)


def rule_steps_numbered(ledger: Ledger) -> Result:
    offenders = []
    expected = 1
    for step in ledger.steps:
        if step.number == -1:
            offenders.append(f"line {step.line}: not a step line: {step.action[:80]!r}")
            continue
        if step.number != expected:
            offenders.append(f"line {step.line}: step {step.number} where {expected} was expected")
        expected = step.number + 1
        if step.malformed:
            offenders.append(f"line {step.line}: step {step.number} needs 'action: ... | result: ... | new fact: ...'")
    return verdict("steps-numbered", offenders, note="core/ledger.md: Steps", passing_note=f"{len(ledger.steps)} steps")


def rule_repeated_action(ledger: Ledger) -> Result:
    seen: Dict[tuple, List[int]] = {}
    for step in ledger.steps:
        if step.malformed or not step.signature:
            continue
        seen.setdefault((step.signature, step.outcome), []).append(step.number)
    fails = [f"steps {numbers}: {key[0][:70]!r} -> same result {len(numbers)} times" for key, numbers in seen.items() if len(numbers) >= 3]
    warns = [f"steps {numbers}: {key[0][:70]!r} -> same result twice; a third time is not allowed" for key, numbers in seen.items() if len(numbers) == 2]
    if fails:
        return Result("repeated-action", FAIL, len(fails), fails + warns, "loop rule 1: the same action with the same result is never done a third time unchanged")
    if warns:
        return Result("repeated-action", WARN, len(warns), warns, "loop rule 1: next time, go to Stuck")
    return Result("repeated-action", PASS)


def rule_oscillation(ledger: Ledger) -> Result:
    signatures = [step.signature for step in ledger.steps if not step.malformed]
    offenders = []
    for index in range(3, len(signatures)):
        a, b, c, d = signatures[index - 3 : index + 1]
        if a == c and b == d and a != b:
            offenders.append(f"steps {index - 2} to {index + 1}: A, B, A, B with A={a[:40]!r}, B={b[:40]!r}")
    return verdict("oscillation", offenders, note="loop rule 3: alternating between two fixes means the cause is elsewhere (core/loop-breaker.md)")


def rule_no_new_fact_streak(ledger: Ledger) -> Result:
    offenders = []
    steps = [step for step in ledger.steps if not step.malformed]
    for previous, current in zip(steps, steps[1:]):
        if previous.no_fact and current.no_fact and not previous.stuck and not current.stuck:
            offenders.append(f"steps {previous.number} and {current.number} both 'new fact: none' and no 'stuck:' line")
    return verdict("no-new-fact-streak", offenders, note="loop rule 2: two steps with no new fact go to Stuck")


def rule_stuck_changes_approach(ledger: Ledger) -> Result:
    offenders = []
    steps = [step for step in ledger.steps if not step.malformed]
    for index, step in enumerate(steps):
        if not step.stuck or index + 1 >= len(steps):
            continue
        before = {earlier.signature for earlier in steps[: index + 1]}
        following = steps[index + 1]
        if following.signature in before:
            offenders.append(f"step {following.number} repeats an earlier action right after 'stuck:' at step {step.number}: {following.action[:70]!r}")
    return verdict("stuck-changes-approach", offenders, note="core/loop-breaker.md step 5: change the approach, not its parameters")


def risky_command(action: str) -> Optional[str]:
    """The risky part of a command, or None. Reads and searches are not commands.

    A command is the text in backticks, or, when the action has none, what
    follows a leading "run" or "execute".
    """
    commands = BACKTICK_RE.findall(action)
    if not commands:
        bare = re.match(r"^\s*(run|execute|ran|executed)\s+(.+)$", action, re.I)
        commands = [bare.group(2)] if bare else []
    for command in commands:
        match = RISKY_RE.search(command)
        if match:
            return match.group(0)
    return None


def rule_risky_needs_challenge(ledger: Ledger) -> Result:
    offenders = []
    steps = [step for step in ledger.steps if not step.malformed]
    for index, step in enumerate(steps):
        word = risky_command(step.action)
        if not word or normalise(step.action).startswith("ask:"):
            continue
        challenge_at = next((earlier.number for earlier in steps[:index] if any(v.startswith("challenge:") for v in earlier.verdicts)), None)
        if challenge_at is None:
            offenders.append(f"step {step.number} runs a risky command ({word!r}) with no earlier 'verdict challenge:' line")
            continue
        asked = any(normalise(later.action).startswith("ask:") for later in steps[:index] if later.number > challenge_at)
        if not asked:
            offenders.append(f"step {step.number} runs a risky command ({word!r}) without an 'action: ask:' step after the challenge at step {challenge_at}")
    return verdict("risky-needs-challenge", offenders, note="SKILL.md gate 2: challenge, show the person, get their answer, then act; an instruction given before the challenge is not approval")


def rule_budget(ledger: Ledger) -> Result:
    match = BUDGET_RE.match(ledger.header.get("budget", ""))
    if not match:
        return Result("budget", SKIP, 0, [], "no readable budget; see rule header")
    budget = int(match.group(1))
    offenders = []
    for step in ledger.steps:
        if step.malformed:
            continue
        if step.number > budget:
            offenders.append(f"step {step.number} is past the budget of {budget} with no 'budget extended' line before it")
            break
        if step.budget_extended_to:
            budget = step.budget_extended_to
    extensions = sum(1 for step in ledger.steps if step.budget_extended_to)
    if extensions > 1:
        offenders.append(f"{extensions} budget extensions; core/loop-breaker.md allows one, then stop")
    return verdict("budget", offenders, note="loop rule 4", passing_note=f"{len(ledger.steps)} of {budget} steps")


def rule_hypotheses(ledger: Ledger) -> Result:
    if "hypotheses" not in ledger.sections:
        return Result("hypotheses-falsifiable", SKIP, 0, [], "no Hypotheses section")
    offenders = []
    step_numbers = {step.number for step in ledger.steps}
    for number, status, text, line in ledger.hypotheses:
        if number == "?":
            offenders.append(f"line {line}: not a hypothesis line: {text[:70]!r}")
            continue
        status_match = HYPOTHESIS_STATUS_RE.match(status)
        if not status_match:
            offenders.append(f"H{number}: status {status!r} is not open, confirmed at step <n>, or ruled out at step <n>")
        else:
            ref = status_match.group(2) or status_match.group(3)
            if ref and int(ref) not in step_numbers:
                offenders.append(f"H{number}: names step {ref}, which does not exist")
        if not re.search(r"\|\s*test:\s*\S", text, re.I):
            offenders.append(f"H{number}: no '| test:'")
        if not re.search(r"\|\s*disproved if:\s*\S", text, re.I):
            offenders.append(f"H{number}: no '| disproved if:'; a hypothesis nothing could disprove is not a hypothesis")
    return verdict("hypotheses-falsifiable", offenders, note="core/hypothesis-loop.md step 4", passing_note=f"{len(ledger.hypotheses)} hypotheses")


def rule_assumptions(ledger: Ledger) -> Result:
    offenders = []
    step_numbers = {step.number for step in ledger.steps}
    for number, status, text, line in ledger.assumptions:
        if number == "?":
            offenders.append(f"line {line}: not an assumption line: {text[:70]!r}")
            continue
        match = ASSUMPTION_STATUS_RE.match(status)
        if not match:
            offenders.append(f"A{number}: status {status!r} is not unverified, verified at step <n>, or false at step <n>")
            continue
        ref = match.group(2) or match.group(3)
        if ref and int(ref) not in step_numbers:
            offenders.append(f"A{number}: names step {ref}, which does not exist")
    return verdict("assumption-status", offenders, note="core/ledger.md: Assumptions", passing_note=f"{len(ledger.assumptions)} assumptions")


def done_state(ledger: Ledger):
    for line in ledger.done_lines:
        match = DONE_RE.match(line)
        if match:
            return match.group(1).lower(), int(match.group(2)), match.group(3)
    return None


def rule_done(ledger: Ledger) -> Result:
    lines = [line for line in ledger.done_lines if line.lower() != "not yet"]
    if not lines:
        return Result("done-observed", INFO, 0, [], "Done says 'not yet': the task is in progress")
    state = done_state(ledger)
    if not state:
        return Result("done-observed", FAIL, 1, lines[:1], "Done must be 'observed at step <n>: ...' or 'stopped at step <n>: ...'")
    kind, number, _ = state
    if number not in {step.number for step in ledger.steps}:
        return Result("done-observed", FAIL, 1, [f"{kind} at step {number}, which does not exist"], "core/done.md question 1")
    return Result("done-observed", PASS, 0, [], f"{kind} at step {number}")


def rule_unverified_at_done(ledger: Ledger) -> Result:
    if not done_state(ledger):
        return Result("unverified-at-done", SKIP, 0, [], "task not finished")
    open_ones = [f"A{number}: {text[:70]}" for number, status, text, _ in ledger.assumptions if status.lower() == "unverified"]
    if open_ones:
        return Result("unverified-at-done", WARN, len(open_ones), open_ones, "list each under 'Unverified' in the answer")
    return Result("unverified-at-done", PASS)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger", required=True, help="path to ledger.md")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args(argv)
    try:
        with open(args.ledger, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as error:
        print(f"check_ledger: cannot read {args.ledger}: {error}", file=sys.stderr)
        return 2

    ledger = parse(text)
    results = [
        rule_header(ledger),
        rule_done_when(ledger),
        rule_steps_numbered(ledger),
        rule_repeated_action(ledger),
        rule_oscillation(ledger),
        rule_no_new_fact_streak(ledger),
        rule_stuck_changes_approach(ledger),
        rule_budget(ledger),
        rule_risky_needs_challenge(ledger),
        rule_hypotheses(ledger),
        rule_assumptions(ledger),
        rule_done(ledger),
        rule_unverified_at_done(ledger),
    ]
    summary = {
        "steps": len(ledger.steps),
        "assumptions": len(ledger.assumptions),
        "hypotheses": len(ledger.hypotheses),
        "stuck": sum(len(step.stuck) for step in ledger.steps),
    }
    exit_code = 1 if any(result.status == FAIL for result in results) else 0
    if args.json:
        print(json.dumps({"tool": "check_ledger", "input": args.ledger, "summary": summary,
                          "results": [result.to_dict() for result in results], "exit_code": exit_code}, indent=2))
        return exit_code
    print(f"check_ledger: {args.ledger}")
    print("  " + ", ".join(f"{key}={value}" for key, value in summary.items()))
    for result in results:
        print(f"{result.status:<4} {result.name:<26} {result.count}")
        for example in result.examples[:MAX_EXAMPLES]:
            print(f"       - {example}")
        if result.note:
            print(f"       note: {result.note}")
    counts = {status: sum(1 for result in results if result.status == status) for status in (PASS, FAIL, WARN, SKIP, INFO)}
    counts_text = " ".join(f"{status}={count}" for status, count in counts.items() if count)
    print(f"{'OK' if exit_code == 0 else 'NOT OK'}: {counts_text}; exit {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
