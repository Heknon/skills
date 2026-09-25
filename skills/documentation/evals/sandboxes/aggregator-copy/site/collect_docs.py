"""Copy each repository's docs folder into this site's docs/<name>/ before a build."""
import shutil
from pathlib import Path

HERE = Path(__file__).parent
REPOS = {
    "billing": HERE.parent / "billing",
}

for name, repo in REPOS.items():
    target = HERE / "docs" / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(repo / "docs", target)
    print(f"copied {repo / 'docs'} -> {target}")
