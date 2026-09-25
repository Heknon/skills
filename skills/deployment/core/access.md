# Access

Two directions: a pipeline reaching a cluster, and you (or a script)
reaching GitLab.

## A pipeline reaching a cluster

**Verdict you produce:** the identity, what it may do, where its
credential is kept, and who rotates it.

```
mechanism:  <service account token in a File variable | GitLab agent for Kubernetes | GitOps pull>
identity:   system:serviceaccount:<namespace>:gitlab-deployer
may:        edit role in <namespace> only       (shown by: kubectl auth can-i ...)
credential: KUBECONFIG, File, protected, scope <environment>, in <project or group>
rotation:   <who, how: delete and re-apply the token Secret, update the variable>
```

### Choose the mechanism

1. **Does the organisation already run Argo CD or OpenShift GitOps?** Then
   the pipeline does not deploy: it builds the image and commits the new
   digest to the GitOps repository, and the controller applies it. Out of
   this skill's depth beyond that; say so.
2. **Is the GitLab agent for Kubernetes installed and connected** (a
   `.gitlab/agents/<name>/config.yaml` in a project, and the agent listed
   under Operate > Kubernetes clusters)? Then jobs use its context,
   `kubectl config use-context <project path>:<agent name>`, and no cluster
   credential is stored in GitLab. Access is granted in the agent's
   configuration (`ci_access`).
3. **Otherwise: a service account per namespace**, its token in a
   kubeconfig, in a File variable scoped to the environment. Works on any
   cluster and any GitLab, air gapped. Recipe: `recipes/cluster-access/`.

### Set up a service account deployer

Done by a namespace administrator, not by the pipeline.

1. `kubectl apply -n <ns> -f recipes/cluster-access/deployer.yaml`
   (`oc apply` on OpenShift). It creates the `gitlab-deployer` service
   account, binds it to the built-in `edit` role in that namespace only,
   and asks for a long-lived token Secret.
2. Check what it may do. In the lab: `yes` to deployments and routes in
   its namespace, `no` to another namespace, `no` to rolebindings.
   ```
   kubectl auth can-i create deployments -n <ns> --as system:serviceaccount:<ns>:gitlab-deployer
   kubectl auth can-i create deployments -n <other ns> --as system:serviceaccount:<ns>:gitlab-deployer
   ```
3. Build the kubeconfig. These commands are the same in PowerShell and a
   POSIX shell except the variable syntax; PowerShell shown:
   ```
   $ns = "shop-staging"; $kc = "deployer.kubeconfig"
   $ca = kubectl get secret gitlab-deployer-token -n $ns -o jsonpath='{.data.ca\.crt}'
   $token = kubectl get secret gitlab-deployer-token -n $ns -o go-template='{{.data.token | base64decode}}'
   kubectl config set-cluster cluster --server=https://api.cluster.example.com:6443 --kubeconfig $kc
   kubectl config set clusters.cluster.certificate-authority-data $ca --kubeconfig $kc
   kubectl config set-credentials gitlab-deployer --token=$token --kubeconfig $kc
   kubectl config set-context deploy --cluster=cluster --user=gitlab-deployer --namespace=$ns --kubeconfig $kc
   kubectl config use-context deploy --kubeconfig $kc
   kubectl get pods --kubeconfig $kc
   ```
   `$token` stays in a variable: never paste a token into a command line,
   which the shell's history keeps. `Remove-Variable token` afterwards.
   The last command must answer (or say `No resources found`), not
   `Forbidden` or a certificate error. If it is `x509: certificate signed
   by unknown authority`, the API server's certificate comes from another
   CA (OpenShift with a custom API certificate): set that CA's PEM,
   base64 encoded, instead. Never `insecure-skip-tls-verify`.
4. A Maintainer stores the file's content as a CI/CD variable: key
   `KUBECONFIG`, type File, protected, environment scope `staging` (or
   `staging/*`). Helm and kubectl read `KUBECONFIG` as a path, which is
   what a File variable gives. Then delete the local file.
5. Rotate: delete the Secret `gitlab-deployer-token`, apply the recipe
   again, rebuild the kubeconfig, update the variable.

## You or a script reaching GitLab

**Verdict you produce:** the token, its scope, and how it is passed.

| Caller | Token | Header |
| --- | --- | --- |
| a job, calling its own project's API, packages or registry | `CI_JOB_TOKEN` | `JOB-TOKEN: $CI_JOB_TOKEN`, or basic auth user `gitlab-ci-token` |
| a job, calling another project | `CI_JOB_TOKEN`, with this project in the other's allowlist (`gitlab/job-token.md`) | same |
| automation outside CI, for one project | a project access token, least role and scopes | `PRIVATE-TOKEN: <token>` |
| a person at a terminal | a personal access token with `read_api` for reading, `api` only for changing | `PRIVATE-TOKEN: <token>` |
| a cluster pulling images | a deploy token with `read_registry` | registry login |

Keep a personal token out of files and history: in PowerShell, read it
into a session variable with
`$env:GITLAB_TOKEN = Read-Host -MaskInput "token"` (PowerShell 7; in
Windows PowerShell 5.1: `$s = Read-Host -AsSecureString "token"` then
`$env:GITLAB_TOKEN = [Net.NetworkCredential]::new("", $s).Password`) and use
`glab` (`gitlab/glab.md`) or the API (`gitlab/api.md`), which both read it.

## Never

- Never give the deployer a ClusterRole binding, `admin`, or access to a
  second namespace "for later".
- Never store a person's own kubeconfig or `oc whoami -t` token in a CI/CD
  variable: it expires, and it carries that person's rights.
- Never use an `oc login` token in a pipeline; use the service account's.

## Stop and ask

- You do not have rights to create the service account or the variable.
  Hand the steps above to the person who does, as the answer.
