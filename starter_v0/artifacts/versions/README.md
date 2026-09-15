# Artifact versions

- `v0`: starter nguyên bản, dùng làm baseline.
- `v1`: chỉ sửa system prompt cho routing, missing information và context.
- `v2`: giữ prompt v1, chỉ sửa tool descriptions/schema.
- `v3`: giữ tools v2, hoàn thiện prompt về confirmation, injection, privacy và output contract.

Không sửa các snapshot sau khi đã chạy. `artifacts/system_prompt.md` và `artifacts/tools.yaml` là bản v3 dùng cho demo/UI.
