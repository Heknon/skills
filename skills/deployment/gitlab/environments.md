# Environments and deployment control

Checked against GitLab 19.4 documentation; *lab* marks what ran on 19.4.1
(Free tier).

## Environments

```yaml
deploy-staging:
  environment:
    name: staging
    url: https://web-shop-staging.apps.example.com
    deployment_tier: staging
```

- A job with `environment:` records a deployment; the environment page
  lists them and can re-run an earlier one ("rollback" in GitLab re-runs
  that old deploy job with its old commit).
- `name` may hold variables and slashes: `review/$CI_COMMIT_REF_SLUG`,
  `staging/api`. Slashes group environments in folders, and variable
  scopes like `staging/*` match them.
- CI/CD variables with an environment scope reach only jobs whose
  environment matches (*lab*).
- `deployment_tier`: `production`, `staging`, `testing`, `development`,
  `other`; guessed from the name when absent.

## Controlling who deploys to production

| Control | Tier | How |
| --- | --- | --- |
| manual job | Free | `when: manual` in the rule; the pipeline waits (*lab*) |
| protected tags or branches | Free | only Maintainers (or the roles you allow) push `v*` tags or merge to the default branch; production jobs run only there |
| protected variables | Free | the production `KUBECONFIG` is protected, so an unprotected ref cannot deploy even if someone edits the rules (*lab:* the job failed with `kubernetes cluster unreachable`) |
| resource group | Free | one production deploy at a time |
| protected environments | Premium | only listed users, groups or roles can run jobs for that environment |
| deployment approvals | Premium | a deploy job waits for N approvals |

On Free, the combination of a manual job on a protected tag and a
protected, environment-scoped credential is what keeps production safe.
Check the tier: the Help page or `GET /api/v4/license` (administrators)
shows it; the API's `/version` response carries `"enterprise": false` on
Community Edition (*lab*).

## Resource groups

`resource_group: production` makes jobs with that name run one at a time
across every pipeline of the project, in the order set by the group's
`process_mode` (`unordered` default, `oldest_first`, `newest_first`,
`newest_ready_first`; changed through the API). A job waiting shows
`waiting_for_resource` (*lab*).

## Review apps

One environment per merge request, stopped when the merge request closes:

```yaml
review:
  stage: deploy
  script:
    - helm upgrade --install "review-$CI_MERGE_REQUEST_IID" ...
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://review-$CI_MERGE_REQUEST_IID.apps.example.com
    on_stop: stop-review
    auto_stop_in: 3 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop-review:
  stage: deploy
  script:
    - helm uninstall "review-$CI_MERGE_REQUEST_IID" --namespace "$KUBE_NAMESPACE"
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual
      allow_failure: true
```

`allow_failure: true` keeps the manual stop job from blocking the
pipeline. Both jobs need the same `rules` event, and the stop job must be able to
run after the branch is deleted (it runs from the merge request's
pipeline). Review namespaces need their own deployer and quota.
