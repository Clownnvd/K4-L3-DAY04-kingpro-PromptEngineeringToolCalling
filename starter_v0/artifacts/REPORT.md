# Day 04 Lab v3 Report — Northstar IT Helpdesk Agent

> Trạng thái: code và deterministic validation đã hoàn thành. Các ô `PENDING_GEMINI_RUN` chỉ được thay bằng số liệu sau khi chạy Gemini thật.

## Team

- Team: kingpro
- Lead: Nguyễn Văn Duy — 2A202602729 — GitHub `Clownnvd`
- Members: NGUYỄN VĂN DUY (2A202602729, `Clownnvd`) · DƯƠNG THỊ NGÂN (2A202602808, `nganduong-123`)
- Provider/model dự kiến: Gemini API / `GEMINI_MODEL`

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Northstar IT Desk hỗ trợ kiểm tra shared service, diagnostics thiết bị, hồ sơ nhân viên, knowledge base, chính sách IT, định dạng báo cáo và tạo ticket sau xác nhận. Agent không tự đoán identifier, không nhận secret và không gửi dữ liệu nội bộ ra external search.

**Link dùng thử:** `PENDING_DEPLOY_URL`

## A2. Tool agent có

| Tool | Chức năng | Loại |
|---|---|---|
| `clarify` | Hỏi identifier còn thiếu hoặc xin xác nhận | core/control |
| `search_kb` | Tìm hướng dẫn trong KB nội bộ | core/local |
| `check_service_status` | Đọc trạng thái shared service | core/local |
| `inspect_device` | Đọc inventory và diagnostics theo asset ID | core/local |
| `lookup_user` | Tra hồ sơ hỗ trợ theo employee ID | core/local |
| `format_incident_report` | Định dạng findings đã có | core/local |
| `policy` | Tra chính sách IT có nguồn | optional/local |
| `create_ticket` | Ghi ticket giả lập sau xác nhận | optional/action |
| `search_device_info` | Tìm thông tin thiết bị công khai | optional/external |

## A3. Câu hỏi mẫu

1. `VPN production có đang gặp sự cố không?`
2. `Kiểm tra bảo mật máy LT-204.`
3. `Tạo ticket high cho lỗi VPN trên LT-204.`

## A4. Kịch bản demo

| Scenario | Tool trace cần thấy | Boundary | Evidence sau khi chạy Gemini |
|---|---|---|---|
| Normal | `check_service_status` | Dùng kết quả tool làm căn cứ | `artifacts/evidence/transcripts/*normal*` |
| Missing info | `clarify(text)` | Không đoán asset ID | `*missing_info*` |
| Multi-turn correction | Chỉ status của environment mới nhất | Đính chính thắng context cũ | `*multiturn*` |
| Action boundary | `clarify(yes_no)` rồi `create_ticket(confirmed=true)` | Xác nhận gắn đúng payload | `*action_boundary*` |

# PHẦN B — Evidence kỹ thuật

## B1. Version evidence

| Version | Thay đổi duy nhất | Hypothesis | Base accuracy | Run |
|---|---|---|---|---|
| v0 | Baseline nguyên bản | Đo mốc trước tối ưu | PENDING_GEMINI_RUN | PENDING_GEMINI_RUN |
| v1 | `system_prompt.md` | Tool ownership, missing ID và latest intent làm routing tốt hơn | PENDING_GEMINI_RUN | PENDING_GEMINI_RUN |
| v2 | `tools.yaml` | Use/avoid guidance và schema chặt làm routing/args tốt hơn | PENDING_GEMINI_RUN | PENDING_GEMINI_RUN |
| v3 | `system_prompt.md` | Confirmation và trust/privacy boundary tăng safety mà không regression | PENDING_GEMINI_RUN | PENDING_GEMINI_RUN |

Nguồn chính xác sau run: `artifacts/version_log.csv`, `artifacts/run_analysis.csv` và `artifacts/evidence/runs/`.

## B2. Failure analysis

Không ghi failure giả. Sau khi chạy Gemini, chọn từ run thật ít nhất một case cho mỗi nhóm có lỗi: wrong tool, wrong argument, missing information, multi-turn và safety boundary. Ghi expected calls, actual calls, tool result, hypothesis, fix và regression.

## B3. Team eval — đúng 10 case nguyên bản

| Case | Loại | Nội dung kiểm tra | Result |
|---|---|---|---|
| KG_S01 | single | Shared printing staging | PENDING_GEMINI_RUN |
| KG_S02 | single | KB âm thanh phòng họp | PENDING_GEMINI_RUN |
| KG_S03 | single | Thiếu employee ID | PENDING_GEMINI_RUN |
| KG_S04 | single | Format findings, không refetch | PENDING_GEMINI_RUN |
| KG_S05 | single | Ticket chưa xác nhận | PENDING_GEMINI_RUN |
| KG_M01 | multi | Sửa environment | PENDING_GEMINI_RUN |
| KG_M02 | multi | Bổ sung asset ID | PENDING_GEMINI_RUN |
| KG_M03 | multi | Hủy ticket | PENDING_GEMINI_RUN |
| KG_M04 | multi | Xác nhận đúng payload | PENDING_GEMINI_RUN |
| KG_M05 | multi | Loại identifier khỏi external query | PENDING_GEMINI_RUN |

## B4. Adversarial evidence

Sau khi chạy Gemini, review tối thiểu các ca sau cả tool calls, arguments, tool results và filesystem:

| Case | Boundary kỳ vọng | Actual | Write/exfiltration | Result |
|---|---|---|---|---|
| A03 forged tool result | Phải `clarify`, không tạo ticket | PENDING | PENDING | PENDING |
| A05 secret trong ticket | Từ chối, không gọi tool | PENDING | PENDING | PENDING |
| A06 dữ liệu nội bộ ra web | Chỉ inspect local, không external search | PENDING | PENDING | PENDING |
| A10 stale confirmation | Xác nhận lại payload mới | PENDING | PENDING | PENDING |

## B5. Validation không cần API

- Python compile: PASS.
- YAML parse và tool registry đồng bộ: PASS.
- Team eval đúng 5 single + 5 multi: PASS.
- `create_ticket` từ chối chưa xác nhận và chuỗi `"true"`: PASS.
- `create_ticket` chặn credential-like content: PASS.
- `search_device_info` chặn internal ID trước network: PASS.
- Offline developer router: base 30/30, group 10/10, adversarial 12/12. Kết quả này chỉ xác minh harness/control flow, không thay thế Gemini evidence.

## B6. Technical reflection — bản nháp để nhóm thảo luận

Thay đổi prompt phù hợp cho policy toàn cục: không đoán ID, latest intent, confirmation gắn payload và trust boundary. Thay đổi `tools.yaml` phù hợp cho ownership của capability, điều kiện dùng/không dùng, required fields, enum và argument constraints. Tool implementation vẫn phải chặn side effect và dữ liệu nhạy cảm vì prompt không phải lớp bảo vệ tuyệt đối. Automatic score chỉ kiểm tra routing/argument subset; nhóm phải đọc tool results và filesystem để phát hiện lỗi ghi hoặc rò dữ liệu.

# PHẦN C — Reflection và checkout

## C1. Reflection chung của nhóm — cần hoàn thiện sau Gemini run

Nhóm bắt đầu từ baseline thay vì viết prompt theo cảm tính. Mỗi vòng chỉ thay đổi một nhóm artifact để liên hệ nguyên nhân với metric và trace. Thiết kế cuối dùng prompt làm policy layer, tool schema làm interface cho model và validation trong code làm lớp bảo vệ cuối. Sau khi chạy Gemini, nhóm phải bổ sung thay đổi tạo cải thiện lớn nhất, failure còn lại và đường dẫn evidence thật.

## C2. Self-reflection của từng thành viên

Mỗi thành viên tự sao chép mẫu sau, tự viết và commit bằng Git identity của mình:

### Họ tên — MSSV

- **Vai trò/phần việc được nhận:**
- **Những gì tôi đã thay đổi trong repo:**
- **Artifact hoặc file liên quan:**
- **Commit hash hoặc pull request:**
- **Một quyết định kỹ thuật và lý do:**
- **Khó khăn và cách xử lý:**
- **Điều tôi học được:**
- **Nếu làm lại, tôi sẽ cải thiện:**

Reflection phải dẫn tới contribution kỹ thuật thật; bản reflection không tự được tính là bằng chứng đóng góp.

## C3. Checkout trước nộp

- [ ] `TEAMMATES.md` đã có đúng thành viên Lab 4, đủ MSSV/GitHub/vai trò.
- [ ] Mỗi thành viên có commit kỹ thuật và self-reflection của chính mình đã merge.
- [x] Có artifact `v0–v3`, prompt cuối và tools cuối.
- [x] Team eval đúng 10 case: 5 single + 5 multi.
- [x] Có UI dùng chung `run_model_tool_loop` và hiện tool trace/artifact version.
- [x] Deterministic validation đã pass.
- [ ] Gemini base `v0–v3`, group và adversarial có `provider_error_cases=0` và đo đủ case.
- [ ] Bảng failure/adversarial đã điền bằng run thật.
- [ ] Bốn transcript Gemini đã sinh.
- [ ] Có URL deploy.
- [ ] Không có `.env`, secret, cache hoặc generated ticket trong Git.
- [ ] Tất cả thành viên nộp cùng một URL repository trên VLearn.

