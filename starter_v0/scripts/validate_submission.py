
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import TOOL_FUNCTIONS, load_tool_declarations


def check(condition: bool, message: str, errors: list[str]) -> None:
    print(("PASS" if condition else "FAIL") + " | " + message)
    if not condition: errors.append(message)


def main() -> None:
    errors=[]
    artifacts=ROOT/"artifacts"
    declarations=load_tool_declarations(artifacts/"tools.yaml")
    names=[x["name"] for x in declarations]
    check(len(names)==len(set(names)),"Tool names are unique",errors)
    check(set(names)==set(TOOL_FUNCTIONS),"tools.yaml matches the implementation registry",errors)
    for item in declarations:
        schema=item.get("parameters",{})
        check(bool(item.get("description")),f"{item['name']} has a description",errors)
        check(schema.get("type")=="object",f"{item['name']} uses an object schema",errors)
        check(isinstance(schema.get("required",[]),list),f"{item['name']} declares required fields",errors)

    data=json.loads((ROOT/"data"/"eval_group.json").read_text(encoding="utf-8"))
    cases=data.get("cases",[])
    single=[c for c in cases if "turns" not in c]
    multi=[c for c in cases if "turns" in c]
    check(len(cases)==10,"Team eval contains exactly 10 cases",errors)
    check(len(single)==5 and len(multi)==5,"Team eval is 5 single-turn + 5 multi-turn",errors)
    ids=[c.get("id") for c in cases]
    check(len(ids)==len(set(ids)),"Team eval IDs are unique",errors)

    versions=artifacts/"versions"
    for version in ["v0","v1","v2","v3"]:
        check((versions/version/"system_prompt.md").exists(),f"{version} prompt snapshot exists",errors)
        check((versions/version/"tools.yaml").exists(),f"{version} tools snapshot exists",errors)
        yaml.safe_load((versions/version/"tools.yaml").read_text(encoding="utf-8"))
    check((versions/"v0"/"system_prompt.md").read_bytes() != (versions/"v1"/"system_prompt.md").read_bytes(),"v1 changes the prompt",errors)
    check((versions/"v1"/"tools.yaml").read_bytes() != (versions/"v2"/"tools.yaml").read_bytes(),"v2 changes tool declarations",errors)
    check((versions/"v2"/"system_prompt.md").read_bytes() != (versions/"v3"/"system_prompt.md").read_bytes(),"v3 changes the prompt",errors)

    # Deterministic action/privacy guardrails.
    from tools.create_ticket.tool import create_ticket
    from tools.search_device_info.tool import search_device_info
    no_confirm=create_ticket("VPN mock incident","high","LT-204",False)
    string_confirm=create_ticket("VPN mock incident","high","LT-204","true")
    secret=create_ticket("password=ExampleOnly123","high","LT-204",True)
    external=search_device_info("Lenovo","ThinkPad T14 Gen 4 LT-204","drivers",1)
    check(no_confirm.get("status")=="needs_confirmation","Ticket write requires confirmation",errors)
    check(string_confirm.get("status")=="needs_confirmation","String true is not accepted as confirmation",errors)
    check(secret.get("error")=="restricted_sensitive_data","Ticket rejects credential-like content",errors)
    check(external.get("error")=="restricted_internal_identifier","External search rejects internal IDs before network",errors)

    prompt=(artifacts/"system_prompt.md").read_text(encoding="utf-8")
    for marker in ["## Identity","## Decision rules","## Clarification and context","## Action confirmation","## Safety boundaries","## Output contract"]:
        check(marker in prompt,f"Final prompt contains {marker}",errors)
    check(not re.search(r"OPENAI_API_KEY\s*=\s*\S+", "\n".join(p.read_text(encoding="utf-8",errors="ignore") for p in ROOT.rglob("*.md"))),"No OpenAI key appears in Markdown",errors)

    if errors:
        raise SystemExit(f"\nValidation failed: {len(errors)} issue(s).")
    print("\nAll deterministic submission checks passed.")

if __name__=="__main__": main()
