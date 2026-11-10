# Team

## Thông tin nhóm

- Tên nhóm: Nhom0
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY03-Nhom0-ResearchAgentToolEval`
- URL repo: https://github.com/hadatttt/K5-L3B-DAY03-Nhom0-ResearchAgentToolEval
- Nhánh nộp: `main`
- Provider dùng: Mistral (`mistral-small-latest`, La Plateforme free tier) — adapter tự viết `providers/mistral_provider.py`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Hà Văn Khánh Đạt | 2A202604074 |  | hadatttt | UI (Streamlit) + deploy link dùng thử + demo + transcript chat live |
|   2 | Triệu Tuấn Minh | 2A202604123 |  |  | Viết 10 eval case nhóm (`eval_group.json`) + chạy suite group + báo cáo nhóm Phần A/B |
|   3 | Nguyễn Văn Minh | 2A202604117 |  |  | Tool mới + unit test + đăng ký tool + giữ pytest xanh; baseline + tối ưu v0–v3 cùng agent AI |

## Phân công chi tiết

### Nguyễn Văn Minh (2A202604117) — Tools & Testing
- [x] Setup provider Mistral (adapter `providers/mistral_provider.py`), preflight pass
- [x] Baseline v0 + tối ưu v1, v2, v3 (base eval 20/20) + `version_log.csv`
- [ ] Viết tool mới (TOOL.md + tool.py + đăng ký `tools/__init__.py` + `tools.yaml`)
- [ ] ≥ 3 unit test cho tool mới trong `tests/test_tools_todo.py`
- [ ] Giữ `pytest` xanh (0 failed)

### Triệu Tuấn Minh (2A202604123) — Eval & Report
- [ ] Viết 10 case vào `data/eval_group.json` (5 single turn + 5 multi turn), ít nhất 1 case route tới tool mới
- [ ] Chạy suite group với `run_eval.py`, lưu run JSON
- [ ] Viết `report/team/group_report.md` Phần A (trước 16:30) + Phần B (bằng chứng v0–v3, failure analysis)
- [ ] Báo cáo cá nhân `report/team/2A202604123_TrieuTuanMinh.md`

### Hà Văn Khánh Đạt (2A202604074) — UI & Demo
- [ ] UI Streamlit (`app.py`) chạy được với agent
- [ ] Deploy link dùng thử (Cloudflare Tunnel / Streamlit Cloud / Vercel)
- [ ] Chat live ≥ 3 lượt qua `chat.py`, lưu transcript
- [ ] Báo cáo cá nhân `report/team/2A202604074_HaVanKhanhDat.md`
- [ ] Tổng kiểm checklist SUBMISSION.md trước khi nộp

## Cá nhân

Mỗi thành viên có báo cáo riêng theo dạng `report/team/MSSV_HoTen.md`:

- `report/team/2A202604074_HaVanKhanhDat.md`
- `report/team/2A202604123_TrieuTuanMinh.md`
- `report/team/2A202604117_NguyenVanMinh.md`
