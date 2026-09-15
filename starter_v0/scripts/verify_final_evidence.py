from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from versioning import artifact_version_dict, build_artifact_version


EVIDENCE = ROOT / "artifacts" / "evidence"


def load_run(path: Path, expected_cases: int) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data["summary"]
    assert data["provider"] == "openai", path
    assert data["model"] == "gpt-4o-mini", path
    assert summary["total_cases"] == expected_cases, path
    assert summary["measured_cases"] == expected_cases, path
    assert summary["provider_error_cases"] == 0, path
    return data


def latest_run(pattern: str, expected_cases: int) -> tuple[Path, dict]:
    for path in sorted((EVIDENCE / "runs").glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            return path, load_run(path, expected_cases)
        except (AssertionError, KeyError, ValueError):
            continue
    raise AssertionError(f"No valid evidence run matched {pattern}")


def main() -> None:
    with (ROOT / "artifacts" / "version_log.csv").open(encoding="utf-8") as handle:
        version_rows = list(csv.DictReader(handle))
    assert [row["version"] for row in version_rows] == ["v0", "v1", "v2", "v3", "v4"]

    for row in version_rows[:4]:
        run_path = ROOT / row["run_file"]
        data = load_run(run_path, 30)
        version = row["version"]
        expected = artifact_version_dict(build_artifact_version(
            version,
            ROOT / "artifacts" / "versions" / version / "system_prompt.md",
            ROOT / "artifacts" / "versions" / version / "tools.yaml",
        ))
        assert data["artifact_version"] == expected["artifact_version"], run_path
        assert row["artifact_version"] == expected["artifact_version"], run_path

    _, group = latest_run("v3_B_group_openai_*.json", 10)
    _, safety = latest_run("v3_B_adversarial_openai_*.json", 12)
    _, bonus = latest_run("v4_B_extension_openai_*.json", 2)
    assert group["summary"]["passed_cases"] == 10
    assert safety["summary"]["passed_cases"] == 12
    assert bonus["summary"]["passed_cases"] == 2

    for scenario in ["normal", "missing_info", "multiturn", "action_boundary"]:
        matches = list((EVIDENCE / "transcripts").glob(f"v3_openai_{scenario}_*.transcript.json"))
        assert matches, scenario

    report = (ROOT / "artifacts" / "REPORT.md").read_text(encoding="utf-8")
    assert "PENDING_" not in report
    print("PASS final evidence: v0-v3 base, group 10/10, safety 12/12, bonus 2/2, four transcripts.")


if __name__ == "__main__":
    main()
