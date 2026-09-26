"""Eval setup: build a git repository with 31 commits and one regression.

Run once in an empty folder, then delete this file:
    uv run python setup.py
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).parent

FILES = {
    "pyproject.toml": """[project]
name = "units"
version = "1.4.0"
requires-python = ">=3.12"

[dependency-groups]
dev = ["pytest>=8.4"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
""",
    ".gitignore": ".venv/\n__pycache__/\n.pytest_cache/\nsetup.py\n",
    "units/__init__.py": "",
    "units/mass.py": '''POUND_IN_KG = 0.45359237


def to_kg(pounds):
    """Pounds to kilograms, rounded to the gram."""
    return round(pounds * POUND_IN_KG, 3)
''',
    "units/length.py": '''MILE_IN_KM = 1.609344


def to_km(miles):
    """Miles to kilometres, rounded to the metre."""
    return round(miles * MILE_IN_KM, 3)
''',
    "tests/test_units.py": '''from units.length import to_km
from units.mass import to_kg


def test_pounds_to_kg():
    assert to_kg(2.5) == 1.134


def test_miles_to_km():
    assert to_km(3) == 4.828
''',
    "README.md": "# units\n\nSmall unit conversions for the shipping service.\n",
}


def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True)


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def append(path, text):
    write(path, (ROOT / path).read_text(encoding="utf-8") + text)


def replace(path, old, new):
    text = (ROOT / path).read_text(encoding="utf-8")
    assert old in text, (path, old)
    write(path, text.replace(old, new))


def commit(message):
    git("add", "-A")
    git("commit", "-q", "-m", message)


TEMPERATURE = '''def to_celsius(fahrenheit):
    """Fahrenheit to Celsius, one decimal."""
    return round((fahrenheit - 32) * 5 / 9, 1)
'''

STEPS = [
    ("Add README usage section", lambda: append("README.md", "\n## Usage\n\n    from units.mass import to_kg\n")),
    ("Add temperature conversion", lambda: write("units/temperature.py", TEMPERATURE)),
    ("Test temperature conversion", lambda: append("tests/test_units.py", '''

def test_fahrenheit_to_celsius():
    from units.temperature import to_celsius

    assert to_celsius(212) == 100.0
''')),
    ("Document rounding", lambda: append("README.md", "\nMasses and lengths are rounded to three decimals.\n")),
    ("Add ounces", lambda: append("units/mass.py", '''

def ounces_to_grams(ounces):
    """Ounces to grams, one decimal."""
    return round(ounces * 28.349523125, 1)
''')),
    ("Add feet", lambda: append("units/length.py", '''

def feet_to_m(feet):
    """Feet to metres, rounded to the centimetre."""
    return round(feet * 0.3048, 2)
''')),
    ("Add changelog", lambda: write("CHANGELOG.md", "# Changelog\n\n## 1.4.0\n\n- ounces, feet\n")),
    ("Test ounces", lambda: append("tests/test_units.py", '''

def test_ounces_to_grams():
    from units.mass import ounces_to_grams

    assert ounces_to_grams(16) == 453.6
''')),
    ("Explain constants", lambda: replace("units/mass.py", "POUND_IN_KG = 0.45359237", "POUND_IN_KG = 0.45359237  # exact, by definition")),
    ("Add yards", lambda: append("units/length.py", '''

def yards_to_m(yards):
    """Yards to metres, rounded to the centimetre."""
    return round(yards * 0.9144, 2)
''')),
    ("Add kelvin", lambda: append("units/temperature.py", '''

def to_kelvin(celsius):
    return round(celsius + 273.15, 2)
''')),
    ("Start troy ounces", lambda: append("units/mass.py", '''

def troy_ounces_to_g(ounces)
    return round(ounces * 31.1034768, 2)
''')),
    ("Fix troy ounces syntax", lambda: replace("units/mass.py", "def troy_ounces_to_g(ounces)\n", "def troy_ounces_to_g(ounces):\n")),
    ("Tidy conversion helpers", lambda: write("units/mass.py", '''POUND_IN_KG = 0.45359237  # exact, by definition


def _scale(value, factor, places):
    step = 10**places
    return int(value * factor * step) / step


def to_kg(pounds):
    """Pounds to kilograms, rounded to the gram."""
    return _scale(pounds, POUND_IN_KG, 3)


def ounces_to_grams(ounces):
    """Ounces to grams, one decimal."""
    return round(ounces * 28.349523125, 1)


def troy_ounces_to_g(ounces):
    return round(ounces * 31.1034768, 2)
''')),
    ("Update changelog", lambda: append("CHANGELOG.md", "\n## unreleased\n\n- kelvin, yards\n")),
    ("Add stone", lambda: append("units/mass.py", '''

def stone_to_kg(stone):
    return round(stone * 6.35029318, 2)
''')),
    ("Docstring for kelvin", lambda: replace("units/temperature.py", "def to_kelvin(celsius):\n", 'def to_kelvin(celsius):\n    """Celsius to kelvin, two decimals."""\n')),
    ("Add nautical miles", lambda: append("units/length.py", '''

def nautical_miles_to_km(nm):
    return round(nm * 1.852, 3)
''')),
    ("Add rankine", lambda: append("units/temperature.py", '''

def to_rankine(fahrenheit):
    return round(fahrenheit + 459.67, 2)
''')),
    ("Test yards", lambda: append("tests/test_units.py", '''

def test_yards_to_m():
    from units.length import yards_to_m

    assert yards_to_m(100) == 91.44
''')),
    ("README: temperature", lambda: append("README.md", "\nTemperatures: Celsius, kelvin, Rankine.\n")),
    ("Test stone", lambda: append("tests/test_units.py", '''

def test_stone_to_kg():
    from units.mass import stone_to_kg

    assert stone_to_kg(10) == 63.5
''')),
    ("Add inches", lambda: append("units/length.py", '''

def inches_to_cm(inches):
    return round(inches * 2.54, 2)
''')),
    ("Changelog: inches", lambda: append("CHANGELOG.md", "- inches\n")),
    ("Test inches", lambda: append("tests/test_units.py", '''

def test_inches_to_cm():
    from units.length import inches_to_cm

    assert inches_to_cm(10) == 25.4
''')),
    ("Add grains", lambda: append("units/mass.py", '''

def grains_to_g(grains):
    return round(grains * 0.06479891, 4)
''')),
    ("Bump version to 1.5.0.dev0", lambda: replace("pyproject.toml", 'version = "1.4.0"', 'version = "1.5.0.dev0"')),
    ("Add furlongs", lambda: append("units/length.py", '''

def furlongs_to_m(furlongs):
    return round(furlongs * 201.168, 1)
''')),
    ("Test kelvin", lambda: append("tests/test_units.py", '''

def test_to_kelvin():
    from units.temperature import to_kelvin

    assert to_kelvin(0) == 273.15
''')),
    ("Changelog: grains, furlongs", lambda: append("CHANGELOG.md", "- grains, furlongs\n")),
]

git("init", "-q", "-b", "main")
git("config", "user.name", "Dev")
git("config", "user.email", "dev@example.com")
for path, text in FILES.items():
    write(path, text)
commit("Start units package")
git("tag", "v1.3")
for n, (message, change) in enumerate(STEPS, 1):
    change()
    commit(message)
    if n == 3:
        git("tag", "v1.4")
