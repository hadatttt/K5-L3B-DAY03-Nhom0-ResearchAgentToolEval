---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News (Algolia HN Search API, keyless)
requires_env: []
inputs: [query, sort, max_results]
outputs: [items, item_count]
side_effect: false
---
# hackernews

Tìm **story trên Hacker News** theo từ khóa — nơi cộng đồng kỹ sư/startup thảo luận công nghệ.
Dùng Algolia HN Search API công khai, không cần API key.

- Dùng khi: user hỏi cộng đồng dev/kỹ sư bàn gì, "trên Hacker News", "HN", "dân kỹ thuật nghĩ gì về X",
  "thread thảo luận về X".
- KHÔNG dùng khi: tin tức báo chí chung (→ `lookup` topic=news), tweet/bài đăng mạng xã hội
  (→ `social_search` / `timeline`), paper (→ `papers`), repo code (→ `github`).

Args:
- `query`: từ khóa chủ đề, ví dụ "LLM agents", "Rust".
- `sort`: `relevance` (mặc định, liên quan nhất) hoặc `date` (mới nhất — "mới đăng", "gần đây nhất").
- `max_results`: số story, mặc định 5, tối đa 20.

Output: `items` gồm `title`, `url` (link bài gốc; Ask/Show HN không có link ngoài thì dùng link thread),
`source`, `summary` (points / comments / author), `discussion_url`, `date`, `points`, `num_comments`;
và `item_count`.

Ghi chú implement: input xấu không raise mà trả error dict (`{"tool": "hackernews_search", "error": ..., "message": ...}`);
`query` rỗng thì không gọi mạng; `sort` tự normalize (trim + lowercase) rồi kiểm tra enum;
`max_results` sai kiểu hoặc < 1 về mặc định 5, > 20 giới hạn về 20. Gửi User-Agent mô tả.
