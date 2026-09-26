"""Make a repository with pre-commit installed and two new files staged.

Run once, before the eval, with the package index or mirror reachable:
    uv run --no-project python make_sandbox.py
"""

import pathlib
import subprocess


def run(*cmd: str) -> None:
    subprocess.run(cmd, check=True)


run("git", "init", "-q", "-b", "main")
run("git", "config", "user.email", "dev@example.com")
run("git", "config", "user.name", "Dev")
run("uv", "lock", "-q")
run("uv", "sync", "-q")
run("git", "add", "-A", ":!make_sandbox.py")
run("git", "commit", "-q", "-m", "Add cart totals")
run("uv", "run", "--frozen", "pre-commit", "install")
pathlib.Path("src/cart/tax.py").write_text(
    "RATES = {'standard': 20, 'reduced': 5}\n"
    "def tax_cents(net_cents:int, rate:str='standard')->int:\n"
    "    return net_cents*RATES[rate]//100\n"
)
pathlib.Path("src/cart/shipping.py").write_text(
    "def shipping_cents(weight_g:int)->int:\n"
    "    if weight_g<=1000: return 490\n"
    "    return 490+ (weight_g-1000)//500*150\n"
)
run("git", "add", "src/cart/tax.py", "src/cart/shipping.py")
pathlib.Path("make_sandbox.py").unlink()
