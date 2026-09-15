# Self-reflection — DƯƠNG THỊ NGÂN

- MSSV: `2A202602808`
- GitHub: `nganduong-123`
- Branch: `contrib/nganduong-123`
- Technical commit: `9275944`

## Reflection

1. Tôi phụ trách tool contracts, team eval, safety review và giao diện có trace cho phần 50% của mình.
2. Tôi sửa `artifacts/tools.yaml` để điều kiện dùng/không dùng của `clarify` và `search_device_info` rõ hơn.
3. Tôi chỉnh ba case trong `data/eval_group.json` và ghi lý do tại `metadata.change_by_ngan`, thay vì đổi expected để chạy theo model.
4. Bộ group eval bằng Groq đạt 10/10, đo đủ 10 case và không có provider error; run nằm trong `artifacts/evidence/runs/`.
5. Bộ adversarial Groq đo đủ 12 case, đạt 10/12; A03 và A11 cho thấy model chọn đúng tool nhưng từng dùng sai `response_type`.
6. Từ lỗi A03/A11, tôi làm rõ rằng yêu cầu tạo ticket có confirmation giả hoặc stale phải gọi `clarify` dạng `yes_no`.
7. Tôi kiểm tra A05 không gọi tool khi input chứa mật khẩu và A06 chỉ đọc asset bằng tool local, không gửi dữ liệu ra web.
8. Tôi tích hợp Groq `openai/gpt-oss-120b` qua adapter tương thích OpenAI và giữ API key trong `.env` đã được Git bỏ qua.
9. Tôi dùng chung `run_model_tool_loop` cho CLI, eval và Streamlit để UI không tạo một luồng agent khác với phần được chấm.
10. Bốn transcript normal, missing-info, multi-turn và action-boundary cho thấy tool name, arguments, results và version artifact có thể truy lại khi review.
11. Nếu làm lại, tôi sẽ chạy nhiều lần mỗi adversarial case để đo độ ổn định theo provider thay vì chỉ nhìn một điểm accuracy.
