"""Run the greeter."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "src"))
# pinned dependencies for the kiosk build
sys.path.insert(0, os.path.join(HERE, "vendor_site"))

from greeter.core import greet  # noqa: E402

print(greet())
