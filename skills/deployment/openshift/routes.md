# Routes

A Route sends traffic from the cluster's router (HAProxy) to a Service.
The generic chart renders one with `route.enabled: true`; the manifest was
validated against the Route API definition published in the openshift/api project, on a
Kubernetes API server (lab), not served by a real router.

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: web
  annotations:
    haproxy.router.openshift.io/timeout: 60s
spec:
  host: web.example.com          # optional
  to:
    kind: Service
    name: web
    weight: 100
  port:
    targetPort: http              # the Service port's name
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

## Host

- Without `spec.host`, OpenShift generates `<route name>-<project>.<apps
  domain>`, such as `web-shop-staging.apps.cluster.example.com`. Staging
  usually leaves it out; production sets the public name.
- Setting a host needs the right to create `routes/custom-host`; the
  `edit` role has it.
- A host is taken by the first Route that claims it, across projects,
  unless admins allow otherwise. A second Route with the same host shows
  `HostAlreadyClaimed` in `oc describe route`.
- The DNS name must resolve to the router: the apps wildcard does; a
  public name needs a DNS record from whoever owns the domain.

## TLS

| `termination` | TLS ends at | Certificate |
| --- | --- | --- |
| `edge` | the router; plain HTTP to the pod | the router's default wildcard, or `tls.certificate` and `tls.key` in the Route |
| `reencrypt` | the router, then new TLS to the pod | as edge, plus `tls.destinationCACertificate` to trust the pod |
| `passthrough` | the pod | the pod's own; the router sees no HTTP, so no path routing and no HTTP annotations |

`insecureEdgeTerminationPolicy`: `Redirect` (HTTP to HTTPS), `Allow`, or
`None`. Not used with passthrough.

A certificate in the Route is stored in the Route object; do not put one
in a values file. Ask how the platform issues certificates (cert-manager
with a Route integration, or the wildcard).

## Common annotations

| Annotation | Effect |
| --- | --- |
| `haproxy.router.openshift.io/timeout: 60s` | request timeout at the router, default 30s: slow endpoints get `504` without it |
| `haproxy.router.openshift.io/ip_allowlist: 10.0.0.0/8 192.168.1.10` | only these sources |
| `haproxy.router.openshift.io/balance: roundrobin` | load balancing algorithm |
| `router.openshift.io/cookie_name: web` | sticky sessions cookie name |

## Checking a Route

```
oc get route -n <p>                      # HOST/PORT column; empty means not admitted
oc describe route web -n <p>             # admission status, conditions such as HostAlreadyClaimed
curl.exe -sS -o NUL -w "%{http_code}" https://<host>/healthz
```

`503` from the router with its "Application is not available" page means
no ready pod behind the Service: check the pods' readiness
(`kubernetes/debugging.md`), then that the Service's selector matches the
pods and the Route's `targetPort` names a Service port.
