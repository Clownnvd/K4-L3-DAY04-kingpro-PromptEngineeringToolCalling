from __future__ import annotations

import argparse, json, sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations,to_openai_tools
from versioning import artifact_version_dict,build_artifact_version

load_lab_env(ROOT)
SCENARIOS={
    "normal":["VPN production hiện có đang gặp sự cố không?"],
    "missing_info":["Kiểm tra Wi-Fi trên laptop của tôi giúp nhé."],
    "multiturn":["Kiểm tra email production.","À nhầm, chỉ kiểm tra email staging."],
    "action_boundary":["Tạo ticket high cho lỗi VPN trên LT-204.","Tôi xác nhận tạo ticket high cho lỗi VPN trên LT-204."],
}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--provider",choices=["gemini","groq","offline"],default="groq")
    parser.add_argument("--model",default=None)
    parser.add_argument("--output-dir",type=Path,default=ROOT/"transcripts")
    args=parser.parse_args()
    prompt_path=ROOT/"artifacts"/"system_prompt.md"; tools_path=ROOT/"artifacts"/"tools.yaml"
    system_prompt=prompt_path.read_text(encoding="utf-8")
    tools=to_openai_tools(load_tool_declarations(tools_path))
    provider=make_provider(args.provider)
    artifact=artifact_version_dict(build_artifact_version("v3",prompt_path,tools_path))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,user_turns in SCENARIOS.items():
        history=[]; records=[]
        for index,user_text in enumerate(user_turns,1):
            messages=[{"role":"system","content":system_prompt},*history,{"role":"user","content":user_text}]
            result=run_model_tool_loop(provider=provider,messages=messages,tools=tools,model=args.model,max_tool_rounds=4)
            records.append({"turn":index,"user":user_text,**result})
            history += [{"role":"user","content":user_text},{"role":"assistant","content":result.get("assistant_text","")}]
        stamp=datetime.now().strftime("%Y%m%dT%H%M%S%f")
        path=args.output_dir/f"v3_{args.provider}_{name}_{stamp}.transcript.json"
        payload={"scenario":name,"provider":args.provider,"model":args.model or getattr(provider,"default_model",None),**artifact,"turns":records,"generated_at":datetime.now().isoformat(timespec="seconds")}
        if args.provider=="offline": payload["evidence_notice"]="Developer validation only; not official LLM evidence."
        path.write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        print(path)

if __name__=="__main__": main()
