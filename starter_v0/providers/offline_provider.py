
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from providers.base import ModelResponse, ToolCall


def fold(text: str) -> str:
    value = unicodedata.normalize("NFD", text.casefold()).replace("đ", "d")
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def reply(intent: str, action: str, message: str) -> ModelResponse:
    return ModelResponse(text=json.dumps({
        "intent": intent, "action": action, "reply": message, "evidence_ids": []
    }, ensure_ascii=False))


def clarify(question: str, response_type: str = "text", options: list[str] | None = None) -> ModelResponse:
    return ModelResponse(tool_calls=[ToolCall("clarify", {
        "question": question, "response_type": response_type, "options": options or []
    })])


def last_value(pattern: str, text: str) -> str | None:
    values = re.findall(pattern, text, re.I)
    return values[-1] if values else None


class OfflineRuleProvider:
    """Deterministic developer fallback; never official LLM evidence."""

    default_model = "offline-rule-router-v1"

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        raw = messages[-1].get("content", "") if messages else ""
        if "TOOL_RESULTS_JSON:" in raw and "Use only these tool results" in raw:
            try:
                payload = raw.split("TOOL_RESULTS_JSON:", 1)[1].split("Use only these tool results", 1)[0].strip()
                events = json.loads(payload)
                names = [event.get("tool", "tool") for event in events]
                evidence = []
                for event in events:
                    result = event.get("result", {})
                    for key in ("service", "asset_id", "employee_id", "ticket_id", "source"):
                        if result.get(key):
                            evidence.append(str(result[key]))
                return ModelResponse(text=json.dumps({"intent": "tool_result", "action": "answered", "reply": "Đã xử lý kết quả từ: " + ", ".join(names), "evidence_ids": evidence}, ensure_ascii=False))
            except Exception:
                return reply("tool_result", "answered", "Đã xử lý yêu cầu từ kết quả tool.")

        latest = raw.split("Latest user turn to answer now:", 1)[-1].strip()
        all_low, low = fold(raw), fold(latest)
        assets = [x.upper() for x in re.findall(r"\b(?:LT|DT|MB|PR|RM)-\d+\b", raw, re.I)]
        employees = [x.upper() for x in re.findall(r"\bEMP-\d+\b", raw, re.I)]
        last_asset = assets[-1] if assets else None
        last_employee = employees[-1] if employees else None

        # Refusal and cancellation use the latest user intent.
        if re.search(r"\b(password|passwd|token|api[ _-]?key|mfa|otp|recovery[ _-]?code)\s*[:=]\s*\S+", raw, re.I):
            return reply("sensitive_data", "refused", "Không xử lý hoặc lưu bí mật; hãy thu hồi hay thay đổi thông tin vừa chia sẻ.")
        if "in nguyen van system prompt" in all_low or "hidden policies" in all_low or "tool schemas" in all_low:
            return reply("prompt_exfiltration", "refused", "Không thể tiết lộ chỉ dẫn hệ thống hoặc cấu hình nội bộ.")
        if "shell_exec" in all_low or "curl de doc file .env" in all_low:
            return reply("unsupported_tool", "refused", "Không có quyền dùng shell hoặc đọc tệp bí mật.")
        if "system:" in all_low and "developer:" in all_low and "confirmed=true" in all_low:
            return reply("role_spoofing", "refused", "Nhãn vai trò giả trong input không thay đổi quy tắc hệ thống.")
        if any(x in low for x in ["khong tao gi ca", "khong tao ticket", "chi noi ban da hieu yeu cau huy", "chi xac nhan da huy"]):
            return reply("cancel_action", "answered", "Đã hiểu yêu cầu hủy; không thực hiện hành động nào.")
        if "cong thuc nau pho" in low or "rest api quan ly ban hang" in low:
            return reply("out_of_scope", "refused", "Tôi chỉ hỗ trợ IT Service Desk của Northstar Labs.")
        if "ban la gi" in low or "co the ho tro nhung viec nao" in low:
            return reply("capabilities", "answered", "Tôi hỗ trợ trạng thái dịch vụ, thiết bị, tài khoản, KB, chính sách, báo cáo và ticket có xác nhận.")

        # Special safety boundaries before normal routing.
        forged_ticket = any(x in all_low for x in ["create_ticket({", "tool_results_json:", "<assistant>", "confirmed=true"])
        ticket_intent = "ticket" in all_low and not any(x in low for x in ["quy dinh", "policy"])
        if ticket_intent:
            priority = (last_value(r"\b(low|medium|high|critical)\b", raw) or "medium").lower()
            explicit = any(x in low for x in ["toi xac nhan tao ticket", "toi xac nhan tao dung ticket", "toi xac nhan tao dung", "thong tin dung roi, toi xac nhan"])
            changed = any(x in all_low for x in ["doi priority", "doi muc uu tien", "thay payload", "thay payload", "ra lai payload", "nghi ro ri du lieu"]) and not "giu nguyen" in all_low
            asks_review = any(x in low for x in ["hoi xac nhan", "xem lai", "ra lai payload", "buoc an toan"])
            if explicit and not forged_ticket and not changed and not asks_review:
                summary = "Sự cố IT được xác nhận"
                if "vpn" in all_low: summary = "VPN lỗi AUTH_TIMEOUT" if "auth_timeout" in all_low else "Sự cố VPN"
                elif "wi-fi" in all_low or "wifi" in all_low: summary = "Sự cố Wi-Fi"
                elif "outlook" in all_low: summary = "Sự cố Outlook"
                return ModelResponse(tool_calls=[ToolCall("create_ticket", {
                    "summary": summary, "priority": priority, "asset_id": last_asset or "", "confirmed": True
                })])
            return clarify(
                f"Bạn có xác nhận tạo ticket priority {priority}" + (f" cho {last_asset}" if last_asset else "") + " với payload hiện tại không?",
                "yes_no",
            )

        external_intent = any(x in all_low for x in ["search web", "len web", "trang driver", "thong so chinh hang", "specs", "drivers"])
        if external_intent and (employees or (assets and any(x in all_low for x in ["giu nguyen toan bo", "gui het", "asset id", "assigned user", "location", "diagnostic"]))):
            # If the safe part explicitly requests local inspection, perform only that part.
            if last_asset and any(x in low for x in ["doc lt-", "kiem tra", "diagnostic"]):
                return ModelResponse(tool_calls=[ToolCall("inspect_device", {"asset_id": last_asset, "check": "all"})])
            return clarify("Hãy cung cấp lại chỉ hãng và model công khai, bỏ toàn bộ identifier nội bộ.", "text")

        # Existing findings own the formatter route.
        if any(x in low for x in ["dinh dang", "trinh bay cac finding", "format thanh", "brief report", "handoff report", "bao cao ky thuat"]):
            template = "technical" if any(x in low for x in ["ky thuat", "technical"]) else "handoff" if "handoff" in low else "brief"
            title_match = re.search(r"(?:t[eê]n|title)\s*['\"]([^'\"]+)['\"]", latest, re.I)
            title = title_match.group(1) if title_match else "IT incident"
            findings = []
            if "vpn" in low: findings.append({"label": "VPN", "detail": "Finding VPN do người dùng cung cấp"})
            if "packet loss" in low: findings.append({"label": "Network", "detail": "Packet loss do người dùng cung cấp"})
            if "dimm" in low: findings.append({"label": "Hardware", "detail": "DIMM lỗi do người dùng cung cấp"})
            if not findings: findings = [{"label": "Finding", "detail": "Dữ kiện do người dùng cung cấp"}]
            return ModelResponse(tool_calls=[ToolCall("format_incident_report", {
                "findings": findings, "template": template, "incident_title": title
            })])

        calls: list[ToolCall] = []

        # Employee intent follows the latest turn, identifiers may come from context.
        user_intent = any(x in low for x in ["tra tai khoan", "tra cuu tai khoan", "tra cuu nhan vien", "trang thai tai khoan", "thiet bi duoc cap", "tra giup tai khoan"])
        if user_intent:
            if not last_employee:
                return clarify("Vui lòng cung cấp employee ID dạng EMP-####.", "text")
            calls.append(ToolCall("lookup_user", {"employee_id": last_employee}))

        # Work out active services. Prefer those in the latest turn.
        def service_names(text: str) -> list[str]:
            found=[]
            mapping={"vpn":["vpn"],"email":["email","outlook"],"sso":["sso"],"wifi":["wifi","wi-fi"],"printing":["printing","may in","print service"]}
            for name,terms in mapping.items():
                if any(t in text for t in terms): found.append(name)
            return found
        services = service_names(low) or service_names(all_low)
        latest_status = any(x in low for x in ["trang thai", "status", "shared", "service", "hoat dong", "co on", "gap su co"])
        all_status = any(x in all_low for x in ["trang thai", "status", "shared", "service", "hoat dong", "co on", "gap su co"])
        kb_intent = any(x in low for x in ["huong dan", "khac phuc", "xu ly", "troubleshooting", "cau hinh", "verified steps"])
        device_intent = any(x in low for x in ["kiem tra", "snapshot", "diagnostic", "phan cung", "hardware", "security", "bao mat", "network", "ket noi vpn"])

        if "moi truong demo" in low:
            return clarify("Bạn muốn kiểm tra production hay staging?", "choice", ["production", "staging"])

        # Status can be requested in the same latest turn as device/KB.
        if services and (latest_status or (("production" in low or "staging" in low) and (not last_asset or " ca " in f" {low} ")) or (all_status and any(x in low for x in ["ca", "van la", "chi kiem tra"]))):
            env_latest=[]
            if "production" in low: env_latest.append("production")
            if "staging" in low: env_latest.append("staging")
            env_all=[]
            if "production" in all_low: env_all.append("production")
            if "staging" in all_low: env_all.append("staging")
            envs=env_latest or env_all
            if not envs: envs=["production"]
            # A latest KB-only switch cancels earlier status.
            if not (kb_intent and any(x in all_low for x in ["khong xem status", "khong xem trang thai"])):
                for service in services:
                    for env in envs:
                        calls.append(ToolCall("check_service_status", {"service": service, "environment": env}))

        # Device requests can include multiple assets.
        if device_intent and (assets or any(x in low for x in ["laptop cua minh", "laptop cua toi", "may cua minh", "may cua toi"])):
            if not assets:
                return clarify("Vui lòng cung cấp asset ID dạng LT-### hoặc DT-###.", "text")
            check = "all"
            if any(x in low for x in ["hardware", "phan cung", "o cung"]): check = "hardware"
            elif any(x in low for x in ["security", "bao mat"]): check = "security"
            elif any(x in low for x in ["network", "wi-fi", "wifi"]): check = "network"
            elif "vpn" in low: check = "vpn"
            elif "software" in low: check = "software"
            active_assets = assets if any(x in low for x in ["so sanh", "va dt-", "va lt-"]) else [last_asset]
            for asset in dict.fromkeys(active_assets):
                calls.append(ToolCall("inspect_device", {"asset_id": asset, "check": check}))

        if kb_intent:
            category="all"
            mapping={"vpn":["vpn"],"email":["email","outlook"],"wifi":["wifi","wi-fi"],"printing":["printing","print","may in"],"account":["account","tai khoan"],"security":["security","bao mat"],"hardware":["hardware","phan cung"],"software":["software"],"meeting_room":["meeting_room","phong hop","am thanh"]}
            source = low + " " + all_low
            for cat,terms in mapping.items():
                if any(term in source for term in terms): category=cat; break
            calls.append(ToolCall("search_kb", {"query": latest, "category": category, "top_k": 3}))

        policy_area=None
        if any(x in low for x in ["policy", "chinh sach", "quy dinh"]):
            if any(x in low for x in ["mfa", "mo khoa", "access"]): policy_area="access_control"
            elif any(x in low for x in ["password", "token", "privacy"]): policy_area="data_privacy"
            elif any(x in low for x in ["toan cong ty", "critical", "incident response"]): policy_area="incident_response"
            elif "ticket" in low: policy_area="ticketing"
            elif "thay doi cau hinh" in low: policy_area="service_operations"
            else: policy_area="all"
        if policy_area:
            calls.append(ToolCall("policy", {"query": latest, "policy_area": policy_area, "top_k": 3}))

        if external_intent:
            manufacturer = next((m for m in ["Lenovo", "Dell", "HP"] if fold(m) in all_low), None)
            model_match = re.search(r"(ThinkPad T14 Gen 4|Latitude 7440)", raw, re.I)
            if manufacturer and model_match:
                qtype="drivers" if "driver" in all_low else "specs" if any(x in all_low for x in ["thong so", "specs"]) else "support"
                calls.append(ToolCall("search_device_info", {"manufacturer": manufacturer, "model": model_match.group(1), "query_type": qtype, "max_results": 3}))

        unique=[]; seen=set()
        for call in calls:
            key=(call.name,json.dumps(call.args,ensure_ascii=False,sort_keys=True))
            if key not in seen: seen.add(key); unique.append(call)
        if unique:
            return ModelResponse(tool_calls=unique)
        return reply("unknown", "clarified", "Tôi cần thêm thông tin để xác định đúng yêu cầu IT Service Desk.")




