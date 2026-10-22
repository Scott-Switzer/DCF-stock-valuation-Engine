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
    "owner_benchmark_access.py",
    "owner_data_proxy.py",
    "data_workspace.py",
    "dcf_code.py",
    "dcf_loader.py",
    "zion_history_provider.py",
    "zion_benchmark_provider.py",
    "valuation_benchmarks.py",
    "enterprise_valuation.py",
    "storage.py",
    "provider_cache.py",
    "ppe_packets.py",
    "ppe_provider.py",
    "dataset_catalog.py",
    "company_packets.py",
    "financial_qa.py",
    "yahoo_provider.py",
    "auto_loading.py",
    "brief.py",
    "sec_first.py",
    "accounting_policy.py",
    "tax_policy.py",
    "decision_support.py",
    "issuer_classification.py",
    "guidance.py",
    "valuation_records.py",
    "xlsx_export.py",
    "compare.py",
    "readiness.py",
    "research_screen.py",
    "residual_income.py",
    "library.py",
    "accounts.py",
    "reverse_dcf.py",
    "mcp.py",
    "suite_models.py",
    "comps_analysis.py",
    "bottom_up_capm.py",
    "fcfe_valuation.py",
    "apv_valuation.py",
    "bank_excess_return.py",
    "research.py",
    "suite_views.py",
    "embedded_assets.py",
    "equity_claims_provider.py",
    "zion_equity_claims_service.py",
]
# Modules the repository keeps under scripts/ but a flat Workers bundle must import by
# bare name; `equity_claims_provider` reaches the public-SEC bridge helper this way.
script_module_names = [
    "public_sec_equity_bridge.py",
]
# This directory contains generated modules only. Remove stale branch artifacts.
sources = {name: root / name for name in module_names}
sources.update({name: root / "scripts" / name for name in script_module_names})
for stale in bundle.glob("*.py"):
    if stale.name not in sources:
        stale.unlink()
for name, source in sources.items():
    shutil.copyfile(source, bundle / name)
