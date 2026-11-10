---
name: wiki
track: bonus
kind: live_api
provider: Wikimedia (MediaWiki API, keyless)
requires_env: []
inputs: [query, lang, max_results]
outputs: [items, item_count]
side_effect: false
---
# wiki

Tra cứu **Wikipedia** theo từ khóa (MediaWiki search API, không cần API key).

- Dùng khi: user hỏi kiến thức nền / định nghĩa / tiểu sử — "X là ai?", "X là gì?",
  "giải thích khái niệm X", "tìm hiểu về X".
- KHÔNG dùng khi: tin tức / sự kiện đang diễn ra (→ `lookup` topic=news),
  paper học thuật (→ `papers`), tweet/bài đăng (→ `social_search`/`timeline`),
  đọc một URL cụ thể (→ `fetch`), quy định nội bộ (→ `policy`).

Args:
- `query`: từ khóa tra cứu, ví dụ "VinUni" hoặc "transformer".
- `lang`: `vi` (mặc định) hoặc `en` — ngôn ngữ Wikipedia.
- `max_results`: số bài trả về, mặc định 3, tối đa 10.

Output: danh sách `items` với `title`, `url`, `source`, `summary` (đoạn snippet đã
bỏ thẻ HTML), và `item_count`.

Ghi chú implement: input xấu không raise mà trả error dict (`{"tool": "wiki_search",
"error": ..., "message": ...}`); `max_results` sai kiểu hoặc < 1 thì về mặc định 3,
> 10 thì giới hạn về 10; `lang` tự normalize (trim + lowercase) trước khi kiểm tra
enum {vi, en}.
