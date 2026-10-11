"""Bundle templates and public data into Python for Workers' read-only filesystem."""

from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[1]
paths = (
    list((root / "templates").glob("*.html"))
    + list((root / "static").rglob("*"))
    + [root / "data/demo.json"]
)
assets = {str(p.relative_to(root)): p.read_text() for p in paths if p.is_file()}
try:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=root).returncode != 0
except (OSError, subprocess.CalledProcessError):
    commit, dirty = "unknown", True
build = {"commit": commit, "tracked_dirty": dirty,
         "asset_sha256": hashlib.sha256(json.dumps(assets, sort_keys=True).encode()).hexdigest()}
(root / "embedded_assets.py").write_text("ASSETS = " + repr(assets) + "\nBUILD = " + repr(build) + "\n")

import shutil

bundle = root / "worker_runtime"
bundle.mkdir(exist_ok=True)
module_names = [
    "worker.py",
    "app.py",
    "dcf_code.py",
    "dcf_loader.py",
    "storage.py",
    "provider_cache.py",
    "ppe_packets.py",
    "ppe_provider.py",
    "dataset_catalog.py",
    "yahoo_provider.py",
    "auto_loading.py",
    "decision_support.py",
    "issuer_classification.py",
    "guidance.py",
    "valuation_records.py",
    "xlsx_export.py",
    "compare.py",
    "readiness.py",
    "residual_income.py",
    "library.py",
    "accounts.py",
    "reverse_dcf.py",
    "mcp.py",
    "suite_models.py",
    "comps_analysis.py",
    "research.py",
    "suite_views.py",
    "embedded_assets.py",
]
# This directory contains generated modules only. Remove stale branch artifacts.
for stale in bundle.glob("*.py"):
    if stale.name not in module_names:
        stale.unlink()
for name in module_names:
    shutil.copyfile(root / name, bundle / name)
