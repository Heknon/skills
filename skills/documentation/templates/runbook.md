# Template: runbook

For whoever is on call when something is wrong. Short, ordered, every
command ready to paste.

````markdown
# <alert name or symptom, exactly as the alert or user reports it>

## What it means

<One or two sentences.>

## Check

1. <Command or dashboard, and what a healthy result looks like.>

## Fix

1. <Step, with the command.>

## Escalate

<Who, and when: after which step, or after how long.>
````

Every command must have been run at least once outside an incident, or
be marked `not run`.
