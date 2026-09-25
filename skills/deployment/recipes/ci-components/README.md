# CI/CD components

Shared pipeline building blocks. Include a component by version; never by branch
in a production pipeline.

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/ci-components/python-checks@1.0.0
    inputs:
      job-prefix: api
      working-directory: services/api
```

## Components

### python-checks

Ruff and pytest for a uv project, or one member of a uv workspace (`package`).
Jobs: `<job-prefix>-lint`, `<job-prefix>-test`.

### buildah-image

Builds the image once per commit with rootless Buildah, tags it with the commit
SHA (and the Git tag in a tag pipeline), and passes the digest on as
`<dotenv-prefix>IMAGE_DIGEST`. Needs a runner that allows it (Buildah needs
seccomp unconfined on the Docker executor). Optional File variables
`INTERNAL_CA` and `INDEX_NETRC` are passed to the build as secrets.

### helm-deploy

`helm upgrade --install` of a chart from a GitLab Helm repository into one
namespace, with `--wait` and `--rollback-on-failure`. Needs a File variable
`KUBECONFIG` scoped to the environment, and the chart project must allow this
project's job token.

### python-publish

On a tag, builds the package with `uv build` and publishes it to the project's
PyPI registry with the job token.

## Release

Push a tag `X.Y.Z`. The tag pipeline tests every component and creates the release.
