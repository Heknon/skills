# RBAC

Who may do what in a namespace. Checked on a Kubernetes 1.37 API server
(lab).

## Ask the API

```
kubectl auth can-i create deployments -n shop-staging
kubectl auth can-i create deployments -n shop-staging --as system:serviceaccount:shop-staging:gitlab-deployer
kubectl auth can-i --list -n shop-staging --as system:serviceaccount:shop-staging:gitlab-deployer
```

`--as` needs impersonation rights (cluster admins have them). Without
them, run `kubectl auth can-i` with the deployer's own kubeconfig.

## The built-in roles, per namespace

| ClusterRole bound in a namespace | Allows |
| --- | --- |
| `view` | read most objects; not Secrets |
| `edit` | create, change and delete workloads, Services, ConfigMaps, Secrets, Jobs, HPAs, PDBs; on OpenShift also Routes, BuildConfigs, ImageStreams. Not Roles or RoleBindings (lab: `no` for rolebindings) |
| `admin` | `edit` plus Roles and RoleBindings in the namespace |

These are aggregated: operators add rules for their own resources with
the label `rbac.authorization.k8s.io/aggregate-to-edit: "true"`. The lab
added Routes to `edit` this way, as OpenShift does.

Helm stores releases as Secrets of type `helm.sh/release.v1` in the
release's namespace, so its identity needs Secrets rights there; `edit`
has them.

## Errors

- `Forbidden: User "system:serviceaccount:shop-staging:gitlab-deployer"
  cannot list resource "pods" in API group "" in the namespace
  "shop-production"` (lab): the identity has no role in that namespace.
  The fix is the right kubeconfig for that environment, not a wider role.
- `Unauthorized`: the token is wrong, expired, or its Secret was deleted.
