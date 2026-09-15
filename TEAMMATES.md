# TEAMMATES — K4-L3B kingpro

| Họ tên | MSSV | GitHub | Vai trò | Tỷ lệ dự kiến |
|---|---|---|---|---:|
| NGUYỄN VĂN DUY | 2A202602729 | `Clownnvd` | Prompt, experiment v0–v3, integration, report | 50% |
| DƯƠNG THỊ NGÂN | 2A202602808 | `nganduong-123` | Tool contracts, team eval, safety, UI/transcript | 50% |

Mỗi thành viên phải tự chạy phần được giao, tự viết reflection và tự commit bằng Git identity của mình. Main cuối giữ commit riêng của cả hai; không squash khi merge.

## Phân công và bằng chứng chi tiết

### NGUYỄN VĂN DUY — Trưởng nhóm, 50%

| Đầu việc | Nội dung đã thực hiện | File/bằng chứng |
|---|---|---|
| Điều phối và tích hợp | Chốt Helpdesk Agent, chia phần việc 50/50, tích hợp contribution của Ngân và xử lý xung đột | PR #5, merge commit `36beaee` |
| Thí nghiệm v0–v3 | Giữ baseline; thiết kế giả thuyết v1, v2, v3; chạy cùng provider/model và cùng 30 case | `starter_v0/artifacts/versions/`, `version_log.csv` |
| Prompt v1 và v3 | Làm rõ routing, missing ID, latest intent, cancellation, confirmation provenance, prompt injection và privacy | `artifacts/versions/v1/system_prompt.md`, `artifacts/versions/v3/system_prompt.md` |
| Tích hợp model | Hoàn thiện adapter OpenAI, Gemini, Groq; chọn `gpt-4o-mini` cho evidence chính và ghi usage/cost | `providers/`, `chat.py`, `app.py` |
| Bonus tool thật | Xây `check_public_status` gọi API chính thức có allowlist, thêm schema, test và evidence | `tools/check_public_status/`, `data/eval_bonus.json` |
| Chạy và kiểm chứng final | Base v0–v3, group 10/10, safety 12/12, bonus 2/2; chuẩn hóa hash CRLF/LF | `artifacts/evidence/`, `scripts/verify_final_evidence.py`, `versioning.py` |
| Báo cáo | Tổng hợp metric, ba failure analysis, giới hạn, chi phí và checklist nộp | `artifacts/REPORT.md`, `INDIVIDUAL-NguyenVanDuy.md` |

**Commit/PR chính:** `c798c87`, `00d84a5`, `c84585f`, `f565a6d`, `ba4eb90`; PR #5.

### DƯƠNG THỊ NGÂN — Thành viên, 50%

| Đầu việc | Nội dung đã thực hiện | File/bằng chứng |
|---|---|---|
| Tool contracts | Review và làm rõ điều kiện dùng/không dùng, tham số và ranh giới của các tool | `starter_v0/artifacts/tools.yaml`, các snapshot `versions/*/tools.yaml` |
| Bộ 10 case nhóm | Hoàn thiện đúng 5 case một lượt và 5 case nhiều lượt; ghi expected tool/args | `starter_v0/data/eval_group.json` |
| Safety review | Chạy và đọc adversarial suite; phân tích confirmation giả, secret và rò dữ liệu | `artifacts/ngan_adversarial_review.md`, evidence Groq trong commit của Ngân |
| UI và transcript ban đầu | Tích hợp Streamlit với `run_model_tool_loop`; hiển thị tool name, args, result/error và artifact version | `starter_v0/app.py`, `scripts/run_demo_scenarios.py` |
| Provider và kiểm tra | Bổ sung Groq/offline adapter, chạy group/adversarial và bốn transcript | `providers/groq_provider.py`, `providers/offline_provider.py`, `artifacts/evidence/` |
| Reflection cá nhân | Ghi phần việc, kết quả, lỗi quan sát, bài học và hướng cải thiện | `artifacts/self_reflection_ngan.md` |

**Commit/PR chính chủ:** `9275944`, `fef1e6b`; PR #3. Hai commit dùng tên **Dương Thị Ngân**, email GitHub `nguyenngan20022003@gmail.com`, tài khoản `nganduong-123` và đã nằm trên `main`.

## Kết quả tích hợp chung

- Evidence chính dùng cùng `gpt-4o-mini`; không trộn điểm giữa các model.
- Bộ nhóm: 10/10; bộ an toàn: 12/12; bonus API: 2/2; provider error: 0.
- `main` giữ commit riêng của cả hai thành viên bằng merge commit, không squash.
- `.env`, API key, cache và ticket phát sinh không được đưa lên GitHub.
