from __future__ import annotations

import argparse, csv, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from env_loader import load_lab_env
from versioning import build_artifact_version

load_lab_env(ROOT)
HYPOTHESES={
    "v0":("baseline","Measure the unchanged starter baseline before any optimization."),
    "v1":("system_prompt.md","Clear tool ownership, missing-identifier and latest-intent rules should improve routing and multi-turn accuracy."),
    "v2":("tools.yaml","Use/avoid guidance plus stricter schemas should improve routing and argument accuracy."),
    "v3":("system_prompt.md","Payload-bound confirmation and trust/privacy boundaries should improve safety without regressing core routing."),
}

def run(cmd:list[str]):
    print("\n>"," ".join(cmd),flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)

def latest(version:str,suite:str)->Path:
    files=sorted((ROOT/"runs").glob(f"{version}_B_{suite}_gemini_*.json"),key=lambda p:p.stat().st_mtime,reverse=True)
    if not files: raise RuntimeError(f"Missing run for {version}/{suite}")
    return files[0]

def verify_and_copy(path:Path,evidence_dir:Path)->dict:
    data=json.loads(path.read_text(encoding="utf-8")); summary=data["summary"]
    if summary.get("provider_error_cases")!=0 or summary.get("measured_cases")!=summary.get("total_cases"):
        raise SystemExit(f"Invalid evidence run: {path.name}: {summary}")
    evidence_dir.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,evidence_dir/path.name)
    return data

def main():
    parser=argparse.ArgumentParser(description="Generate all official Gemini evidence; this script never selects OpenAI.")
    parser.add_argument("--model",default=os.getenv("GEMINI_MODEL","gemini-3.7-flash"))
    args=parser.parse_args()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("Missing GEMINI_API_KEY. Add it to starter_v0/.env; OPENAI_API_KEY is never used by this script.")
    py=sys.executable
    evidence_runs=ROOT/"artifacts"/"evidence"/"runs"
    evidence_transcripts=ROOT/"artifacts"/"evidence"/"transcripts"
    run([py,"scripts/preflight_provider.py","--provider","gemini","--model",args.model,"--tools","artifacts/versions/v0/tools.yaml"])
    rows=[]; previous=""
    for version in ["v0","v1","v2","v3"]:
        prompt=f"artifacts/versions/{version}/system_prompt.md"; tools=f"artifacts/versions/{version}/tools.yaml"
        run([py,"run_eval.py","--provider","gemini","--model",args.model,"--version",version,"--suite","base","--system-prompt",prompt,"--tools",tools,"--eval-cases","data/eval_base.json"])
        path=latest(version,"base"); data=verify_and_copy(path,evidence_runs); summary=data["summary"]
        av=build_artifact_version(version,ROOT/prompt,ROOT/tools)
        current=str(summary.get("case_accuracy")); changed,why=HYPOTHESES[version]
        rows.append({"version":version,"author":"kingpro","changed_artifact":changed,"artifact_version":av.artifact_version,"prompt_hash":av.prompt_hash,"tools_hash":av.tools_hash,"reason":why,"hypothesis":why,"metric_name":"case_accuracy","metric_before":previous,"metric_after":current,"run_file":str((evidence_runs/path.name).relative_to(ROOT)).replace('\\','/')})
        previous=current
    for suite,data_path in [("group","data/eval_group.json"),("adversarial","data/eval_adversarial.json")]:
        run([py,"run_eval.py","--provider","gemini","--model",args.model,"--version","v3","--suite",suite,"--system-prompt","artifacts/versions/v3/system_prompt.md","--tools","artifacts/versions/v3/tools.yaml","--eval-cases",data_path])
        verify_and_copy(latest("v3",suite),evidence_runs)
    run([py,"scripts/run_demo_scenarios.py","--provider","gemini","--model",args.model,"--output-dir",str(evidence_transcripts)])
    fieldnames=["version","author","changed_artifact","artifact_version","prompt_hash","tools_hash","reason","hypothesis","metric_name","metric_before","metric_after","run_file"]
    with (ROOT/"artifacts"/"version_log.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames); writer.writeheader(); writer.writerows(rows)
    run([py,"scripts/parse_runs.py",str(evidence_runs),"--output","artifacts/run_analysis.csv"])
    print("\nDONE: official Gemini evidence, version log, group/adversarial runs and four transcripts are ready.")

if __name__=="__main__": main()
