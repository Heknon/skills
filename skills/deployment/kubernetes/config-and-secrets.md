# Configuration and secrets

## Where each kind of value goes

| Value | Place | Chart |
| --- | --- | --- |
| plain setting, per environment | values file, as an environment variable | `env` |
| a configuration file | values file, rendered into a ConfigMap and mounted | `config.files`, `config.mountPath` |
| a secret the app reads | a Secret in the namespace, created outside the chart, referenced by name | `envFromSecrets` |
| a secret file (certificate, key) | a Secret mounted as a volume; add the option to the chart if missing | |

## Secrets are created outside the chart

The chart references Secrets by name and never holds their values: Helm
stores every value it was given in the release, readable with `helm get
values` by anyone who can read Secrets in the namespace.

Ways a Secret gets into the namespace, most controlled first:

1. **An operator syncing from a vault** (External Secrets Operator, the
   Vault agent, a cloud secret store CSI driver): the cluster pulls the
   value; nothing secret passes through Git or GitLab. Check with the
   platform team whether one is installed (`kubectl get crd | findstr
   externalsecrets` in PowerShell).
2. **Sealed Secrets**: an encrypted manifest in Git that only the cluster
   can decrypt. Needs its controller.
3. **Created by a person with rights**, once per environment:
   `kubectl create secret generic web-secrets -n <ns> --from-env-file=<file>`,
   the file deleted afterwards. Record who owns rotation.

The deploy pipeline does not create application Secrets from CI/CD
variables: that puts every application secret in GitLab, readable by
every Maintainer and by any job on a protected branch.

## Taking a change into use

- A ConfigMap rendered by the chart: the checksum annotation changes the
  pod template, so pods roll on the next deploy.
- A Secret or ConfigMap changed outside the chart: running pods keep the
  old environment. `kubectl rollout restart deployment/<name> -n <ns>`
  replaces them (*changes*; say so). Mounted files update by themselves
  after a delay, environment variables never do.

## Reading without revealing

- `kubectl get secret web-secrets -n <ns> -o jsonpath='{.data}'` shows
  base64 values: that is revealing. To check presence and keys:
  `kubectl get secret web-secrets -n <ns> -o go-template='{{range $k, $v := .data}}{{$k}} {{end}}'`.
- `kubectl describe secret` shows keys and sizes, not values.
