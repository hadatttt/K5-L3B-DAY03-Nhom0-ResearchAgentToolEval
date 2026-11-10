---
name: github
track: bonus
kind: live_api
provider: GitHub REST search API (keyless, ~10 request/phút)
requires_env: []
inputs: [query, sort, language, max_results]
outputs: [items, item_count]
side_effect: false
---
# github

Tìm **repository open-source trên GitHub** theo từ khóa, sắp theo số sao hoặc mới cập nhật.
Dùng GitHub REST search API không cần token (giới hạn khoảng 10 request/phút cho mỗi IP).

- Dùng khi: "repo GitHub về X", "thư viện / framework / project open-source cho X",
  "code mẫu cho X", "repo nhiều sao nhất về X".
- KHÔNG dùng khi: paper (→ `papers`), model đã huấn luyện (→ `hf_models`), tin tức (→ `lookup`),
  user đưa sẵn một URL github cụ thể cần đọc (→ `fetch`).

Args:
- `query`: từ khóa, ví dụ "llm agent framework".
- `sort`: `stars` (mặc định, nhiều sao nhất) hoặc `updated` (mới cập nhật gần đây).
- `language`: tuỳ chọn, ngôn ngữ lập trình (vd "Python"); được thêm vào query dạng `language:Python`.
- `max_results`: số repo, mặc định 5, tối đa 20.

Output: `items` gồm `title` (owner/repo), `url`, `source`, `summary` (mô tả repo), `stars`,
`language`, `date` (lần cập nhật cuối); và `item_count`.

Ghi chú implement: input xấu không raise mà trả error dict (`{"tool": "github_repo_search", ...}`);
`query` rỗng thì không gọi mạng; `sort` ngoài enum trả lỗi; `max_results` được kẹp về [1, 20].
Lỗi HTTP (vd 403 khi vượt rate limit) trả error dict.
