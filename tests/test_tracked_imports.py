"""Fail when a tracked file imports a module the commit does not contain.

A tracked file that imports a sibling existing only as an *untracked* file runs
fine on the author's machine and dies on a clean checkout. That is how the
``fcfe_valuation`` and ``apv_valuation`` lanes were imported from ``app.py`` and
``compare.py`` before the modules were ever added to a commit.

Imports are resolved against the committed tree (``git ls-files``) rather than
against whatever happens to be in the working directory, so an untracked copy
cannot mask the gap, and the check behaves the same locally and on a runner.
Names that are stdlib or already installed in site-packages are ignored: they
are not expected to live in this repo. Generated modules that .gitignore
excludes (``embedded_assets.py``, ``worker_runtime/``, ``python_modules/``) are
ignored for the same reason -- their absence from the commit is deliberate.

The resolver is deliberately permissive about *where* a name lives, because this
repo puts its top-level modules, ``scripts/`` and ``tests/`` helpers on sys.path
from inside individual files (pytest contributes ``pythonpath = ["."]``). A
module found anywhere in the commit counts as committed.

``git ls-files`` reads the index, so this works in shallow checkouts.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _stdlib_names() -> set[str]:
    """Standard-library module names, without requiring Python 3.10+."""
    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return set(names) | {"__future__"}
    base = Path(sysconfig.get_paths()["stdlib"])
    found = {p.stem for p in base.glob("*.py")}
    found |= {p.name for p in base.iterdir() if p.is_dir()}
    found -= {"site-packages", "dist-packages", "lib-dynload"}
    return found | set(sys.builtin_module_names) | {"__future__"}


STDLIB = _stdlib_names()


def _git(*args: str, root: Path) -> list[str]:
    out = subprocess.run(
        ("git", *args, "-z"), cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.split("\0") if p]


def _index(paths: list[str]) -> tuple[set[str], set[str]]:
    """Module stems and directory names available from a set of repo paths."""
    stems, dirs = set(), set()
    for path in paths:
        p = Path(path)
        for parent in p.parents:
            if parent == Path("."):
                break
            dirs.add(parent.name)
        if p.suffix == ".py":
            stems.add(p.parent.name if p.name == "__init__.py" else p.stem)
    return stems, dirs


def _installed(name: str) -> bool:
    """True when site-packages already provides this name."""
    for key in ("purelib", "platlib"):
        base = Path(sysconfig.get_paths()[key])
        if (base / f"{name}.py").exists() or (base / name / "__init__.py").exists():
            return True
    return False


def _imported_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names - STDLIB


def find_violations(root: Path) -> list[str]:
    """Tracked files importing a module that exists only outside the commit."""
    tracked = [p for p in _git("ls-files", root=root) if p.endswith(".py")]
    untracked = [
        p
        for p in _git("ls-files", "--others", "--exclude-standard", root=root)
        if p.endswith(".py")
    ]
    committed_stems, committed_dirs = _index(tracked)
    stray_stems, stray_dirs = _index(untracked)

    violations = []
    for path in tracked:
        try:
            source = (root / path).read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError):
            continue  # deleted in the working tree, or not source text
        for name in sorted(_imported_names(source)):
            if name in committed_stems or name in committed_dirs:
                continue
            if _installed(name):
                continue
            if name in stray_stems or name in stray_dirs:
                violations.append(
                    f"{path}: imports '{name}', which exists only as an untracked file"
                )
    return violations


def test_committed_tree_has_no_uncommitted_imports():
    violations = find_violations(ROOT)
    assert not violations, (
        "tracked files import modules that are not in the commit, so a clean "
        "checkout cannot import them:\n  "
        + "\n  ".join(violations)
        + "\n\nCommit the module, or drop the import."
    )


def _repo(tmp_path: Path, *, tracked: dict[str, str], untracked: dict[str, str]) -> Path:
    """A throwaway repo with `tracked` staged and `untracked` left unstaged."""
    root = tmp_path / "repo"
    for name, body in {**tracked, **untracked}.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    subprocess.run(("git", "init", "-q"), cwd=root, check=True)
    for name in tracked:
        subprocess.run(("git", "add", "--", name), cwd=root, check=True)
    return root


def test_detects_module_that_was_never_committed(tmp_path):
    root = _repo(
        tmp_path,
        tracked={"app.py": "from fcfe_valuation import fcfe_value\n"},
        untracked={"fcfe_valuation.py": "def fcfe_value():\n    return 1\n"},
    )
    assert find_violations(root) == [
        "app.py: imports 'fcfe_valuation', which exists only as an untracked file"
    ]


def test_detects_uncommitted_package_directory(tmp_path):
    root = _repo(
        tmp_path,
        tracked={"app.py": "from valuation_lanes.apv import apv_value\n"},
        untracked={
            "valuation_lanes/__init__.py": "",
            "valuation_lanes/apv.py": "def apv_value():\n    pass\n",
        },
    )
    assert [v.split(":")[0] for v in find_violations(root)] == ["app.py"]


def test_committed_and_external_imports_pass(tmp_path):
    root = _repo(
        tmp_path,
        tracked={
            "app.py": "import json\n\nfrom dcf_code import discount_fcff\nimport pytest\n",
            "dcf_code.py": "def discount_fcff():\n    return 1\n",
        },
        untracked={},
    )
    assert find_violations(root) == []
