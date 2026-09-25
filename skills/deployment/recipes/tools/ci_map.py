"""Map a GitLab project's CI/CD configuration: where it comes from, every include,
every job, and every downstream pipeline, followed recursively. Read only.

Usage (PowerShell or a shell; the token is read from the environment):
    $env:GITLAB_URL = "https://gitlab.example.com"
    $env:GITLAB_TOKEN = <read_api token, or api to also resolve child pipeline files>
    uv run ci_map.py group/project [--ref main] [--runtime] [--depth 3]
    uv run ci_map.py --consumers platform/templates --group shop

Optional: GITLAB_CA_FILE, a PEM file with the CA of the GitLab server.
Standard library only; Python 3.10 or later.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

URL = os.environ.get("GITLAB_URL", "").rstrip("/")
TOKEN = os.environ.get("GITLAB_TOKEN", "")
CA = os.environ.get("GITLAB_CA_FILE")
CTX = ssl.create_default_context(cafile=CA) if CA else ssl.create_default_context()


class ApiError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:200]}")
        self.status = status


def api(path: str, data: dict | None = None, raw: bool = False):
    req = urllib.request.Request(
        f"{URL}/api/v4{path}",
        data=json.dumps(data).encode() if data is not None else None,
        headers={"PRIVATE-TOKEN": TOKEN, "Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, context=CTX) as r:
            body = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read().decode(errors="replace")) from None
    return body if raw else json.loads(body)


def enc(s: str) -> str:
    return urllib.parse.quote(str(s), safe="")


def unquote(v: str) -> str:
    v = v.strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"" else v


def triggers(merged_yaml: str) -> dict[str, dict]:
    """Trigger blocks of top-level jobs, read from GitLab's normalized merged_yaml."""
    out: dict[str, dict] = {}
    job = None
    in_trigger = False
    item: dict | None = None
    for line in merged_yaml.splitlines():
        if line and not line.startswith(" ") and line.rstrip().endswith(":"):
            job, in_trigger, item = line.rstrip()[:-1].strip("\"'"), False, None
            continue
        if job is None:
            continue
        if line.startswith("  trigger:"):
            in_trigger, item = True, None
            out[job] = {"include": [], "project": None, "branch": None}
            rest = line.split(":", 1)[1].strip()
            if rest:  # trigger: group/project
                out[job]["project"] = unquote(rest)
            continue
        if in_trigger:
            if not line.startswith("    "):
                in_trigger = False
                continue
            m = re.match(r"^    (project|branch|include|strategy):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2)
                if key in ("project", "branch"):
                    out[job][key] = unquote(val)
                elif key == "include" and val:
                    out[job]["include"].append({"local": unquote(val)})
                continue
            m = re.match(r"^    - (\w+):\s*(.*)$", line)
            if m:
                item = {m.group(1): unquote(m.group(2))}
                out[job]["include"].append(item)
                continue
            m = re.match(r"^      (\w+):\s*(.*)$", line)
            if m and item is not None:
                item[m.group(1)] = unquote(m.group(2))
            m = re.match(r"^    - (\S.*)$", line)
            if m and ":" not in m.group(1):
                out[job]["include"].append({"local": unquote(m.group(1))})
    return out


def show_includes(includes: list, pad: str) -> None:
    if not includes:
        print(f"{pad}includes: none")
        return
    print(f"{pad}includes:")
    for i in includes:
        extra = i.get("extra") or {}
        where = i["location"]
        if extra.get("project"):
            where = f"{extra['project']}:{i['location']} @ {extra.get('ref')}"
        note = ""
        if extra.get("ref") == "HEAD":
            note = "   <- not pinned: follows that project's default branch"
        if extra.get("rules"):
            note += f"   rules: {json.dumps(extra['rules'])}"
        ctx = i.get("context_project")
        print(f"{pad}  {i['type']:<9} {where}{note}   (from {ctx})")


def lint_content(project: str, content: str) -> dict | None:
    try:
        return api(f"/projects/{enc(project)}/ci/lint?include_jobs=true", {"content": content})
    except ApiError as e:
        if e.status == 403:
            return None  # POST lint needs the api scope
        raise


def show_config(project: str, lint: dict, pad: str, depth: int, seen: set) -> None:
    if not lint.get("valid"):
        print(f"{pad}INVALID: {lint.get('errors')}")
    for w in lint.get("warnings") or []:
        print(f"{pad}warning: {w}")
    show_includes(lint.get("includes") or [], pad)
    jobs = [j["name"] + ("" if j.get("when") in (None, "on_success") else f" ({j['when']})")
            for j in lint.get("jobs") or []]
    label = lint.get("_jobs_label", "jobs defined, rules not evaluated")
    print(f"{pad}{label} ({len(jobs)}): {', '.join(jobs) or 'none'}")
    for job, t in triggers(lint.get("merged_yaml") or "").items():
        if t["project"]:
            print(f"{pad}trigger {job} -> multi-project pipeline in {t['project']}"
                  f" (branch {t['branch'] or 'its default'})")
            if depth > 0:
                map_project(t["project"], t["branch"], pad + "    ", depth - 1, seen)
            continue
        for inc in t["include"]:
            if "artifact" in inc:
                print(f"{pad}trigger {job} -> dynamic child pipeline from artifact {inc['artifact']}"
                      f" of job {inc.get('job')}: its content exists only after that job ran"
                      f" (read it: GET /projects/:id/jobs/<job id>/artifacts/{inc['artifact']})")
            elif "local" in inc or "file" in inc:
                path = inc.get("local") or inc.get("file")
                src = inc.get("project", project)
                print(f"{pad}trigger {job} -> child pipeline {src}:{path}")
                if depth > 0:
                    show_child(project, src, path, inc.get("ref"), pad + "    ", depth - 1, seen)
            elif "component" in inc:
                print(f"{pad}trigger {job} -> child pipeline from component {inc['component']}")
            else:
                print(f"{pad}trigger {job} -> {inc}")


def show_child(project: str, src: str, path: str, ref: str | None, pad: str, depth: int, seen: set) -> None:
    content = (f"include:\n  - project: {src}\n    file: {path}\n" + (f"    ref: {ref}\n" if ref else "")
               if src != project else f"include:\n  - local: {path}\n")
    lint = lint_content(project, content)
    if lint is None:
        print(f"{pad}not resolved: linting a child file needs a token with the api scope;"
              f" read it with GET /projects/{enc(src)}/repository/files/{enc(path.lstrip('/'))}/raw")
        return
    show_config(project, lint, pad, depth, seen)


def map_project(project: str, ref: str | None, pad: str, depth: int, seen: set) -> None:
    key = (project, ref)
    if key in seen:
        print(f"{pad}{project}: already shown above")
        return
    seen.add(key)
    try:
        p = api(f"/projects/{enc(project)}")
    except ApiError as e:
        print(f"{pad}{project}: cannot read ({e}); a 404 also means no access")
        return
    ref = ref or p.get("default_branch")
    cfg = p.get("ci_config_path")
    print(f"{pad}project {p['path_with_namespace']} (id {p['id']}), ref {ref}")
    if cfg and "@" in cfg:
        file, rest = cfg.split("@", 1)
        other, _, other_ref = rest.partition(":")
        print(f"{pad}config: EXTERNAL, {file} in project {other}"
              f"{' @ ' + other_ref if other_ref else ' (its default branch)'}; this repository's own"
              f" .gitlab-ci.yml is not used")
        content = f"include:\n  - project: {other}\n    file: {file}\n" + (f"    ref: {other_ref}\n" if other_ref else "")
        lint = lint_content(project, content)
        if lint is None:
            print(f"{pad}not resolved: needs a token with the api scope; read the file in {other}")
            return
        show_config(project, lint, pad, depth, seen)
        return
    path = cfg or ".gitlab-ci.yml"
    try:
        api(f"/projects/{enc(project)}/repository/files/{enc(path)}?ref={enc(ref)}")
    except ApiError as e:
        if e.status != 404:
            raise
        if p.get("auto_devops_enabled"):
            print(f"{pad}config: no {path} on {ref}; Auto DevOps is enabled for the project, so GitLab"
                  f" runs its Auto DevOps template instead (what follows is that template)")
        else:
            print(f"{pad}config: no {path} on {ref} and Auto DevOps is off: no pipelines run")
            return
    else:
        print(f"{pad}config: {path} in this repository" + ("" if cfg else " (the default path)"))
    try:
        lint = api(f"/projects/{enc(project)}/ci/lint?include_jobs=true&content_ref={enc(ref)}"
                   f"&dry_run=true&dry_run_ref={enc(ref)}")
        lint["_jobs_label"] = f"jobs a pipeline for a push to {ref} would have, rules evaluated"
    except ApiError as e:
        print(f"{pad}lint failed: {e}")
        return
    show_config(project, lint, pad, depth, seen)


def runtime(project: str, pipeline_id: int, pad: str, depth: int) -> None:
    pl = api(f"/projects/{enc(project)}/pipelines/{pipeline_id}")
    jobs = api(f"/projects/{enc(project)}/pipelines/{pipeline_id}/jobs?per_page=100")
    print(f"{pad}pipeline {pipeline_id} in {project}: {pl['status']}, source {pl['source']}, ref {pl['ref']}")
    for j in sorted(jobs, key=lambda j: j["id"]):
        print(f"{pad}  job {j['name']} [{j['stage']}] {j['status']}")
    for b in api(f"/projects/{enc(project)}/pipelines/{pipeline_id}/bridges?per_page=100"):
        d = b.get("downstream_pipeline")
        if not d:
            print(f"{pad}  trigger {b['name']} {b['status']}: no downstream pipeline")
            continue
        dproj = api(f"/projects/{d['project_id']}")["path_with_namespace"]
        print(f"{pad}  trigger {b['name']} {b['status']} -> pipeline {d['id']} in {dproj}")
        if depth > 0:
            runtime(dproj, d["id"], pad + "      ", depth - 1)


def consumers(template: str, group: str) -> None:
    projects = api(f"/groups/{enc(group)}/projects?include_subgroups=true&per_page=100&archived=false")
    print(f"projects in {group} whose configuration uses {template}:")
    found = 0
    for p in projects:
        cfg = p.get("ci_config_path") or ""
        if "@" in cfg and cfg.split("@", 1)[1].split(":")[0] == template:
            print(f"  {p['path_with_namespace']}: its whole configuration is {cfg}")
            found += 1
            continue
        try:
            lint = api(f"/projects/{p['id']}/ci/lint")
        except ApiError:
            continue
        for i in lint.get("includes") or []:
            proj = (i.get("extra") or {}).get("project")
            if proj == template or f"/{template}/" in i["location"]:
                ref = (i.get("extra") or {}).get("ref", "")
                print(f"  {p['path_with_namespace']}: {i['type']} {i['location']} {('@ ' + ref) if ref else ''}")
                found += 1
    print(f"{found} uses found; only default branches were read")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?")
    ap.add_argument("--ref")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--runtime", action="store_true", help="also show the latest pipeline on the ref and its downstream pipelines")
    ap.add_argument("--consumers", metavar="TEMPLATE_PROJECT")
    ap.add_argument("--group")
    a = ap.parse_args()
    if not URL or not TOKEN:
        print("set GITLAB_URL and GITLAB_TOKEN", file=sys.stderr)
        return 2
    if a.consumers:
        if not a.group:
            print("--consumers needs --group", file=sys.stderr)
            return 2
        consumers(a.consumers, a.group)
        return 0
    if not a.project:
        ap.print_help()
        return 2
    print(f"GitLab {api('/version')['version']}")
    map_project(a.project, a.ref, "", a.depth, set())
    if a.runtime:
        p = api(f"/projects/{enc(a.project)}")
        ref = a.ref or p["default_branch"]
        latest = api(f"/projects/{enc(a.project)}/pipelines?ref={enc(ref)}&per_page=1")
        print()
        if latest:
            runtime(a.project, latest[0]["id"], "", a.depth)
        else:
            print(f"no pipeline on {ref} yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
