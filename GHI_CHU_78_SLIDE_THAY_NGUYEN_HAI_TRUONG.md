# Ghi chú toàn bộ deck Day 04 — Thầy Nguyễn Hải Trường

Nguồn đã đọc: `Day04_Nguyen_Hai_Truong_78_trang.pdf` (78 slide).

## Tư tưởng xuyên suốt

Prompt là giao diện giữa ý định con người và hành vi mô hình. Prompt tốt không được đánh giá bằng độ dài hay câu chữ "hay", mà bằng việc tạo ra hành vi mong muốn ổn định, có thể kiểm tra và tái lập. Tool calling là giao diện giữa mô hình và thế giới bên ngoài; mô hình chỉ đề xuất tool và arguments, còn ứng dụng chịu trách nhiệm kiểm tra, thực thi, xử lý lỗi và trả kết quả lại cho mô hình.

## 1. Prompt cơ bản

- Bắt đầu bằng `Task + Format`; chỉ thêm `Role` và `Context` khi chúng thực sự cải thiện chất lượng hoặc độ nhất quán.
- `Specificity beats cleverness`: prompt ngắn, rõ và đo được tốt hơn prompt dài, hoa mỹ nhưng mơ hồ.
- Khi cấm một hành vi, phải chỉ ra hành vi thay thế. Ví dụ: thay vì chỉ ghi "không đoán", ghi "nếu thiếu asset ID, gọi clarify để hỏi lại".
- Prompt cần được cải tiến theo vòng: viết → chạy test → quan sát lỗi → đặt giả thuyết → sửa → chạy lại cùng bộ test.
- Không thêm token nếu phần bổ sung không làm thay đổi hành vi cần đạt.

## 2. Kỹ thuật nâng cao

- Thử zero-shot trước.
- Dùng one-shot/few-shot khi mô hình đã hiểu nhiệm vụ nhưng sai định dạng hoặc hành vi không ổn định. Chỉ dùng 2–5 ví dụ đúng, đa dạng và có edge case.
- Dùng decomposition/CoT cho bài toán cần suy luận nhiều bước; không dùng cho extraction hoặc formatting đơn giản.
- Structured output phải có schema cụ thể và luôn được validate ở tầng ứng dụng.
- Temperature chỉ điều chỉnh độ ngẫu nhiên, không sửa được một prompt mơ hồ. Không tune temperature và top_p cùng lúc.

## 3. System prompt production-grade

Một system prompt cần năm phần:

1. `Identity/Persona`: agent là ai, thuộc phạm vi nào, phong cách giao tiếp nào.
2. `Rules`: hành vi luôn phải thực hiện.
3. `Capabilities`: agent có tool/dữ liệu nào và ranh giới từng tool.
4. `Constraints`: hành vi bị cấm, điều kiện từ chối, hỏi lại hoặc chuyển người.
5. `Output contract`: ngôn ngữ, cấu trúc JSON/Markdown, các trường và giá trị hợp lệ.

System prompt không được mâu thuẫn, không dùng yêu cầu mơ hồ như "hãy thông minh", không nhồi quá nhiều nội dung và không hard-code test case.

## 4. Context engineering

- Chỉ đưa dữ kiện liên quan vào context; không đổ toàn bộ lịch sử hội thoại.
- Đặt chỉ dẫn quan trọng ở đầu hoặc cuối vì nội dung giữa context dài dễ bị bỏ quên.
- Giữ lịch sử gần nhất và dữ kiện liên quan; tóm tắt, bỏ hoặc lưu ngoài context những phần cũ.
- Phân bổ token riêng cho system prompt, history, tool schemas và output buffer.
- Với knowledge base, truy xuất theo nhu cầu, giới hạn chunk và top-k, kèm nguồn.

## 5. An toàn và đánh giá

- Phòng vệ nhiều lớp: phân cách input không tin cậy, ưu tiên instruction hierarchy, validate input, validate output, cấp quyền tối thiểu và yêu cầu con người xác nhận với hành động nhạy cảm.
- Phải kiểm tra happy path, câu mơ hồ, ngoài phạm vi, prompt injection, quyết định gọi tool và tính nhất quán định dạng.
- Đánh giá correctness, consistency và safety trên cùng một bộ test; so sánh A/B giữa các phiên bản.
- Prompt chỉ là lớp đầu. Ứng dụng và tool implementation vẫn phải chặn thao tác nguy hiểm nếu mô hình gọi sai.

## 6. Tool calling và thiết kế tool

- Luồng chuẩn: user → mô hình quyết định → tool-call JSON → ứng dụng validate/thực thi → tool result → mô hình tổng hợp câu trả lời.
- Tên tool ngắn và diễn đạt đúng hành động.
- Description phải nói đủ: tool làm gì, khi nào dùng, khi nào không dùng.
- JSON Schema phải phân biệt required/optional, dùng enum và quy ước định dạng khi có thể.
- Mỗi tool chỉ đảm nhiệm một hành động nghiệp vụ rõ; tránh quá nhỏ hoặc ôm quá nhiều việc.
- Tool return nên là JSON nhất quán, có `status`, `data` hoặc `message/code`, nguồn và thời gian nếu cần.
- Tool loop phải giới hạn số vòng, xử lý timeout/error, không retry im lặng quá hai lần và không crash.
- Chỉ gọi song song các tool độc lập; nếu tool B cần output của tool A thì phải chạy tuần tự.

## 7. Áp dụng trực tiếp vào Northstar IT Helpdesk Lab 4

Không sửa mất baseline `v0`. Chạy và lưu evidence trước, sau đó cải tiến có kiểm soát:

- `v0`: giữ nguyên starter, chạy baseline và phân loại failure.
- `v1`: làm rõ routing trong `tools.yaml`: chức năng, trigger, điều kiện không dùng, required fields.
- `v2`: sửa system prompt cho thiếu identifier, hội thoại nhiều lượt, correction/cancellation và thứ tự tool.
- `v3`: hoàn thiện confirmation, prompt injection, external-data boundary, error handling và output contract.

Mỗi phiên bản phải có một hypothesis chính, chạy lại cùng suite, lưu run file, metric, failure trace và regression review.

## 8. Những thiếu sót thấy ngay trong starter hiện tại

- `Rules` mới ở mức chung, chưa mô tả decision policy.
- `Capabilities` chỉ nói được dùng tool, chưa nói ranh giới từng tool.
- `Constraints` thiếu quy tắc không đoán ID, không thu secret, confirmation, cancellation, indirect injection và dữ liệu được phép gửi ra ngoài.
- `Output format` có bốn trường nhưng chưa định nghĩa giá trị hợp lệ và cách phản hồi lỗi.
- Nhiều tool description chưa nêu rõ khi nào dùng và khi nào không dùng.
- `create_ticket` chưa diễn đạt đủ explicit confirmation và việc xác nhận cũ mất hiệu lực khi payload thay đổi.

## 9. Sáu câu tự kiểm theo slide của thầy

1. Agent chạy end-to-end mà không crash chưa?
2. System prompt có đủ Persona, Rules, Capabilities, Constraints và Format chưa?
3. Tool schemas có description rõ và required fields đúng chưa?
4. Agent phân biệt đúng lúc trả lời trực tiếp và lúc gọi tool chưa?
5. Tool lỗi có được xử lý và giải thích cho người dùng chưa?
6. Đã ghi ít nhất hai lỗi và phân loại đúng prompt/tool schema/control flow chưa?
