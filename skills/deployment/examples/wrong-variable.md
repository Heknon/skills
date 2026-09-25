# Worked example: a variable with the wrong value in child pipelines

Kind: Variables, then Debug. This happened in the lab while building the
monorepo recipe; the log lines are real.

## The ask

> Our instance has `PYTHON_IMAGE` set to the mirror. The parent pipeline
> works, but every job in the child pipelines fails to pull its image.
> Why?

## Steps

1. **Read the failing job's log** (`core/debug.md`, hop 4):

   ```
   Using Docker executor with image registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim ...
   ERROR: Job failed: failed to pull image "registry.example.com/mirror/astral-sh/uv:0.12-python3.12-trixie-slim"
   ```

   The job used `registry.example.com/...`, not the instance's value.

2. **Find every definition of the variable**: the parent's
   `.gitlab-ci.yml` has `variables: PYTHON_IMAGE:
   registry.example.com/mirror/...`; the instance setting has the working
   mirror path; the child files do not set it.

3. **Walk the precedence list** (`gitlab/variables.md`), per pipeline:
   - Parent: instance variable (6) beats the file's top-level variable
     (8). The parent's jobs got the mirror. Its `changed` job passed.
   - Child: the parent's top-level `variables` are forwarded to the child
     (`trigger:forward:yaml_variables` is true by default) and arrive as
     **pipeline variables from an upstream pipeline** (3), which beat the
     instance variable (6). The child's jobs got the file's value.

4. **Confirm with one change**: set the parent's `PYTHON_IMAGE` in the
   file to the working mirror path and push. The child jobs pulled the
   image and passed.

## The answer

```
## Result
The child pipelines use the PYTHON_IMAGE written in the parent's
.gitlab-ci.yml, not the instance variable. Variables in the parent's
variables: block are forwarded to child pipelines as pipeline variables,
and pipeline variables outrank instance, group and project variables. In
the parent itself the instance variable wins, which is why it works there.

Fix, either:
- set the right mirror path in the parent's variables: (done in this
  change), or
- stop forwarding it: trigger:forward:yaml_variables: false on the trigger
  jobs, so the children see the instance variable.

## Checked
- Job log of common-test before the change: pulled registry.example.com/...
- After the change: the child pipeline's jobs pulled the mirror image and
  passed.

## Not checked
- none

## Needs a person
- none
```
