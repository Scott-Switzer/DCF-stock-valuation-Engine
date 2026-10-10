"""Bundle templates and public data into Python for Workers' read-only filesystem."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = (
    list((root / "templates").glob("*.html"))
    + list((root / "static").rglob("*"))
    + [root / "data/demo.json"]
)
assets = {str(p.relative_to(root)): p.read_text() for p in paths if p.is_file()}
(root / "embedded_assets.py").write_text("ASSETS = " + repr(assets) + "\n")

import shutil

bundle = root / "worker_runtime"
bundle.mkdir(exist_ok=True)
for name in [
    "worker.py",
    "app.py",
    "dcf_code.py",
    "dcf_loader.py",
    "storage.py",
    "provider_cache.py",
    "ppe_packets.py",
    "ppe_provider.py",
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
    "suite_views.py",
    "embedded_assets.py",
]:
    shutil.copyfile(root / name, bundle / name)
