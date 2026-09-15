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

def latest(version:str,suite:str,provider:str)->Path:
    files=sorted((ROOT/"runs").glob(f"{version}_B_{suite}_{provider}_*.json"),key=lambda p:p.stat().st_mtime,reverse=True)
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
    parser=argparse.ArgumentParser(description="Generate official evidence with one fixed provider/model per run.")
    parser.add_argument("--provider",choices=["openai","gemini","groq"],default=os.getenv("LAB_PROVIDER","openai"))
    parser.add_argument("--model",default=None)
    args=parser.parse_args()
    if args.model is None:
        defaults={"openai":os.getenv("OPENAI_MODEL","gpt-4o-mini"),"gemini":os.getenv("GEMINI_MODEL","gemini-3.6-flash"),"groq":os.getenv("GROQ_MODEL","qwen/qwen3.8-27b")}
        args.model=defaults[args.provider]
    key_name={"openai":"OPENAI_API_KEY","gemini":"GEMINI_API_KEY","groq":"GROQ_API_KEY"}[args.provider]
    if not os.getenv(key_name):
        raise SystemExit(f"Missing {key_name}. Add it to starter_v0/.env.")
    py=sys.executable
    evidence_runs=ROOT/"artifacts"/"evidence"/"runs"
    evidence_transcripts=ROOT/"artifacts"/"evidence"/"transcripts"
    run([py,"scripts/preflight_provider.py","--provider",args.provider,"--model",args.model,"--tools","artifacts/versions/v0/tools.yaml"])
    rows=[]; previous=""
    for version in ["v0","v1","v2","v3"]:
        prompt=f"artifacts/versions/{version}/system_prompt.md"; tools=f"artifacts/versions/{version}/tools.yaml"
        run([py,"run_eval.py","--provider",args.provider,"--model",args.model,"--version",version,"--suite","base","--system-prompt",prompt,"--tools",tools,"--eval-cases","data/eval_base.json"])
        path=latest(version,"base",args.provider); data=verify_and_copy(path,evidence_runs); summary=data["summary"]
        av=build_artifact_version(version,ROOT/prompt,ROOT/tools)
        current=str(summary.get("case_accuracy")); changed,why=HYPOTHESES[version]
        rows.append({"version":version,"author":"kingpro","changed_artifact":changed,"artifact_version":av.artifact_version,"prompt_hash":av.prompt_hash,"tools_hash":av.tools_hash,"reason":why,"hypothesis":why,"metric_name":"case_accuracy","metric_before":previous,"metric_after":current,"run_file":str((evidence_runs/path.name).relative_to(ROOT)).replace('\\','/')})
        previous=current
    for suite,data_path in [("group","data/eval_group.json"),("adversarial","data/eval_adversarial.json")]:
        run([py,"run_eval.py","--provider",args.provider,"--model",args.model,"--version","v3","--suite",suite,"--system-prompt","artifacts/versions/v3/system_prompt.md","--tools","artifacts/versions/v3/tools.yaml","--eval-cases",data_path])
        verify_and_copy(latest("v3",suite,args.provider),evidence_runs)
    run([py,"run_eval.py","--provider",args.provider,"--model",args.model,"--version","v4","--suite","extension","--system-prompt","artifacts/versions/v4/system_prompt.md","--tools","artifacts/versions/v4/tools.yaml","--eval-cases","data/eval_bonus.json"])
    bonus_path=latest("v4","extension",args.provider); bonus_data=verify_and_copy(bonus_path,evidence_runs); bonus_summary=bonus_data["summary"]
    bonus_av=build_artifact_version("v4",ROOT/"artifacts/versions/v4/system_prompt.md",ROOT/"artifacts/versions/v4/tools.yaml")
    rows.append({"version":"v4","author":"kingpro","changed_artifact":"tools.yaml","artifact_version":bonus_av.artifact_version,"prompt_hash":bonus_av.prompt_hash,"tools_hash":bonus_av.tools_hash,"reason":"Add a no-key allowlisted public status API while keeping the v3 prompt unchanged.","hypothesis":"A live external tool should add demonstrable value without leaking internal data or changing core routing rules.","metric_name":"bonus_case_accuracy","metric_before":"","metric_after":str(bonus_summary.get("case_accuracy")),"run_file":str((evidence_runs/bonus_path.name).relative_to(ROOT)).replace('\\','/')})
    run([py,"scripts/run_demo_scenarios.py","--provider",args.provider,"--model",args.model,"--output-dir",str(evidence_transcripts)])
    fieldnames=["version","author","changed_artifact","artifact_version","prompt_hash","tools_hash","reason","hypothesis","metric_name","metric_before","metric_after","run_file"]
    with (ROOT/"artifacts"/"version_log.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames); writer.writeheader(); writer.writerows(rows)
    run([py,"scripts/parse_runs.py",str(evidence_runs),"--output","artifacts/run_analysis.csv"])
    print(f"\nDONE: official {args.provider}/{args.model} evidence, version log, group/adversarial/bonus runs and four transcripts are ready.")

if __name__=="__main__": main()
