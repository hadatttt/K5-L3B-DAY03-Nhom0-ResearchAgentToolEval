---
name: hf_models
track: bonus
kind: live_api
provider: Hugging Face Hub public API (keyless)
requires_env: []
inputs: [query, sort, task, max_results]
outputs: [items, item_count]
side_effect: false
---
# hf_models

Tìm **model AI trên Hugging Face Hub** theo từ khóa, sắp theo lượt tải, lượt thích hoặc đang trending.
Dùng API công khai, không cần token.

- Dùng khi: "model nào trên Hugging Face cho X", "checkpoint / pretrained model của X",
  "model X được tải nhiều nhất", "model đang trending".
- KHÔNG dùng khi: paper nghiên cứu (→ `papers`), source code / repo (→ `github`),
  tin tức về công ty AI (→ `lookup`), định nghĩa khái niệm (→ `wiki`).

Args:
- `query`: từ khóa tên model / họ model, ví dụ "qwen", "whisper".
- `sort`: `downloads` (mặc định), `likes`, hoặc `trending`.
- `task`: tuỳ chọn, lọc theo `pipeline_tag` (vd "text-generation", "automatic-speech-recognition").
- `max_results`: số model, mặc định 5, tối đa 20.

Output: `items` gồm `title` (model id), `url`, `source`, `summary` (task · downloads · likes),
`task`, `downloads`, `likes`; và `item_count`.

Ghi chú implement: input xấu không raise mà trả error dict (`{"tool": "hf_model_search", ...}`);
`query` rỗng thì không gọi mạng; `sort` ngoài enum trả lỗi; `max_results` được kẹp về [1, 20];
response không phải list (API đổi format) trả error dict thay vì crash.
