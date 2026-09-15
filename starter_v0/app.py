from __future__ import annotations

import json, os, re
from datetime import datetime
from pathlib import Path
import streamlit as st

from chat import run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT=Path(__file__).parent
ARTIFACTS=ROOT/"artifacts"
load_lab_env(ROOT)
st.set_page_config(page_title="Northstar IT Desk",page_icon="🧭",layout="wide")
st.markdown("""
<style>
:root{--ink:#0b3338;--coral:#ef6f61;--sun:#f4c95d;--paper:#f7f3e8;--mint:#dcebe5}
.stApp{background:linear-gradient(135deg,#f8f4e9,#e8f1ec);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}.block-container{max-width:1500px;padding-top:1rem}
.hero{background:var(--ink);color:white;border-radius:24px;padding:22px 28px;border-bottom:6px solid var(--coral);box-shadow:0 14px 35px #0b333826}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.4rem 0 0;color:#cde1dc}
.pill{display:inline-block;background:var(--sun);color:var(--ink);border-radius:99px;padding:5px 10px;font-weight:800;font-size:.72rem;margin-bottom:10px}
.panel{background:#fffdf7;border:1px solid #d8dfd8;border-radius:20px;padding:16px;box-shadow:0 8px 24px #0b333810;margin-bottom:12px}
.metric-card{background:var(--mint);border-radius:16px;padding:13px;margin:8px 0}
[data-testid="stChatMessage"]{background:#fffdf9;border:1px solid #dfe5df;border-radius:18px;padding:8px}
.stButton>button{border-radius:999px;border:1px solid var(--ink);color:var(--ink)}
</style>""",unsafe_allow_html=True)

def redact(text:str)->str:
    return re.sub(r"(?i)\b(password|passwd|token|api[ _-]?key|mfa|otp|recovery[ _-]?code)\s*[:=]\s*\S+",r"\1=[REDACTED]",text)

def get_transcript_path()->Path:
    if "transcript_path" not in st.session_state:
        st.session_state.transcript_path=ROOT/"transcripts"/f"ui_{datetime.now():%Y%m%dT%H%M%S}.transcript.json"
    return st.session_state.transcript_path

def save_transcript(provider:str,model:str,artifact:dict)->None:
    path=get_transcript_path(); path.parent.mkdir(exist_ok=True)
    turns=json.loads(json.dumps(st.session_state.turns,ensure_ascii=False,default=str))
    for turn in turns:
        if isinstance(turn.get("user"),str): turn["user"]=redact(turn["user"])
    payload={"notice":"Secret đã được che. Offline chỉ là developer validation, không phải LLM evidence.","provider":provider,"model":model,**artifact,"turns":turns,"updated_at":datetime.now().isoformat(timespec="seconds")}
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

def latest_valid_run():
    if not (ROOT/"runs").exists(): return None
    for path in sorted((ROOT/"runs").glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        try:
            data=json.loads(path.read_text(encoding="utf-8")); s=data.get("summary",{})
            if data.get("provider")!="offline" and s.get("provider_error_cases")==0 and s.get("measured_cases")==s.get("total_cases"): return path,data
        except Exception: pass
    return None

prompt_path=ARTIFACTS/"system_prompt.md"; tools_path=ARTIFACTS/"tools.yaml"
system_prompt=prompt_path.read_text(encoding="utf-8")
tools=to_openai_tools(load_tool_declarations(tools_path))
artifact=artifact_version_dict(build_artifact_version("v3",prompt_path,tools_path))
for key,default in [("history",[]),("turns",[]),("last_trace",None)]:
    if key not in st.session_state: st.session_state[key]=default

st.markdown('<div class="hero"><span class="pill">KINGPRO · LAB 4</span><h1>Northstar IT Desk</h1><p>Agent hỗ trợ IT có tool trace, xác nhận hành động và ranh giới dữ liệu rõ ràng.</p></div>',unsafe_allow_html=True)
st.write("")
left,center,right=st.columns([1.05,2.25,1.05],gap="large")
with left:
    st.subheader("Điều khiển")
    provider_options=["Groq API","Gemini API","Offline validation"]
    default_provider=0 if os.getenv("GROQ_API_KEY") else (1 if os.getenv("GEMINI_API_KEY") else 2)
    provider_label=st.selectbox("Chế độ",provider_options,index=default_provider)
    provider_name={"Groq API":"groq","Gemini API":"gemini","Offline validation":"offline"}[provider_label]
    default_models={"groq":os.getenv("GROQ_MODEL","openai/gpt-oss-120b"),"gemini":os.getenv("GEMINI_MODEL","gemini-3.7-flash"),"offline":"offline-rule-router-v1"}
    model=st.text_input("Model",value=default_models[provider_name],disabled=provider_name=="offline")
    if provider_name=="offline": st.info("Kiểm tra UI và tool loop; không dùng làm bằng chứng LLM.")
    elif provider_name=="gemini" and not os.getenv("GEMINI_API_KEY"): st.error("Chưa có GEMINI_API_KEY trong .env.")
    elif provider_name=="groq" and not os.getenv("GROQ_API_KEY"): st.error("Chưa có GROQ_API_KEY trong .env.")
    st.subheader("Tool trace gần nhất")
    trace=st.session_state.last_trace
    if not trace: st.caption("Chưa có tool call.")
    else:
        for rnd in trace.get("rounds",[]):
            with st.expander(f"Vòng {rnd.get('round')} · {len(rnd.get('tool_calls',[]))} call",expanded=True):
                for call in rnd.get("tool_calls",[]):
                    st.markdown(f"**{call['name']}**"); st.json(call.get("args",{}))
                for event in rnd.get("tool_results",[]):
                    if event.get("result",{}).get("error"): st.error(event["result"])
                    else: st.json(event.get("result",{}),expanded=False)
with center:
    st.subheader("Hội thoại")
    if not st.session_state.history: st.markdown('<div class="panel"><h3>Thử một tình huống</h3><p>Hỏi trạng thái dịch vụ, kiểm tra thiết bị hoặc yêu cầu tạo ticket.</p></div>',unsafe_allow_html=True)
    for item in st.session_state.history:
        with st.chat_message(item["role"]):
            if item["role"]=="assistant":
                try: st.json(json.loads(item["content"]))
                except Exception: st.markdown(item["content"])
            else: st.markdown(item["content"])
    cols=st.columns(3); quick=["VPN production có đang gặp sự cố không?","Kiểm tra bảo mật máy LT-204.","Tạo ticket high cho lỗi VPN trên LT-204."]
    chosen=None
    for col,label in zip(cols,quick):
        if col.button(label,use_container_width=True): chosen=label
    prompt=st.chat_input("Nhập yêu cầu IT...") or chosen
with right:
    st.subheader("Artifact đang chạy")
    st.markdown(f'<div class="metric-card"><b>Phiên bản</b><br>{artifact["artifact_version"]}</div>',unsafe_allow_html=True)
    st.code(f'prompt {artifact["prompt_hash"][:12]}\ntools  {artifact["tools_hash"][:12]}',language=None)
    st.subheader("Evidence")
    valid=latest_valid_run()
    if valid:
        path,data=valid; st.metric("Case accuracy",f'{data["summary"].get("case_accuracy",0)*100:.1f}%'); st.caption(path.name)
    else: st.warning("Chưa có run LLM hợp lệ; không hiển thị số liệu giả.")
    st.subheader("Ranh giới")
    st.markdown("- Không đoán ID\n- Không lưu secret\n- Ticket phải xác nhận\n- Không gửi dữ liệu nội bộ ra web")
    st.caption(f"Transcript: {get_transcript_path().name}")

if prompt:
    missing_key=(provider_name=="gemini" and not os.getenv("GEMINI_API_KEY")) or (provider_name=="groq" and not os.getenv("GROQ_API_KEY"))
    if missing_key: st.error(f"Thêm API key cho {provider_name} vào starter_v0/.env rồi thử lại.")
    else:
        provider=make_provider(provider_name)
        messages=[{"role":"system","content":system_prompt},*trim_history(st.session_state.history,5),{"role":"user","content":prompt}]
        try:
            with st.spinner("Đang phân tích và chọn tool..."):
                result=run_model_tool_loop(provider=provider,messages=messages,tools=tools,model=None if provider_name=="offline" else model,max_tool_rounds=4)
            answer=result.get("assistant_text","")
            st.session_state.history += [{"role":"user","content":prompt},{"role":"assistant","content":answer}]
            st.session_state.turns.append({"time":datetime.now().isoformat(timespec="seconds"),"user":prompt,**result})
            st.session_state.last_trace=result; save_transcript(provider_name,model,artifact); st.rerun()
        except Exception as exc: st.error(f"{type(exc).__name__}: {exc}")
