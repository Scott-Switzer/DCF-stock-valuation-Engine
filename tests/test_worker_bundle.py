"""The Workers bundle must include every local module that bundled code imports."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bundled_names():
    source = (ROOT / "scripts" / "embed_assets.py").read_text()
    block = source.split("for name in [", 1)[1].split("]:", 1)[0]
    return set(re.findall(r'"([A-Za-z_]+\.py)"', block))


def test_every_local_import_in_bundled_code_is_bundled():
    names = bundled_names()
    local = {p.stem for p in ROOT.glob("*.py")}
    missing = set()
    for name in names:
        text = (ROOT / name).read_text()
        for module in local:
            if re.search(rf"^\s*(from|import) {module}\b", text, re.MULTILINE):
                if f"{module}.py" not in names:
                    missing.add(f"{name} -> {module}.py")
    assert not missing, f"Bundle omits imported modules: {sorted(missing)}"


def test_readiness_is_bundled():
    assert "readiness.py" in bundled_names()
