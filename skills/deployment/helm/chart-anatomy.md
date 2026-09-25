# Chart anatomy

The files of an application chart, as in `recipes/generic-chart/app/`.

```
app/
  Chart.yaml            name, version, type, kubeVersion, dependencies
  values.yaml           every value, with its default and a comment
  values.schema.json    JSON Schema for the values; Helm checks it before rendering
  .helmignore           files left out of the package (tests, ci values)
  templates/
    _helpers.tpl        named templates: names, labels, image, security context
    deployment.yaml     one object kind per file
    service.yaml
    route.yaml          OpenShift Route, when enabled
    ingress.yaml        Kubernetes Ingress, when enabled
    configmap.yaml
    hpa.yaml  pdb.yaml  serviceaccount.yaml
    migration-job.yaml  a pre-install and pre-upgrade hook
    cronjobs.yaml
    NOTES.txt           printed after install; commands to check the release
  ci/
    *-values.yaml       values the chart's pipeline lints and renders with
```

## `Chart.yaml`

| Field | Rule |
| --- | --- |
| `apiVersion: v2` | Helm 3 and 4 charts |
| `name` | lowercase, digits, `-`; the folder has the same name |
| `version` | semantic version of the chart; bumped on every change |
| `appVersion` | the application's version, informational; a generic chart leaves it `"0"` since each service sets the image |
| `type` | `application`, or `library` for a chart of helpers that installs nothing |
| `kubeVersion` | the range the chart supports, such as `">=1.27.0-0"`; the `-0` admits vendor versions such as `v1.33.4+abc` |
| `dependencies` | `name`, `version`, `repository` (`https://...`, `oci://...`, or `@<repo alias>`), `alias`, `condition` |

## `values.schema.json`

- JSON Schema draft-07 works in Helm 3 and 4.
- `"additionalProperties": false` at every object level turns a misspelt
  key into an error: `additional properties 'replicas' not allowed` (lab).
- `required`, `enum`, `pattern`, `minimum` catch wrong values before any
  template runs. The recipe forbids the tag `latest` and requires
  `image.repository`.
- Helm checks the merged values: defaults, `-f` files and `--set`.
- `helm lint` checks the schema too, so a chart whose defaults leave a
  required value empty needs values from `ci/` to lint.

## Names and labels

- Object names: the release name (or `fullnameOverride`), cut to 53
  characters so suffixes fit in the 63 allowed.
- Selector labels (`app.kubernetes.io/name`, `app.kubernetes.io/instance`)
  never change for a release: a Deployment's selector is immutable, and
  changing it fails the upgrade with `field is immutable`.
- Other labels (`helm.sh/chart`, `app.kubernetes.io/version`) go on
  metadata, never in selectors.
