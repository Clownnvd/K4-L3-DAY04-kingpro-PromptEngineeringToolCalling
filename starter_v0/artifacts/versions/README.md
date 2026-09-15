# Artifact versions

- `v0`: starter nguyên bản, dùng làm baseline.
- `v1`: chỉ sửa system prompt cho routing, missing information và context.
- `v2`: giữ prompt v1, chỉ sửa tool descriptions/schema.
- `v3`: giữ tools v2, hoàn thiện prompt về confirmation, injection, privacy và output contract.
- `v4`: giữ nguyên prompt v3, chỉ thêm `check_public_status` gọi live API chính thức không cần khóa.

Không sửa các snapshot sau khi đã chạy. `artifacts/system_prompt.md` giữ prompt v3; `artifacts/tools.yaml` là tools v4 dùng cho demo/UI.
