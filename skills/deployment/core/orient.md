# Orient

**Verdict you produce:** the path from a commit to a running workload in
this project, one hop per line, each with the file or command that shows
it, and the hops you could not see.

```
trigger:     <which pushes, merge requests and tags create a pipeline>   (<file:line>)
checks:      <lint and test jobs>                                       (<file:line>)
image:       <job, builder, image name and tag scheme>                  (<file:line>)
chart:       <chart, where it comes from, its version>                  (<file:line>)
values:      <values files per environment>                             (<paths>)
deploy:      <job per environment, command, manual or automatic>        (<file:line>)
identity:    <how the job reaches the cluster: variable name, scope>    (<settings or file>)
target:      <cluster, namespace per environment>                       (<file:line or setting>)
not seen:    <hops that live outside the repository>
```

## Steps

1. **Find the pipeline configuration.** `.gitlab-ci.yml` at the root,
   unless the project sets another path: `ci_config_path` from
   `GET /projects/:id` (Settings > CI/CD > General pipelines > CI/CD
   configuration file). It can name a file in another project
   (`file.yml@group/project`), in which case the repository may have no
   CI file at all. Read the file whole.
2. **Resolve every include.** For the whole map, including child and
   multi-project pipelines and configuration kept in another project, use
   `core/discover.md`; what follows is the short version. For each `include:` entry, note its kind
   (`gitlab/includes-and-components.md`): `local` files are read from this
   repository; `project`, `component` and `template` entries live
   elsewhere. Read what you can reach. Better than reading: ask GitLab.
   The CI lint API returns `merged_yaml`, the configuration with every
   include resolved, and with `dry_run=true&include_jobs=true` and the ref
   it lists the jobs a pipeline on that ref would have, with their `when`
   (`gitlab/api.md`). That answers "what runs on a tag" without pushing
   one. It cannot simulate a merge request pipeline.
3. **Read `workflow:rules`** to know which events create a pipeline
   (`gitlab/rules.md`).
4. **List the jobs by stage**, and for each its `rules`, `needs`,
   `environment` and `image`. The deploy jobs are the ones with
   `environment:` or with `helm`, `kubectl`, `oc` in their script.
5. **Follow the image**: the job that builds it, the tag it pushes, and how
   the deploy job learns it (`--set image.tag=...`, a dotenv report, a
   values file).
6. **Follow the chart**: a folder in the repository (`Chart.yaml`), a
   repository (`helm repo add`), or an OCI reference (`oci://`). Note the
   version and where it is pinned.
7. **Find the cluster identity**: a `KUBECONFIG` or token variable, the
   GitLab agent (`environment:kubernetes`, a `.gitlab/agents/` folder),
   or `oc login` in a script. Variables are in Settings > CI/CD >
   Variables at project, group and instance level; list them without
   values (`gitlab/api.md`).
8. **Name the target**: `--namespace`, `KUBE_NAMESPACE`, the kubeconfig's
   context, or the agent's configuration.
9. **Check it against reality** when you can read the cluster: `helm list
   -n <namespace>` shows the release and chart version; `helm history`
   shows when and what revision.

## Never

- Never describe the pipeline from the job names. A job called `deploy`
  may only render templates.
- Never assume the included files are what the repository says: a
  `project` include without `ref` follows that project's default branch.
- Never print variable values while listing them.

## Stop and ask

- The configuration includes a project you cannot read. Name the project
  and file, and ask for access or its content.
- The pipeline deploys with something not in this skill, such as Argo CD
  applications in another repository. Describe the hop you can see, and
  ask where the rest lives.
