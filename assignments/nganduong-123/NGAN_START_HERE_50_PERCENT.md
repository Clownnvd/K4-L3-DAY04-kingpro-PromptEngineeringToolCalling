# START HERE — Phần việc 50% của Dương Thị Ngân

## Repository chung

- Repo private: `https://github.com/Clownnvd/K4-L3-DAY04-kingpro-PromptEngineeringToolCalling.git`
- Branch của Ngân: `contrib/nganduong-123`
- Nhóm: K4-L3-DAY04-kingpro-PromptEngineeringToolCalling, 2 người
- Tỷ lệ dự kiến: Nguyễn Văn Duy 50% · Dương Thị Ngân 50%

## Chia đôi phạm vi

### Nguyễn Văn Duy — 50%

- System prompt và decision policy.
- Baseline `v0`, cải tiến `v1/v3`, version log và base runs.
- Tích hợp provider Gemini, runner cuối, merge và report B1/B2/B7.
- Kiểm tra repo, secret hygiene và nộp bài.

### Dương Thị Ngân — 50%

1. **Tool contracts:** review và hoàn thiện `artifacts/tools.yaml` cho 9 tool.
2. **Team eval:** sở hữu `data/eval_group.json`, đúng 10 case = 5 single + 5 multi.
3. **Safety:** review A03, A05, A06 bằng actual calls/results/filesystem.
4. **UI + transcripts:** kiểm tra `app.py`, tool trace và 4 scenario bắt buộc.
5. **Report:** viết phần B3/B4/B4a/B6 và self-reflection của Ngân.

Các file trong ZIP là **starter candidate** do trưởng nhóm/AI chuẩn bị để tiết kiệm thời gian. Chúng chỉ trở thành contribution của Ngân sau khi Ngân trực tiếp đọc, chạy, sửa có lý do và tự commit.

## Cách đưa ZIP vào branch của Ngân

### 1. Chấp nhận lời mời GitHub

Mở GitHub tài khoản `nganduong-123`, vào Notifications hoặc email và chấp nhận lời mời cộng tác repo `Clownnvd/K4-L3-DAY04-kingpro-PromptEngineeringToolCalling`.

### 2. Clone repo và tạo branch

```powershell
cd "$HOME\Desktop"
git clone https://github.com/Clownnvd/K4-L3-DAY04-kingpro-PromptEngineeringToolCalling.git K4-L3-DAY04-kingpro
cd K4-L3-DAY04-kingpro
git switch -c contrib/nganduong-123
git config user.name "Dương Thị Ngân"
git config user.email "nguyenngan20022003@gmail.com"
```

Kiểm tra:

```powershell
git branch --show-current
git config user.name
git config user.email
```

### 3. Giải nén và chép payload

Giải nén ZIP. Giả sử thư mục giải nén là `K4-L3-DAY04-kingpro-NGAN-50-PERCENT-v1`:

```powershell
Copy-Item -Path "$HOME\Desktop\K4-L3-DAY04-kingpro-NGAN-50-PERCENT-v1\payload\*" `
  -Destination "$HOME\Desktop\K4-L3-DAY04-kingpro" -Recurse -Force
```

Không chép `.env`, key hoặc token.

### 4. Cài và chạy offline

```powershell
cd "$HOME\Desktop\K4-L3-DAY04-kingpro\starter_v0"
python -m pip install -r requirements.txt
python -m compileall -q .
python run_eval.py --provider offline --version ngan-draft --suite group --eval-cases data/eval_group.json
python ..\assignments\nganduong-123\check_delivery.py --allow-placeholders
streamlit run app.py
```

Mở `http://localhost:8501`, thử 4 tình huống:

1. VPN production đang lỗi không?
2. Kiểm tra Wi-Fi trên laptop của tôi.
3. Email production → sửa thành staging.
4. Tạo ticket high cho LT-204 → xác nhận đúng payload.

Offline chỉ kiểm tra code/UI, không ghi là LLM evidence.

## Việc Ngân bắt buộc tự làm

### A. Tool contracts

- Đọc `tools/*/TOOL.md` và `artifacts/tools.yaml`.
- Sửa ít nhất **2 tool descriptions hoặc parameter descriptions** dựa trên điều Ngân thấy chưa rõ.
- Ghi lý do sửa trong `artifacts/ngan_adversarial_review.md`.
- Bảo đảm mỗi description nói: làm gì, khi nào dùng, khi nào không dùng.

### B. Team eval

- Giữ đúng 10 case: 5 single-turn + 5 multi-turn.
- Tự sửa ít nhất **3 case** và điền `metadata.change_by_ngan`.
- Không chép fixed cases hoặc hard-code case IDs vào prompt.
- Chạy offline; khi có Gemini thì chạy lại bằng Gemini.

### C. Safety review

Điền actual evidence cho A03, A05, A06:

- Actual tool calls và arguments.
- Tool results/final response.
- Kiểm tra có ticket file hoặc external payload phát sinh không.
- PASS/FAIL, nguyên nhân và artifact cần sửa.

### D. UI/transcript

- Chạy `app.py` và xác nhận hiện tool name, args, result/error, round/status, artifact version/hash, transcript path.
- Chạy `scripts/run_demo_scenarios.py` để tạo 4 transcript.
- Nếu chỉnh UI, chỉ chỉnh phần hiển thị trace/evidence; không tạo agent loop thứ hai.

### E. Reflection

Tự viết 8–12 câu trong `artifacts/self_reflection_ngan.md`, dẫn file/run/commit thật.

## Kiểm tra hoàn thành

```powershell
cd "$HOME\Desktop\K4-L3-DAY04-kingpro"
python assignments\nganduong-123\check_delivery.py
```

Phải hiện `NGAN DELIVERY PASS`.

## Commit và push

```powershell
git status
git add starter_v0/artifacts/tools.yaml `
        starter_v0/data/eval_group.json `
        starter_v0/app.py `
        starter_v0/.streamlit/config.toml `
        starter_v0/chat.py `
        starter_v0/providers `
        starter_v0/run_eval.py `
        starter_v0/scripts/run_demo_scenarios.py `
        starter_v0/scripts/preflight_provider.py `
        starter_v0/requirements.txt `
        starter_v0/artifacts/ngan_adversarial_review.md `
        starter_v0/artifacts/self_reflection_ngan.md `
        assignments/nganduong-123/check_delivery.py

git commit -m "feat(lab4): complete Ngan tools eval safety and UI"
git push -u origin contrib/nganduong-123
```

Sau khi push, mở GitHub và tạo Pull Request:

- Base: `main`
- Compare: `contrib/nganduong-123`
- Title: `feat(lab4): Ngan tools eval safety and UI`

Trong PR ghi rõ file đã sửa, lệnh đã chạy, kết quả run và giới hạn còn lại.




