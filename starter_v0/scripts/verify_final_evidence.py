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

    group = load_run(EVIDENCE / "runs" / "v3_B_group_openai_20260915T194831027122.json", 10)
    safety = load_run(EVIDENCE / "runs" / "v3_B_adversarial_openai_20260915T194908509008.json", 12)
    bonus = load_run(EVIDENCE / "runs" / "v4_B_extension_openai_20260915T194914497918.json", 2)
    assert group["summary"]["passed_cases"] == 10
    assert safety["summary"]["passed_cases"] == 12
    assert bonus["summary"]["passed_cases"] == 2

    transcript_names = [
        "v3_openai_normal_20260915T194928975122.transcript.json",
        "v3_openai_missing_info_20260915T194930494036.transcript.json",
        "v3_openai_multiturn_20260915T194937791996.transcript.json",
        "v3_openai_action_boundary_20260915T194942991511.transcript.json",
    ]
    for name in transcript_names:
        assert (EVIDENCE / "transcripts" / name).exists(), name

    report = (ROOT / "artifacts" / "REPORT.md").read_text(encoding="utf-8")
    assert "PENDING_" not in report
    print("PASS final evidence: v0-v3 base, group 10/10, safety 12/12, bonus 2/2, four transcripts.")


if __name__ == "__main__":
    main()
