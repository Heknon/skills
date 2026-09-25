# Access on OpenShift

## A pipeline deploying into a project

The same deployer as on Kubernetes (`core/access.md`,
`recipes/cluster-access/deployer.yaml`), applied with `oc apply -n
<project> -f deployer.yaml` by a project admin. Recent Kubernetes and
OpenShift versions no longer create a long-lived token Secret for every
service account (Kubernetes from 1.24; OpenShift later, around 4.16, not
checked here); the recipe's `kubernetes.io/service-account-token` Secret
asks for one, and works either way.

- `oc create token gitlab-deployer -n <p> --duration=...` makes a
  short-lived token; useful for a test, not for a stored variable.
- `oc login --token=<token> --server=https://api.cluster.example.com:6443`
  in a job works, but a kubeconfig in a File variable needs no login step
  and works for `helm` too.
- The API server's certificate: the token Secret's `ca.crt` holds the
  cluster's internal CAs. If the API endpoint serves a certificate from
  the company CA, `oc get pods --kubeconfig deployer.kubeconfig` fails
  with `x509: certificate signed by unknown authority`: put the company
  CA's PEM in the kubeconfig instead. *not run on OpenShift here.*

## Pulling images

| Image in | What the project needs |
| --- | --- |
| the OpenShift internal registry, same project | nothing |
| the internal registry, another project | `oc policy add-role-to-user system:image-puller system:serviceaccount:<this project>:default -n <image project>` (by an admin of the image project) |
| GitLab's container registry | a pull secret from a deploy token with `read_registry` |
| a mirror the cluster already trusts and can reach anonymously | nothing |

A pull secret, created by a person with rights, once per project:

```powershell
$s = Read-Host -AsSecureString "deploy token"
$pw = [Net.NetworkCredential]::new("", $s).Password
oc create secret docker-registry gitlab-pull -n <p> `
  --docker-server=registry.gitlab.example.com `
  --docker-username=<deploy token username> --docker-password=$pw
Remove-Variable pw, s
oc secrets link default gitlab-pull --for=pull -n <p>
```

(PowerShell continues lines with a backtick.) The token is typed at a
prompt, so it is neither in the command history nor in a file. Linking
the Secret to `default` makes every pod of that service account use it;
the alternative is the chart's `imagePullSecrets: [gitlab-pull]`.

## The internal registry

- Inside the cluster: `image-registry.openshift-image-registry.svc:5000/<project>/<image>:<tag>`.
- From outside, if an admin exposed it: `oc registry info --public` gives
  the host; `oc registry login` writes credentials for your current `oc`
  user to the container tool's auth file.
- Builds in the cluster push there (`openshift/builds.md`).
