# INDIVIDUAL — NGUYỄN VĂN DUY

- **MSSV:** 2A202602729
- **GitHub:** `Clownnvd`
- **Vai trò:** trưởng nhóm; thiết kế thí nghiệm prompt v0–v3; tích hợp provider, eval và báo cáo.
- **Phần đã thực hiện:** giữ baseline v0, xây snapshot v1–v3, ghi giả thuyết cho từng lần sửa, tích hợp OpenAI/Groq/Gemini và cố định `gpt-4o-mini` cho evidence chính, bổ sung bonus live API có allowlist.
- **Bằng chứng:** `starter_v0/artifacts/versions/`, `starter_v0/artifacts/version_log.csv`, `starter_v0/artifacts/evidence/`, `starter_v0/providers/`, `starter_v0/tools/check_public_status/`.
- **Quyết định kỹ thuật:** dùng cùng provider, model và bộ 30 case khi so v0–v3 để thay đổi metric có thể quy về prompt hoặc tool schema.
- **Failure đã quan sát:** v0 tin fake tool result và tạo ticket; v1 tăng routing nhưng giảm độ chính xác tham số; v3 ban đầu chưa phân biệt tốt fake role và stale confirmation.
- **Cách xử lý:** dùng failure trace để siết schema ở v2 và thêm confirmation provenance, latest intent, cancellation cùng direct-refusal gates ở v3; sau đó chạy regression trên base, group và safety.
- **Kết quả:** v3 base 86,67%; nhóm 10/10; safety 12/12; bonus 2/2; không có provider error.
- **Điều học được:** cần chốt expected behavior và chạy baseline trước khi sửa; prompt giúp model quyết định, tool schema giúp truyền đúng tham số, còn implementation là lớp bảo vệ cuối.
- **Nếu làm lại:** thêm deterministic confirmation token ở backend để giảm phụ thuộc vào việc model tự suy luận nguồn xác nhận.

File này đã được commit bằng Git identity `Clownnvd` và merge vào `main` cùng evidence kỹ thuật của Duy.
