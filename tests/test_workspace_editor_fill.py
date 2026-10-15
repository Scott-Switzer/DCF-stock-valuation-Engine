"""The assumptions editor must fill on the bundled-preview fast path.

Regression test for the PR #29 fallout: assemble() early-returned when
results arrived bundled with the load response, skipping the
workspace-data send, so the editor stayed on "Enter a ticker" with a
hidden form and no assumption could be edited.
"""
import subprocess


def test_bundled_preview_still_fills_assumptions_editor():
    subprocess.run(["node", "tests/js/workspace_editor_fill.cjs"], check=True, timeout=10)
