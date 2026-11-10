# Báo cáo cá nhân — Nguyễn Văn Minh — 2A202604117

## 1. Thông tin thành viên

- Họ tên: Nguyễn Văn Minh
- MSSV: 2A202604117
- Email: vm140205@gmail.com
- GitHub: vm140205-collab
- Vai trò: **Tools & Testing** (xem [TEAM.md](../../TEAM.md))

## 2. Phần việc phụ trách

- Setup provider chạy thật (Mistral — không có sẵn trong starter, phải tự viết adapter).
- Chạy baseline `v0` và tối ưu `v1`, `v2`, `v3` theo vòng lặp evidence-driven; ghi `artifacts/version_log.csv`.
- Viết tool mới `wiki` (code + `TOOL.md` + đăng ký + ≥ 3 unit test).
- Giữ `pytest` xanh (0 failed) sau mỗi thay đổi.
- Sửa regression G06 ở `v5` (phát hiện bởi bộ eval group của Hà Văn Khánh Đạt).

## 3. Đóng góp cụ thể

**Setup provider Mistral**

- Starter không có provider Mistral. Viết [`providers/mistral_provider.py`](../../starter_v0/providers/mistral_provider.py) — API La Plateforme tương thích OpenAI nên tái dùng openai SDK, parse `tool_calls` và giữ nguyên JSON lỗi (`_invalid_json_arguments`) đúng như provider khác để eval chấm thay vì ẩn thành provider_error.
- Đăng ký ở `providers/__init__.py`, `run_eval.py`, `chat.py`, `scripts/preflight_provider.py`. Preflight pass: chọn đúng `timeline(sama, limit=1)`.

**Baseline v0 và phân tích**

- v0 = 14/20 (0.70): [`runs/v0_B_base_mistral_20261110T172130331004.json`](../../starter_v0/runs/v0_B_base_mistral_20261110T172130331004.json).
- Đọc `actual_tool_calls` của 6 case FAIL: tất cả đều do **chỉ dẫn xấu cố ý trong starter prompt** (đoán thay vì hỏi: `timeline(sama)` khi thiếu handle, `fetch(arxiv.org)` khi thiếu URL; gửi Telegram không xác nhận; gọi `timeline(elonmusk)` thay vì `social_search` khi chỉ có từ khóa).

**Tối ưu v1 → v3 (mỗi version một giả thuyết)**

- **v1** (giả thuyết: chỉ dẫn xấu gây lỗi đoán/hỏi thiếu): viết lại `system_prompt.md` — bỏ đoán bừa, thêm rule clarify/confirm. Kết quả 14/20 nhưng **tập lỗi đổi hoàn toàn**: sửa được 5 case (R03, R10, R11, R13, M02), hỏng 4 case mới (R01, R04, R07, M06) vì model clarify quá tay — hỏi lại cả khi thông tin đã đủ.
- **v2** (giả thuyết: v1 không phân biệt "thiếu info bắt buộc" vs "đủ info"): thêm danh sách "Do NOT clarify when…", convention `response_type` của `clarify`, giới hạn parallel calls chỉ khi user yêu cầu nhiều nguồn. Kết quả **20/20**.
- **v3** (giả thuyết: description mơ hồ là gốc lỗi routing/args): viết lại description toàn bộ tool trong `tools.yaml` (làm gì / khi nào dùng / khi nào không + convention args). Contract test bắt 1 lỗi của chính tôi: khai báo param `paper_text` lệch signature hàm (`url`/`top_k` thay vì `arxiv_url`/`max_pages`/`max_chars`) — sửa theo. Kết quả 20/20 sau khi ép `clarify` dùng `yes_no` cho yêu cầu send.

**Tool mới `wiki` (CP3)**

- [`tools/wiki/tool.py`](../../starter_v0/tools/wiki/tool.py): tra Wikipedia qua MediaWiki API **keyless** — phù hợp demo vì nhóm thiếu key Firecrawl/RapidAPI. Input xấu trả error dict thay vì raise; `max_results` sai kiểu/< 1 về mặc định 3, > 10 kẹp về 10; `lang` normalize rồi mới kiểm tra enum {vi, en}.
- Bắt được 2 bug thật khi chạy live: Wikipedia **403** do chặn User-Agent mặc định của python-requests → thêm UA mô tả.
- 5 unit test trong [`tests/test_tools_todo.py`](../../starter_v0/tests/test_tools_todo.py): happy path (assert cả request gửi đi lẫn kết quả map), query rỗng/sai kiểu không gọi mạng, `lang` ngoài enum, kẹp `max_results` (kể cả số dạng chuỗi `"5"`), HTTP 500 trả error dict.

**Khám phá về model nhỏ — probe 1 case thay vì chạy cả suite**

- Sau khi thêm `wiki`, R12 fail lặp lại. Sau 2 lần sửa rule text không ăn, viết [`scripts/probe_case.py`](../../starter_v0/scripts/probe_case.py) — chạy **1 case qua đúng pipeline chấm của eval** (~5s thay vì ~10 phút cả suite). Probe chỉ ra sai không phải "model thiếu thông tin" mà là **nondeterminism của mistral-small** (2 mode: trả text thường không gọi tool; repetition loop sinh hàng trăm tool call lặp).
- 3 phát hiện có bằng chứng:
  1. **Model nhỏ theo few-shot tốt hơn theo rule** — thêm 4 ví dụ vào prompt → R12 8/8 (trước đó rule "PHẢI gọi tool" chỉ đạt ~4/6).
  2. **Câu ép "never plain text" tự gây repetition loop** (M06 1/4 → đổi thành "một tool call mỗi request, sau đó tóm tắt bằng text" → 4/4). Bài học: rule quá cứng tạo hành vi trốn thoát khác tệ hơn.
  3. **Negative example ("WRONG: …") làm model né luôn cả tool đúng** (R12 tụt 4/8) — phải bỏ.
- v4 chốt: base 20/20 [`runs/v4_B_base_mistral_20261110T182018442733.json`](../../starter_v0/runs/v4_B_base_mistral_20261110T182018442733.json).

**Sửa regression G06 ở v5**

- Đạt probe G06 (đã xác nhận ở lượt 2 → phải `send(confirmed=true)`): v3 5/5, v4 0/5 — do rule v4 "first response MUST clarify yes_no" bị model áp cho cả lượt xác nhận. Bộ base không bắt được vì chỉ test lượt đầu.
- Sửa: đổi rule send thành **phụ thuộc trạng thái** (chưa xác nhận → clarify yes_no; lượt mới nhất LÀ xác nhận → send ngay) + few-shot multi-turn confirm-then-send, viết cùng logic vào description `send` trong `tools.yaml`.
- Bằng chứng: G06 5/5, không phá boundary (R12 5/5, G04 3/3, M06 3/3); base 20/20 + group 10/10: [`runs/v5_B_base_mistral_20261110T183443778073.json`](../../starter_v0/runs/v5_B_base_mistral_20261110T183443778073.json), [`runs/v5_B_group_mistral_20261110T183520849576.json`](../../starter_v0/runs/v5_B_group_mistral_20261110T183520849576.json).

## 4. Bằng chứng

- File:
  - [`starter_v0/providers/mistral_provider.py`](../../starter_v0/providers/mistral_provider.py)
  - [`starter_v0/artifacts/system_prompt.md`](../../starter_v0/artifacts/system_prompt.md), [`starter_v0/artifacts/tools.yaml`](../../starter_v0/artifacts/tools.yaml), [`starter_v0/artifacts/version_log.csv`](../../starter_v0/artifacts/version_log.csv) (v0→v5, mỗi dòng một giả thuyết)
  - [`starter_v0/tools/wiki/`](../../starter_v0/tools/wiki) (tool mới), [`starter_v0/scripts/probe_case.py`](../../starter_v0/scripts/probe_case.py)
  - Run JSON: v0 → v5 trong [`starter_v0/runs/`](../../starter_v0/runs) (kèm 4 run trung gian 19/20 của v4 — bằng chứng quá trình đo lặp)
- Commit: `842e7d1` (setup Mistral + v0–v3), `760bcf2` (tool wiki + v4), `c650993` (v5 fix G06)
- AI/công cụ đã dùng và cách tự kiểm tra kết quả:
  - Dùng **trợ lý AI coding agent (pi)** để đọc starter, chạy lệnh, viết code/test và phân tích run JSON; mình là người ra quyết định từng bước (chọn hướng sửa, duyệt từng thay đổi) và là người chạy/kiểm tra kết quả cuối.
  - Tự kiểm tra: mọi metric trích từ `summary` trong run JSON thật, không tự ghi từ trí nhớ; mọi giả thuyết đều đo lại bằng run thật (probe `-n` nhiều lần để loại nhiễu nondeterminism); tool mới được test bằng `pytest` offline (86 passed, 0 skipped, 0 failed) **và** chạy live một lượt trước khi tính là xong; contract test giữ `tools.yaml` ↔ code ↔ eval đồng bộ mỗi lần sửa.

## 5. Tự đánh giá

- **Làm tốt:** mỗi version đúng một giả thuyết và đều có số before/after trong `version_log.csv`; không blind-retry — khi 2 lần sửa cùng một giả định fail, viết probe để đo trực tiếp hiện tượng (nondeterminism) rồi mới đổi hướng (rule → few-shot); tool mới có guardrail input xấu và được test cả 3 lớp (unit test offline, live API, eval routing G10).
- **Chưa xong:** chưa làm bonus Small Local Model (B7) và chưa test `wiki` với tiếng Anh nhiều hơn vài query.
- **Học được:** metric tổng không nói lên phần "thành phần lỗi" (v0 = v1 = 0.70 nhưng lỗi khác hẳn nhau); rule càng cứng càng dễ tạo hành vi trốn thoát ở model nhỏ — few-shot và rule theo **trạng thái** (state machine) ổn định hơn; và eval do nhóm tự viết có giá trị thật: G06 bắt được regression mà bộ base 20/20 không thấy.
