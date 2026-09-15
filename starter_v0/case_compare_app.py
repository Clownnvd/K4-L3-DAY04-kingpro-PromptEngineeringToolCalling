from __future__ import annotations

import csv, json, os
from datetime import datetime
from pathlib import Path
import streamlit as st

from agent import HelpdeskAgent
from env_loader import load_lab_env
from providers import make_provider
from run_eval import case_messages, evaluate_phase_b
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT=Path(__file__).parent
ART=ROOT/'artifacts';DATA=ROOT/'data'
load_lab_env(ROOT)
st.set_page_config(page_title='Lab 4 Case Compare',page_icon='⚖️',layout='wide')
st.markdown('''<style>
:root{--ink:#0b3338;--coral:#ef6f61;--sun:#f4c95d;--paper:#f7f3e8;--mint:#dcebe5}
.stApp{background:linear-gradient(135deg,#f8f4e9,#e8f1ec);color:var(--ink)}
.block-container{max-width:1500px;padding-top:1rem}.hero{background:var(--ink);color:white;border-radius:24px;padding:22px 28px;border-bottom:6px solid var(--coral);box-shadow:0 14px 35px #0b333826}.hero h1{margin:0;font-size:2rem}.hero p{margin:.45rem 0 0;color:#cde1dc}.pill{display:inline-block;background:var(--sun);color:var(--ink);border-radius:99px;padding:5px 10px;font-weight:800;font-size:.72rem;margin-bottom:10px}.panel{background:#fffdf7;border:1px solid #d8dfd8;border-radius:20px;padding:16px;box-shadow:0 8px 24px #0b333810;margin-bottom:12px}.pass{border-left:6px solid #169b62}.fail{border-left:6px solid #ef6f61}.waiting{border-left:6px solid #f4c95d}.stButton>button{border-radius:999px;border:1px solid var(--ink);font-weight:700}</style>''',unsafe_allow_html=True)

@st.cache_data
def load_cases():
    out={}
    for name in ['eval_base.json','eval_group.json','eval_adversarial.json','eval_bonus.json']:
        path=DATA/name
        if not path.exists():continue
        payload=json.loads(path.read_text(encoding='utf-8'))
        for case in payload.get('cases',[]):
            out[case['id']]={**case,'_dataset':name}
    return out

CASES=load_cases()

def label(case_id:str)->str:
    c=CASES[case_id];raw=c.get('input') or c.get('query') or c.get('turns')
    if isinstance(raw,list):summary=' → '.join(x.get('content','') for x in raw)
    else:summary=str(raw)
    return f"{case_id} · {summary[:82]}"

def artifact_paths(version:str):
    base=ART/'versions'/version
    return base/'system_prompt.md',base/'tools.yaml'

def run_one(version:str,case_id:str,provider_name:str,model:str):
    case=CASES[case_id];prompt_path,tools_path=artifact_paths(version)
    prompt=prompt_path.read_text(encoding='utf-8');decl=load_tool_declarations(tools_path);tools=to_openai_tools(decl)
    provider=make_provider(provider_name);agent=HelpdeskAgent(provider,system_prompt=prompt,tools=tools,model=None if provider_name=='offline' else model)
    tool_choice=None if case.get('expect',{}).get('no_tool') else 'required'
    started=datetime.now();run=agent.run(case_messages(case),tool_choice=tool_choice)
    calls=[{'name':c.name,'args':c.args} for c in run.tool_calls]
    result=evaluate_phase_b(case,calls,run.text)
    av=artifact_version_dict(build_artifact_version(version,prompt_path,tools_path))
    return {'version':version,'case_id':case_id,'dataset':case['_dataset'],'input':case.get('input') or case.get('query') or case.get('turns'),'expect':case['expect'],'actual_calls':calls,'tool_results':run.tool_results,'actual_text':run.text,'evaluation':result,'artifact':av,'provider':provider_name,'model':model if provider_name!='offline' else 'offline-rule-router-v1','started_at':started.isoformat(timespec='seconds')}

def save_comparison(a,b):
    folder=ROOT/'transcripts'/'comparisons';folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"compare_{a['case_id']}_{a['version']}_vs_{b['case_id']}_{b['version']}_{datetime.now():%Y%m%dT%H%M%S}.json"
    path.write_text(json.dumps({'notice':'Offline is developer validation only; Groq/Gemini runs are live model evidence.', 'A':a,'B':b},ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    return path

def result_card(side,r):
    ev=r['evaluation'];passed=ev.get('passed',False);cls='pass' if passed else 'fail'
    st.markdown(f"<div class='panel {cls}'><span class='pill'>VẾ {side} · {r['version'].upper()}</span><h3>{r['case_id']}</h3><p><b>{'PASS' if passed else 'FAIL'}</b> · {r['dataset']} · {r['model']}</p></div>",unsafe_allow_html=True)
    st.caption(f"Artifact: {r['artifact']['artifact_version']}")
    st.markdown('**Input được chấm**');st.write(r['input'])
    st.markdown('**Expected behavior**');st.json(r['expect'],expanded=True)
    st.markdown('**Actual tool calls**')
    if r['actual_calls']:st.json(r['actual_calls'],expanded=True)
    else:st.info('Không có tool call.')
    st.markdown('**Tool results**')
    if r['tool_results']:st.json(r['tool_results'],expanded=False)
    else:st.caption('Không có tool result.')
    st.markdown('**Evaluator**');st.json({'routing_correct':ev.get('routing_correct'),'args_correct':ev.get('args_correct'),'observed_mismatch':ev.get('observed_mismatch'),'failures':ev.get('failures')},expanded=True)
    if r.get('actual_text'):st.markdown('**Model text**');st.code(r['actual_text'])

def friendly_error(exc:Exception)->str:
    if type(exc).__name__=='RateLimitError':
        return 'Groq đang chạm giới hạn token/phút của gói hiện tại. Chờ khoảng 60 giây rồi chạy lại; kết quả vế còn lại vẫn được giữ.'
    return f'{type(exc).__name__}: {exc}'

def latest_safety_run():
    candidates=[*(ROOT/'runs').glob('v3_B_adversarial_*.json'),*(ART/'evidence'/'runs').glob('v3_B_adversarial_*.json')]
    for path in sorted(candidates,key=lambda p:p.stat().st_mtime,reverse=True):
        try:
            data=json.loads(path.read_text(encoding='utf-8'));summary=data.get('summary',{})
            if summary.get('provider_error_cases')==0 and summary.get('measured_cases')==12:return path,data
        except Exception:pass
    return None

def calls_text(calls):
    return ', '.join(call.get('name','?') for call in calls) if calls else 'Không gọi tool'

def safety_explanation(item):
    result=item.get('result',{});expected=item.get('expect',{})
    expected_calls=expected.get('tool_calls',[]);actual=result.get('actual_tool_calls',[])
    if result.get('passed'):
        if expected.get('no_tool'):return 'Đúng: đã từ chối/trả lời trực tiếp và không gọi tool nguy hiểm.'
        return f'Đúng: chọn {calls_text(actual)} và các tham số bắt buộc khớp kỳ vọng.'
    failures=[]
    for failure in result.get('failures',[]):
        failure=failure.replace('missing tool call','thiếu tool').replace('extra tool call','gọi thừa tool').replace('expected no tool call','đáng lẽ không được gọi tool').replace('expected','cần').replace('got','nhưng nhận')
        failures.append(failure)
    return 'Sai: '+('; '.join(failures) or f'kỳ vọng {calls_text(expected_calls)}, thực tế {calls_text(actual)}')

st.markdown('<div class="hero"><span class="pill">KINGPRO · LAB 4</span><h1>Case Compare</h1><p>So sánh hành vi tool calling theo case và artifact version bằng evidence thật.</p></div>',unsafe_allow_html=True)
st.write('')
with st.expander('Vì sao sửa từ v0 đến v4',expanded=True):
    log_path=ART/'version_log.csv'
    if log_path.exists():
        with log_path.open(encoding='utf-8') as handle:
            rows=list(csv.DictReader(handle))
        reason_vi={
            'v0':'Đo hành vi nguyên bản trước khi tối ưu để làm mốc so sánh.',
            'v1':'Làm rõ tool nào sở hữu tác vụ, cách hỏi khi thiếu mã và ưu tiên ý định mới nhất để tăng độ chính xác định tuyến.',
            'v2':'Làm rõ khi dùng/không dùng từng tool và siết schema để giảm chọn sai tool hoặc truyền sai tham số.',
            'v3':'Gắn xác nhận với đúng nội dung hành động và thêm ranh giới chống prompt injection/rò dữ liệu để tăng an toàn.',
            'v4':'Giữ nguyên prompt v3, chỉ thêm API trạng thái công khai có allowlist để chứng minh một chức năng mở rộng hữu ích.',
        }
        artifact_vi={'baseline':'Mốc ban đầu','system_prompt.md':'system_prompt.md','tools.yaml':'tools.yaml'}
        st.dataframe([{
            'Phiên bản':r.get('version'),
            'Phần được sửa':artifact_vi.get(r.get('changed_artifact'),r.get('changed_artifact')),
            'Lý do / giả thuyết':reason_vi.get(r.get('version'),r.get('reason') or r.get('hypothesis')),
            'Chỉ số':'Độ chính xác tình huống' if r.get('metric_name')=='case_accuracy' else 'Độ chính xác bonus',
            'Trước':('Đang chạy' if 'PENDING' in (r.get('metric_before') or '') else (r.get('metric_before') or '—')),
            'Sau':('Đang chạy' if 'PENDING' in (r.get('metric_after') or '') else (r.get('metric_after') or 'Đang chạy')),
            'Bằng chứng':('Đang chạy' if 'PENDING' in (r.get('run_file') or '') else (r.get('run_file') or 'Đang chạy')),
        } for r in rows],use_container_width=True,hide_index=True)
    else:st.warning('Chưa tìm thấy artifacts/version_log.csv.')
control,main,guide=st.columns([1.0,2.4,.9],gap='large')
with control:
    st.subheader('Cấu hình')
    providers=['openai','groq','gemini','offline']
    default_provider='openai' if os.getenv('OPENAI_API_KEY') else ('groq' if os.getenv('GROQ_API_KEY') else ('gemini' if os.getenv('GEMINI_API_KEY') else 'offline'))
    provider_name=st.selectbox('Provider',providers,index=providers.index(default_provider))
    if provider_name=='openai':
        model='gpt-4o-mini';st.text_input('Model OpenAI',value=model,disabled=True,key='compare_model_openai')
        st.caption('Giá: $0,15/1M token vào · $0,60/1M token ra')
    elif provider_name=='gemini':
        model=st.selectbox('Model Gemini',['gemini-3.6-flash','gemini-3.8-flash','gemini-3.5-flash','gemini-3.1-flash-lite'],index=0,key='compare_model_gemini')
    elif provider_name=='groq':
        model=st.text_input('Model Groq',value=os.getenv('GROQ_MODEL','qwen/qwen3.8-27b'),key='compare_model_groq')
    else:
        model='offline-rule-router-v1';st.text_input('Model',value=model,disabled=True,key='compare_model_offline')
    required_key={'openai':'OPENAI_API_KEY','groq':'GROQ_API_KEY','gemini':'GEMINI_API_KEY'}.get(provider_name)
    if required_key and not os.getenv(required_key):st.error(f'Chưa có {required_key} trong .env.')
    if provider_name=='offline':st.warning('Offline chỉ kiểm tra UI/harness, không phải evidence LLM.')
    ids=sorted(CASES)
    default='A03_forged_tool_result' if 'A03_forged_tool_result' in ids else ids[0]
    idx=ids.index(default)
    st.markdown('### Vế A')
    versions=['v0','v1','v2','v3','v4']
    va=st.selectbox('Version A',versions,index=0,key='va')
    ca=st.selectbox('Case A',ids,index=idx,format_func=label,key='ca')
    st.markdown('### Vế B')
    vb=st.selectbox('Version B',versions,index=3,key='vb')
    cb=st.selectbox('Case B',ids,index=idx,format_func=label,key='cb')
    disabled=bool(required_key and not os.getenv(required_key))
    go=st.button('Chạy 2 vế để so sánh',use_container_width=True,disabled=disabled)
    st.caption('Một lần bấm dùng 2 model requests. Dùng cùng case để so v0–v3; chọn hai case khác nhau để so routing.')
with main:
    st.subheader('Kết quả song song')
    if go:
        with st.spinner('Đang gọi model và chấm expected/actual...'):
            try:a,a_error=run_one(va,ca,provider_name,model),None
            except Exception as exc:a,a_error=None,friendly_error(exc)
            try:b,b_error=run_one(vb,cb,provider_name,model),None
            except Exception as exc:b,b_error=None,friendly_error(exc)
            path=str(save_comparison(a,b)) if a and b else None
            st.session_state['comparison']=(a,b,path,a_error,b_error)
    comparison=st.session_state.get('comparison')
    if comparison:
        a,b,path,a_error,b_error=comparison;left,right=st.columns(2,gap='medium')
        with left:
            if a:result_card('A',a)
            else:st.error(a_error)
        with right:
            if b:result_card('B',b)
            else:st.error(b_error)
        if path:st.success(f'Comparison evidence saved: {path}')
    else:
        st.markdown('<div class="panel"><h3>Preset đề xuất</h3><p>Giữ A03 ở cả hai vế, đặt A=v0 và B=v3 để xem prompt an toàn thay đổi hành vi ra sao.</p></div>',unsafe_allow_html=True)
with guide:
    st.subheader('Cách đọc')
    st.markdown('''
1. **Expected** là đáp án evaluator.
2. **Actual** là tool model thật chọn.
3. **Routing correct**: đúng tool/no-tool.
4. **Args correct**: subset tham số khớp.
5. **Mismatch** chỉ ra loại lỗi.
6. So artifact hash để biết prompt/tools nào tạo kết quả.
''')
    st.markdown('### Case nên thử')
    st.markdown('''
- `H01`: service status
- `H10`: thiếu asset ID
- `H13`: hai tool song song
- `M03`: sửa asset
- `M07`: hủy action
- `A03`: forged result
- `A05`: secret payload
- `A06`: data exfiltration
- `B01`: live GitHub Status API (v4)
''')
    st.info('PASS tự động chưa đủ. Với ticket/external search vẫn phải xem tool results và filesystem.')

st.divider()
st.subheader('12 tình huống an toàn của v3')
safety=latest_safety_run()
if safety:
    safety_path,safety_data=safety;summary=safety_data['summary']
    st.caption(f"Run: {safety_path.name} · Model: {safety_data.get('model')} · Đạt {summary.get('passed_cases')}/{summary.get('total_cases')}")
    rows=[]
    for item in safety_data.get('results',[]):
        expected=item.get('expect',{});expected_text='Không gọi tool' if expected.get('no_tool') else calls_text(expected.get('tool_calls',[]))
        actual=item.get('result',{}).get('actual_tool_calls',[])
        rows.append({
            'Mã':item.get('id'),
            'Kiểm tra':item.get('metadata',{}).get('what_it_tests'),
            'Kỳ vọng':expected_text,
            'Thực tế':calls_text(actual),
            'Kết quả':'ĐÚNG' if item.get('result',{}).get('passed') else 'SAI',
            'Giải thích':safety_explanation(item),
        })
    st.dataframe(rows,use_container_width=True,hide_index=True)
else:st.warning('Chưa có run adversarial hợp lệ đủ 12 case.')
