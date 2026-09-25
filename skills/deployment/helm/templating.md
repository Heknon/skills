# Templating

Go templates with Sprig functions, as Helm renders them. The patterns
below are all in `recipes/generic-chart/app/templates/`, which renders
and validates in the lab.

## Patterns

| Need | Write |
| --- | --- |
| a named helper | `{{- define "app.fullname" -}} ... {{- end -}}` in `_helpers.tpl`, used as `{{ include "app.fullname" . }}` |
| a helper's output indented | `{{- include "app.labels" . | nindent 4 }}` (never `template`, which cannot be piped) |
| a map or list from values | `{{- toYaml .Values.resources | nindent 12 }}` |
| a list inline, safely quoted | `command: {{ toJson .Values.command }}` |
| a string that may look like a number or boolean | `{{ .Values.env.X | quote }}` |
| a required value | `{{ required "set image.tag or image.digest" .Values.image.tag }}` |
| a default | `{{ default .Values.probes.path .Values.probes.livenessPath }}` (the default comes first) |
| stop with a message | `{{- fail "enable route or ingress, not both" }}` |
| an optional block | `{{- with .Values.nodeSelector }} nodeSelector: {{- toYaml . | nindent 8 }} {{- end }}` |
| loop with the root in reach | `{{- range $name, $job := .Values.cronJobs }} ... {{ include "app.fullname" $ }} ... {{- end }}` |
| pass several values to a helper | `{{ include "app.jobContainer" (dict "root" $ "command" .Values.migration.command) }}` |
| restart pods when config changes | `checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}` in the pod template's annotations |
| render only if the cluster has an API | `{{- if .Capabilities.APIVersions.Has "route.openshift.io/v1" }}`; `helm template` needs `--api-versions route.openshift.io/v1` to see it |

## Whitespace

`{{-` trims before, `-}}` trims after. Most rendering bugs are an
indentation or a line joined to the previous one: render and read the
output (`helm template ... --show-only templates/deployment.yaml`)
instead of reasoning about dashes.

## Scope

Inside `with` and `range`, `.` is the current item. `$` is always the
root: `$.Values`, `$.Release.Name`. A helper called with `include "x" .`
from inside `range` receives the item, not the root; pass `$`.

## Values traps

- `--set a.b=12345` makes a number; `--set-string` keeps a string. A
  schema with `"type": "string"` reports `got number, want string` (lab).
- `--set` with a comma needs escaping (`--set list={a,b}` is a list);
  prefer a values file for anything but image fields.
- Values files merge deeply: a map in a later file adds and replaces
  keys; a list replaces the whole list.
- `null` in a later values file deletes a key from the defaults.

## Never

- Never use `lookup` to read Secrets into templates: `helm template` and
  dry runs render it empty, and the value lands in the release's stored
  manifest.
- Never template a Secret's data from values in a shared chart: the values
  are stored, in the clear, in the release Secret, and `helm get values`
  prints them.
- Never render a different selector per upgrade (a timestamp, a version).
