from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]

def main():
 p=argparse.ArgumentParser();p.add_argument('--allow-placeholders',action='store_true');args=p.parse_args();errors=[]
 def check(ok,msg):
  print(('PASS' if ok else 'FAIL')+' | '+msg)
  if not ok:errors.append(msg)
 tools_path=ROOT/'starter_v0'/'artifacts'/'tools.yaml';data_path=ROOT/'starter_v0'/'data'/'eval_group.json'
 tools=yaml.safe_load(tools_path.read_text(encoding='utf-8-sig'))['tools'];check(len(tools)==9,'Có đúng 9 tool declarations')
 for tool in tools:
  check(len(tool.get('description',''))>=70,f"{tool['name']} description đủ cụ thể")
  check(isinstance(tool.get('parameters',{}).get('required',[]),list),f"{tool['name']} có required fields")
 data=json.loads(data_path.read_text(encoding='utf-8-sig'));cases=data.get('cases',[]);single=[c for c in cases if 'turns' not in c];multi=[c for c in cases if 'turns' in c]
 check(len(cases)==10,'Team eval đúng 10 case');check(len(single)==5 and len(multi)==5,'Team eval đúng 5 single + 5 multi');check(len({c.get('id') for c in cases})==10,'Case IDs duy nhất')
 changed=[c for c in cases if c.get('metadata',{}).get('change_by_ngan') and '[NGÂN' not in c['metadata']['change_by_ngan']]
 if not args.allow_placeholders:check(len(changed)>=3,'Ít nhất 3 case có change_by_ngan thật')
 for rel in ['starter_v0/app.py','starter_v0/chat.py','starter_v0/scripts/run_demo_scenarios.py']:
  check((ROOT/rel).exists(),f'{rel} tồn tại')
 app=(ROOT/'starter_v0'/'app.py').read_text(encoding='utf-8-sig');check('run_model_tool_loop' in app,'UI dùng chung run_model_tool_loop')
 review=(ROOT/'starter_v0'/'artifacts'/'ngan_adversarial_review.md').read_text(encoding='utf-8-sig');reflection=(ROOT/'starter_v0'/'artifacts'/'self_reflection_ngan.md').read_text(encoding='utf-8-sig')
 if not args.allow_placeholders:
  check('[NGÂN ĐIỀN]' not in review and '[NGÂN TỰ' not in review,'Adversarial review đã bỏ placeholder')
  written=[line for line in reflection.splitlines() if line.strip()[:2] in {f'{i}.' for i in range(1,10)} and '[NGÂN' not in line and '[Tuỳ chọn]' not in line]
  check(len(written)>=8,'Reflection có tối thiểu 8 câu thật')
  try:
   branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip();check('nganduong-123' in branch,'Đang ở branch của Ngân')
  except Exception:check(False,'Đọc được Git branch')
 if errors:raise SystemExit(f'NGAN DELIVERY FAIL: {len(errors)} mục')
 print('NGAN DELIVERY PASS' if not args.allow_placeholders else 'NGAN STARTER PACKAGE VALID')
if __name__=='__main__':main()
