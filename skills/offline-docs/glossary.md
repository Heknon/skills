# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| distribution | What is installed and versioned, named as in `uv add` and `uv pip show`, such as `PyYAML` or `types-fetchkit`. |
| import name | What `import` takes, such as `yaml` or `fetchkit`; one distribution can provide several, and the names often differ. |
| pin | The interpreter path, Python version, distribution version and file location, found before anything is read. |
| installed code | The files the interpreter imports, in `site-packages` or the standard library folder; not a copy elsewhere. |
| site-packages | The folder of a Python environment that holds installed distributions (`.venv\Lib\site-packages` on Windows). |
| standard library folder | The interpreter's own `Lib\` folder (Linux: `lib/python3.12/`), printed by `sysconfig.get_paths()['stdlib']`. |
| wheel | A built distribution file (`.whl`), a zip that is unpacked into `site-packages` on install. |
| sdist | A source distribution (`.tar.gz`) with `PKG-INFO` and the source tree; often has the changelog the wheel lacks. |
| dist-info folder | `<name>-<version>.dist-info\` in `site-packages`, holding the distribution's metadata files. |
| METADATA | The dist-info file with name, version, dependencies and the long description, which is often the README. |
| RECORD | The dist-info file listing every installed file with its hash and size. |
| direct_url.json | The dist-info file present for editable and direct installs; says where it came from. |
| editable install | An install whose code is read from a project folder through a `.pth` file; changes there run without reinstalling. |
| copy | An install whose code was copied into `site-packages`; changing the source elsewhere does not change what runs. |
| compiled module | A module built to machine code (`.so` on Linux, `.pyd` on Windows), with no Python source to read. |
| builtin module | A compiled module built into the interpreter itself, listed in `sys.builtin_module_names`, with no file at all. |
| stub | A `.pyi` file of signatures and types without code, read by type checkers and never by the interpreter. |
| inline stub | A stub shipped inside the package it describes, in the same wheel, so for the same version. |
| stub package | A separate distribution, usually `types-<name>`, installing `<name>-stubs\`; it may target another version. |
| typeshed | The shared collection of stubs that `types-*` packages come from and that type checkers bundle. |
| py.typed | An empty marker file saying a package ships its own types. |
| docstring | The string at the top of a module, class or function; the author's description, printed by `help()` and pydoc. |
| pager | A program such as `less` or `more` that shows long output a screen at a time and waits for a key. |
| signature | The parameters a callable accepts, with defaults and kinds, as `inspect.signature` prints them. |
| text signature | A signature written by the author of a compiled function, in `__text_signature__`; without one, `inspect.signature` fails. |
| wrapper | A function that a decorator puts in place of the decorated one; with `functools.wraps` it carries `__wrapped__`. |
| passthrough | `*args` or `**kwargs` passed on unchanged to another function, which decides what is accepted. |
| changelog | A file of release notes (`CHANGELOG`, `CHANGES`, `HISTORY`, `NEWS`), or release notes inside METADATA. |
| mirror | The internal package index that serves distributions to the air-gapped network. |
| wheelhouse | A folder of wheel files used as an index, as in the eval sandboxes. |
| throwaway environment | The environment `uv run --isolated --no-project --with <dist>==<version>` builds in uv's cache for one command. |
| source kind | Where evidence came from: code, stub, docstring, --help, metadata or internal page. |
| verdict | The last line of an answer: confirmed from source, confirmed from a stub, help or page only, or not found. |
