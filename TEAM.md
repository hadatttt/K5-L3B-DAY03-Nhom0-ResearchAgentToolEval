# Team

## Thông tin nhóm

- Tên nhóm: Nhom0
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY03-Nhom0-ResearchAgentToolEval`
- URL repo: https://github.com/hadatttt/K5-L3B-DAY03-Nhom0-ResearchAgentToolEval
- Nhánh nộp: `main`
- Commit chốt: _(điền hash commit cuối cùng trước khi nộp)_
- Link UI dùng thử: https://k5-l3b-day03-nhom0-researchagenttooleval-e3h7zcwv24sllsjwahcte.streamlit.app/
- Provider dùng: Mistral (`mistral-small-latest`, La Plateforme free tier) — adapter tự viết `providers/mistral_provider.py`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Hà Văn Khánh Đạt | 2A202604074 | hagamer2004@gmail.com | hadatttt | Viết 10 eval case nhóm (`eval_group.json`) + chạy suite group + báo cáo nhóm Phần A/B |
|   2 | Triệu Tuấn Minh | 2A202604123 | trieutuanminh004@gmail.com | ttm4623 | UI (Streamlit) + deploy link dùng thử + demo + transcript chat live |
|   3 | Nguyễn Văn Minh | 2A202604117 | vm140205@gmail.com | vm140205-collab | Tool mới + unit test + đăng ký tool + giữ pytest xanh; baseline + tối ưu v0–v3 cùng agent AI |

## Phân công chi tiết

### Nguyễn Văn Minh (2A202604117) — Tools & Testing
- [x] Setup provider Mistral (adapter `providers/mistral_provider.py`), preflight pass
- [x] Baseline v0 + tối ưu v1, v2, v3 (base eval 20/20) + `version_log.csv`
- [x] Viết tool mới `wiki` (TOOL.md + tool.py + đăng ký `tools/__init__.py` + `tools.yaml`) + v4, v5 (fix G06)
- [x] ≥ 3 unit test cho tool mới trong `tests/test_tools_todo.py` (5 test cho `wiki`)
- [x] Giữ `pytest` xanh (0 failed)
- Ghi chú: các commit của Nguyễn Văn Minh có tác giả git `Nhom0 <nhom0@vinuni.edu>` (vd `842e7d1`, `760bcf2`, `c650993`) — xem báo cáo cá nhân.

### Hà Văn Khánh Đạt (2A202604074) — Eval & Report
- [x] Viết 10 case vào `data/eval_group.json` (5 single turn + 5 multi turn), G10 route tới tool mới `wiki`
- [x] Chạy suite group với `run_eval.py`, lưu run JSON (v4 9/10, v3 9/9, đối chứng v0 7/9) — phát hiện regression G06 ở v4
- [x] Viết `report/team/group_report.md` Phần A (trước 16:30)
- [x] Phần B — mục 3, B1 (v0–v6), B2, B3, B4 (transcript 4 lượt `chat.py`), B5a, B5, 5, 7, 8
- [x] Chạy chat live 4 lượt qua `chat.py` (v6) → `transcripts/v6_mistral_20261110T191842794505.transcript.json`
- [x] Báo cáo cá nhân `report/team/2A202604074_HaVanKhanhDat.md` (bản nháp, cập nhật commit sau khi push)
- [x] Bonus test challenge: viết 14 test stub tool có sẵn → `pytest` 86 passed, 0 skipped
- [x] Bonus hơn 3 tool mới: viết `hackernews`, `github`, `hf_models` (TOOL.md + đăng ký + 13 test + 6 eval case `eval_group_bonus.json`) → v6: base 20/20, group 10/10, bonus 6/6; `pytest` 115 passed, 0 skipped

### Triệu Tuấn Minh (2A202604123) — UI & Demo
- [x] UI Streamlit (`app.py`) chạy được với agent
- [x] Deploy link dùng thử (Streamlit Cloud): https://k5-l3b-day03-nhom0-researchagenttooleval-e3h7zcwv24sllsjwahcte.streamlit.app/
- [x] Chat live ≥ 3 lượt, lưu transcript (UI: `transcripts/ui_mistral_*`; CLI 4 lượt do Đạt chạy)
- [x] Báo cáo cá nhân `report/team/2A202604123_TrieuTuanMinh.md`
- [ ] Tổng kiểm checklist SUBMISSION.md trước khi nộp

## Cá nhân

Mỗi thành viên có báo cáo riêng theo dạng `report/team/MSSV_HoTen.md`:

- `report/team/2A202604074_HaVanKhanhDat.md`
- `report/team/2A202604123_TrieuTuanMinh.md`
- `report/team/2A202604117_NguyenVanMinh.md`
