# Chạy Lab 4 kingpro

## Chạy ngay, không cần API

```powershell
cd "C:\Users\S88 Service\Downloads\K4-Day04-Lab-Starter\starter_v0"
python scripts/validate_submission.py
python run_eval.py --provider offline --version v3 --suite base --eval-cases data/eval_base.json
streamlit run app.py
```

Mở `http://127.0.0.1:8501`. Chế độ offline chỉ kiểm tra UI, local tools và control flow; không dùng làm evidence LLM.

## Sau khi tạo Gemini key

Tạo `starter_v0/.env`:

```text
GEMINI_API_KEY=<key-của-nhóm>
GEMINI_MODEL=gemini-3.7-flash
```

Chạy một lệnh:

```powershell
.\RUN_LAB4_GEMINI.ps1
```

Script chỉ chọn provider `gemini`; không đọc hay sử dụng `OPENAI_API_KEY`. Nó chạy preflight, base v0–v3, group, adversarial, bốn transcript, cập nhật `version_log.csv`, rồi chép evidence cần nộp vào `artifacts/evidence/`.

## Trước khi nộp

1. Điền đúng `TEAMMATES.md`.
2. Đọc run thật và hoàn thiện các ô PENDING trong `artifacts/REPORT.md`.
3. Deploy UI và điền URL.
4. Mỗi thành viên tự commit phần việc/reflection và merge.
5. Quét secret, sau đó mọi người nộp cùng URL repo.
