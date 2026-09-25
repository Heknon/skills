# Variables and secrets

Two questions, one procedure each: where a value should live, and why a
variable has the value it has.

## Where a value lives

**Verdict you produce:** one place per value, with its flags.

```
<NAME>: <place> [type: env_var | file] [protected] [masked | masked and hidden] [scope: <environment>]
  because: <answers to the questions>
```

Answer in order; the first yes decides.

1. **Is it a credential, a token, a key, or a password?**
   - Needed by the application at run time: a **Kubernetes Secret** in the
     namespace, created by an administrator or a secrets operator, and
     referenced by name in the values (`envFromSecrets`). Not a CI/CD
     variable, and never in a values file.
   - Needed by the pipeline (registry login, cluster access, index
     credentials): a **CI/CD variable**, protected if only protected
     branches and tags use it, and scoped to the environment when each
     environment has its own. A one-line token is masked (masked and
     hidden when nobody needs to read it back). A kubeconfig, certificate
     or `.netrc` is a **file** variable; being several lines, it cannot be
     masked, so it must never be printed.
2. **Does it differ per environment and is it not secret?** A **values
   file** per environment (`deploy/values-<env>.yaml`) for the
   application, or the deploy job's `variables:` for the pipeline (such as
   `KUBE_NAMESPACE`).
3. **Is it the same for every project in a group** (a mirror path, a chart
   project id, a runner tag)? A **group CI/CD variable**, not protected
   unless it is secret, or an input default of a shared component.
4. **Is it for one project and not secret?** The file's top `variables:`.
5. **Does a person choose it when starting a pipeline?** A pipeline
   **input** (`spec:inputs` in the file), not a pipeline variable: inputs
   are typed and validated, and pipeline variables may be switched off
   for the project (`gitlab/variables.md`).

## Why a variable has the wrong value

**Verdict you produce:** the place the value came from, and the rule that
made it win or be absent.

1. **Is it defined at all for this job?** An empty value almost always
   means one of:
   - **protected** variable, and the ref is not protected. Tags are
     protected only if they match a protected tag pattern. Seen as:
     `kubernetes cluster unreachable: Get "http://localhost:8080/version"`
     when `KUBECONFIG` was missing.
   - **environment scope** does not match the job's `environment:name`,
     or the job has no `environment:` at all (scoped variables only reach
     jobs with a matching environment).
   - defined in a **later** place than it is used: a variable from a
     dotenv report reaches only jobs that `needs` or `dependencies` the
     job that wrote it.
   - used where it is **not expanded**, such as `rules:changes` or
     `include` with a non-predefined variable (`gitlab/variables.md`,
     where variables can be used).
2. **Which definition won?** Walk the precedence list in
   `gitlab/variables.md` from the top; the highest place that defines it
   wins. Two surprises to check first:
   - A **pipeline variable** (run page, schedule, API, trigger, or an
     **upstream pipeline**) beats every project, group and instance
     variable. Variables in a parent's `.gitlab-ci.yml` reach its child
     pipelines as pipeline variables, so there they outrank the settings
     that lost to them in the parent (seen in the lab).
   - A project variable beats `variables:` in the file.
3. **Was the value changed on the way?** Expansion: `$` inside a value is
   expanded unless the variable is raw or written `$$`. Masking: a masked
   value shows as `[MASKED]`. YAML: an unquoted value is parsed before it
   becomes a string; in the file's `variables:`, `yes` and `on` arrive as
   `true`, and `1.10` arrives as `1.1` (seen on 19.4). Quote every value
   that is not plain text.
4. **Check with evidence that reveals nothing.** In a job:
   `if [ -n "$KUBECONFIG" ]; then echo "KUBECONFIG set"; else echo "KUBECONFIG unset"; fi`
   or `test -n "$TOKEN" && echo "TOKEN length ${#TOKEN}"`. Never
   `${VAR:-default}` in a message: when the variable is set, it prints
   the value. Through the API, list keys, scopes and flags without values
   (`gitlab/api.md`).

## Never

- Never print a secret to check it, not even in a branch you will delete:
  job logs are kept.
- Never read a secret's value with `glab variable get` or the API into the
  conversation; it shows the value unless the variable is hidden.
- Never make a secret unprotected to get a pipeline on an unprotected
  branch working. Protect the branch or tag instead, or ask.
- Never put a secret in a pipeline variable or input: they are shown on the
  pipeline page.

## Stop and ask

- The fix needs a new or changed CI/CD variable. Name it, its place, type,
  flags and scope, and ask a Maintainer to set it; do not set it yourself
  unless asked.
- A secret is already in the repository or a job log. Say where, and that
  it must be rotated; deleting the commit does not unpublish it.
