"""Exercise failed and overlapping paging requests against the actual shipped JS."""
import subprocess


def test_share_paging_retries_without_skipping_or_overlapping():
    subprocess.run(["node", "tests/js/share_paging.cjs"], check=True, timeout=10)


def test_workspace_chart_receives_method_specific_history():
    subprocess.run(["node", "tests/js/workspace_chart.cjs"], check=True, timeout=10)
