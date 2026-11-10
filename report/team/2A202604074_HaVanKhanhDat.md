# Báo cáo cá nhân — Hà Văn Khánh Đạt — 2A202604074

## 1. Thông tin thành viên

- Họ tên: Hà Văn Khánh Đạt
- MSSV: 2A202604074
- Email: hagamer2004@gmail.com
- GitHub: hadatttt
- Vai trò: **Eval & Report** (xem [TEAM.md](../../TEAM.md))

## 2. Phần việc phụ trách

- Tạo repo nhóm, setup môi trường chạy (venv, `.env`, preflight provider).
- Viết 10 eval case nhóm trong `starter_v0/data/eval_group.json` (5 single turn + 5 multi turn, ≥ 1 case route tới tool mới).
- Chạy suite group bằng `run_eval.py` và lưu run JSON.
- Viết báo cáo nhóm `report/team/group_report.md`: Phần A (giới thiệu agent) và Phần B (bằng chứng v0–v3, failure analysis, reflection).

## 3. Đóng góp cụ thể

**Setup và thử provider**

- Clone repo, tạo `.venv`, cài `requirements.txt`, tạo `.env`; `pytest` ban đầu 62 passed / 17 skipped.
- Kiểm tra từng API key bằng cách gọi thật từng tool: `lookup` (Tavily), `fetch` (Firecrawl), `social_search` (RapidAPI) đều trả kết quả.
- Chạy baseline đầu tiên bằng Gemini → phát hiện 5/20 case lỗi provider (`503` quá tải, `429` hết quota) nên run không dùng được làm baseline. Đây là một trong các lý do nhóm chuyển sang Mistral.
- Phát hiện và sửa lỗi `.env` (`MISTRAL_API_KEY =` có dấu cách), chạy preflight Mistral pass.

**Eval case nhóm (10/10)**

Thiết kế để **không trùng** với 20 case base mà cover các convention/boundary base chưa đo:

| Case | Lý do thêm |
|---|---|
| G01 handle có `@` | Base chưa test việc bỏ `@` |
| G02 `timeframe=month` | Base chỉ test `day` / `week` |
| G03 `papers` + `sort_by=submittedDate` | Base không chấm argument của `papers` |
| G04 user ép "khỏi cần hỏi lại" | Boundary `send` dưới áp lực — khó hơn R12 |
| G05 đặt vé máy bay | Out-of-scope dạng *hành động*, dễ bị nhầm sang `lookup` |
| G06 xác nhận rồi gửi (multi) | Base chỉ test lượt đầu (`clarify`), chưa test lượt `send(confirmed=true)` |
| G07 `papers` → `paper_text` (multi) | Chuyển tool khi đã có id paper |
| G08 giữ query, đổi Latest → Top (multi) | Carry-over argument của `social_search` |
| G09 từ chối rồi quay lại research (multi) | Agent không được "kẹt" ở chế độ từ chối |

| G10 `timeline` → `wiki` (multi) | Route tới tool mới `wiki` khi lượt 2 hỏi "X là ai" |

Cố ý **không chấm** `query` tiếng Việt ở G09 vì so khớp chính xác dễ chấm sai.

**Phát hiện regression của v4:** chạy đủ 10 case trên v4 ([`runs/v4_B_group_mistral_20261110T182349044706.json`](../../starter_v0/runs/v4_B_group_mistral_20261110T182349044706.json)) được 9/10 — G06 (đã xác nhận → `send`) hỏng. Dùng `scripts/probe_case.py -n 5` so sánh: v3 5/5 PASS, v4 0/5 PASS → lỗi ổn định do rule "mọi yêu cầu gửi → lượt đầu bắt buộc clarify yes_no" của v4. Bộ base vẫn 20/20 nên không thấy; đã ghi vào B1/B3 kèm giả thuyết cho v5 và báo cho người phụ trách prompt.

**Chạy suite group và đối chứng**

- v3: [`runs/v3_B_group_mistral_20261110T175433407926.json`](../../starter_v0/runs/v3_B_group_mistral_20261110T175433407926.json) — 9/9.
- Tự chạy thêm cùng 9 case trên prompt/tools **gốc v0** (lấy từ commit `c68da4c`, truyền qua `--system-prompt` / `--tools`): [`runs/v0_B_group_mistral_20261110T175509644918.json`](../../starter_v0/runs/v0_B_group_mistral_20261110T175509644918.json) — 7/9. Hai case bắt được lỗi của v0: G04 (v0 tự `send` không xác nhận) và G08 (v0 sửa query thành "Claude from Anthropic" + gọi thừa `timeline`). Mục đích: chứng minh bộ case của nhóm thật sự phân biệt được bản tốt và bản xấu, không phải case dễ.

**Bonus — Test challenge (0 skipped)**

- Viết thật 14 test stub cho tool có sẵn trong [`tests/test_tools_todo.py`](../../starter_v0/tests/test_tools_todo.py): `clarify` (1), `format` (3), `send` (2), `lookup` (1), `fetch` (2), `timeline` (1), `social_search` (1), `policy` (3).
- `pytest`: 72 passed / 14 skipped → **86 passed, 0 skipped, 0 failed**. Toàn bộ offline bằng `fake_http` và `monkeypatch`.
- Không tìm thấy bug trong tool có sẵn; các test khoá lại guardrail quan trọng: `send` thiếu env không gửi request, dòng giống lệnh trong policy bị tách vào `untrusted_text`.

**Báo cáo nhóm**

- Phần A: mô tả agent, bảng 11 tool (gồm tool mới `wiki`), 5 câu hỏi mẫu kèm tool kỳ vọng.
- Phần B: mục 3 (giải pháp v1–v4, đọc diff commit `842e7d1`, `760bcf2`), B1 (version evidence v0–v4 + bảng metric chi tiết + regression G06), B2 (failure analysis lấy từ `actual_tool_calls`), B3 (bảng 10 case với kết quả v0/v3/v4), B5a (tool mới + unit test), B5 (test challenge), mục 5 (khó khăn), mục 7 (reflection), mục 8 (tài liệu tham khảo).
- Phát hiện hash artifact trên máy Windows khác hash trong `version_log.csv` → kiểm tra và xác nhận là do CRLF (`core.autocrlf=true`), nội dung giống hệt v3; ghi vào mục 5.

## 4. Bằng chứng

- File:
  - [`starter_v0/data/eval_group.json`](../../starter_v0/data/eval_group.json)
  - [`starter_v0/runs/v3_B_group_mistral_20261110T175433407926.json`](../../starter_v0/runs/v3_B_group_mistral_20261110T175433407926.json)
  - [`starter_v0/runs/v0_B_group_mistral_20261110T175509644918.json`](../../starter_v0/runs/v0_B_group_mistral_20261110T175509644918.json)
  - [`starter_v0/runs/v0_B_base_gemini_20261110T173540507369.json`](../../starter_v0/runs/v0_B_base_gemini_20261110T173540507369.json) (bằng chứng lỗi provider Gemini)
  - [`report/team/group_report.md`](group_report.md)
- Commit: _(điền hash sau khi push)_
- AI/công cụ đã dùng và cách tự kiểm tra kết quả:
  - Dùng **Claude Code** để đọc repo, chạy lệnh, soạn nháp eval case và các mục báo cáo.
  - Tự kiểm tra: mọi số liệu trong báo cáo đều đối chiếu lại với `summary` và `results[*].result` trong run JSON thật (không chép từ trí nhớ); eval case được kiểm tra bằng `pytest` (contract test giữa `tools.yaml` ↔ code ↔ eval) và bằng run thật trên Mistral; chạy thêm đối chứng v0 để chắc case không quá dễ.

## 5. Tự đánh giá

- **Làm tốt:** eval case có chủ đích (mỗi case lấp một khoảng trống của bộ base) và có đối chứng v0 vs v3 làm bằng chứng; báo cáo bám sát log thật, chỉ ra được việc metric v0 = v1 nhưng thành phần lỗi khác nhau hoàn toàn.
- **Chưa xong:** B4 (live chat) và phần UI của B5a chờ transcript và UI của Triệu Tuấn Minh.
- **Học được:** nhìn metric tổng là không đủ — phải đọc `actual_tool_calls` mới biết prompt đang sai theo hướng nào (đoán bừa hay hỏi quá tay). Và cần chọn provider ổn định trước khi đo, vì lỗi `503` / `429` làm hỏng cả một lần baseline.
