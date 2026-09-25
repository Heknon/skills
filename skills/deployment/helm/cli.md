# The Helm CLI

Everything `helm` offers beyond the deploy command, for Helm 4.3 and 3.22,
taken from their `--help` and run in the lab. Task-oriented use is in
`helm/commands.md`; flag differences between 3 and 4 in
`helm/versions.md`.

## Installing on Windows, air gapped

Helm is one `helm.exe`. Take the `windows-amd64` zip from the internal
mirror, unpack it to a folder on `PATH` (such as
`$env:LOCALAPPDATA\Programs\helm`), and check `helm version`. No
installer, no package manager needed.

## Where Helm keeps things

| What | Linux | Windows | Variable |
| --- | --- | --- | --- |
| configuration: `repositories.yaml`, `registry/config.json` | `~/.config/helm` | `%APPDATA%\helm` | `HELM_CONFIG_HOME` |
| cache: repository indexes, downloaded charts | `~/.cache/helm` | `%TEMP%\helm` | `HELM_CACHE_HOME` |
| data: plugins | `~/.local/share/helm` | `%APPDATA%\helm` | `HELM_DATA_HOME`, `HELM_PLUGINS` |

`helm env` prints the values in use. `HELM_REPOSITORY_CONFIG`,
`HELM_REPOSITORY_CACHE` and `HELM_REGISTRY_CONFIG` point at single
files and folders, useful to keep a CI job's Helm state inside its
workspace.

## Choosing the cluster and namespace

| Flag | Variable | Notes |
| --- | --- | --- |
| `--kubeconfig <file>` | `KUBECONFIG` | the recipes use a File variable named `KUBECONFIG` |
| `--kube-context <name>` | `HELM_KUBECONTEXT` | a context in that file |
| `-n <ns>`, `--namespace` | `HELM_NAMESPACE` | without it, the context's namespace (*lab:* the deployer's kubeconfig listed `shop-staging` releases on Helm 3 and 4); pass `-n` anyway, so the command says where it acts |
| `--kube-ca-file`, `--kube-tls-server-name` | `HELM_KUBECAFILE`, `HELM_KUBETLS_SERVER_NAME` | a CA or name for the API server's certificate |
| `--kube-token`, `--kube-apiserver` | `HELM_KUBETOKEN`, `HELM_KUBEAPISERVER` | avoid: the token is on the command line |
| `--kube-insecure-skip-tls-verify` | `HELM_KUBEINSECURE_SKIP_TLS_VERIFY` | never |
| `--debug` | `HELM_DEBUG` | more output; with `template`, renders invalid YAML so you can read it |

## Commands

| Command | Does | Notes |
| --- | --- | --- |
| `helm version` | the client's version | read it first |
| `helm env` | Helm's paths and variables | |
| `helm create <name>` | a starter chart | prefer the generic chart recipe |
| `helm lint --strict <chart> -f <values>` | checks the chart and values schema | `--with-subcharts` for dependencies |
| `helm template <release> <chart> -f <values>` | renders locally, no cluster | `--show-only templates/x.yaml`; `--api-versions route.openshift.io/v1`; `--kube-version 1.33.0`; `--namespace` for rendered namespaces |
| `helm install`, `helm upgrade --install` | deploy | `core/deploy.md` |
| `helm list -n <ns>`; `helm list -A` | releases; in every namespace | `--failed`, `--pending`, `--superseded`, `-o json` |
| `helm status <release> -n <ns>` | state, notes | `--revision <n>`, `-o json` |
| `helm history <release> -n <ns>` | revisions and why each failed | `--max <n>`, `-o json` |
| `helm get values\|manifest\|notes\|hooks\|metadata\|all <release> -n <ns>` | what was deployed | `values` prints what was passed, secrets included; `--all` adds defaults; `--revision <n>` for an older one |
| `helm rollback <release> <revision> -n <ns>` | back to a revision, as a new one | `--wait`, `--timeout`, `--cleanup-on-fail` |
| `helm uninstall <release> -n <ns>` | deletes the release and its objects | `--keep-history`, `--dry-run`; never as a fix |
| `helm test <release> -n <ns>` | runs the chart's `test` hooks | the generic chart has none |
| `helm show chart\|values\|readme\|crds\|all <chart>` | a chart's contents, not installed | `--version` |
| `helm pull <chart> --version X` | downloads the archive | `--untar` to read it; the way to mirror third-party charts |
| `helm package <dir>` | makes `name-version.tgz` | `--version`, `--app-version` override `Chart.yaml`; `--dependency-update`; `-d <dir>` |
| `helm push <tgz> oci://<registry>/<path>` | to an OCI registry | `helm/repositories.md` |
| `helm registry login\|logout <host>` | OCI credentials | `--password-stdin` |
| `helm repo add\|update\|list\|remove` | HTTP repositories | `--password-stdin` on `add` |
| `helm search repo <name> --versions` | versions in added repositories | `search hub` needs the internet: never |
| `helm dependency build\|update\|list <chart>` | subcharts into `charts/` | `helm/repositories.md` |
| `helm verify <tgz>` | checks a `.prov` signature | needs the signer's public key |
| `helm plugin list\|install\|uninstall\|update` | plugins | below |
| `helm completion powershell` | tab completion | `helm completion powershell \| Out-String \| Invoke-Expression` in the profile |

Output formats: `-o table` (default), `json`, `yaml` on `list`, `status`,
`history`, `get values`. Parse `json` with `ConvertFrom-Json` in
PowerShell, never the table.

## Plugins, offline

Plugins are not part of Helm; check `helm plugin list` before relying on
one. Air gapped, install from a folder or archive from the mirror.

*lab, helm-diff 3.15.14, Linux build of the plugin; the Windows archive has the same layout with `diff.exe`:*
- **From the unpacked folder**, Helm 4 and 3 alike:
  `helm plugin install .\helm-diff-windows-amd64` → `Installed plugin:
  diff`; it then shows as `APIVERSION legacy` in Helm 4 and works (`helm
  diff upgrade ...` printed the changed `replicas`).
- **From the archive**, Helm 4 checks a signature: `Error: plugin
  verification failed: no provenance file (.prov) found`. `--verify=false`
  skips the check (Helm warns); use the folder instead.
- `HELM_NO_PLUGINS=1` disables plugins.

`helm diff upgrade <release> <chart> -n <ns> -f <values> [--reuse-values]`
shows what an upgrade would change; `--allow-unreleased` for a release
that does not exist yet.
