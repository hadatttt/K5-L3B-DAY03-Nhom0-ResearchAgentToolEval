# Snapshot prompt + tools theo version

Bản lưu `system_prompt.md` + `tools.yaml` của từng version trong `../version_log.csv`, để UI (`app.py`)
cho chọn version và so sánh hành vi. File đang dùng để chạy eval vẫn là `../system_prompt.md` và `../tools.yaml`.

| Version | Nguồn | Hash (khớp `version_log.csv`) |
|---|---|---|
| v0 | commit `c68da4c` (starter gốc) | p `eb1c8179815b` · t `e69bc53ed884` |
| v1 | prompt v1 chưa từng được commit; tái tạo bằng cách đảo ngược 3 edit v1→v2 trên prompt `842e7d1` ([`../../scripts/rebuild_v1_prompt.py`](../../scripts/rebuild_v1_prompt.py), commit `e210d2b`) + tools commit `c68da4c`. sha256 khớp chính xác hash trong log | p `5138c3df1f4b` · t `e69bc53ed884` |
| v2 | prompt commit `842e7d1` + tools commit `c68da4c` | p `c5fc9144fc14` · t `e69bc53ed884` |
| v3 | commit `842e7d1` | p `c5fc9144fc14` · t `d31530f1bcea` |
| v4 | commit `760bcf2` | p `9b250c66219d` · t `14319c9dd933` |
| v5 | commit `c650993` | p `b220796d340b` · t `7a8ef9c2aae3` |
| v6 | bản hiện tại (3 tool bonus) | p `b5a1cd613565` · t `189681c8d038` |

Hash trong log được tính trên file có xuống dòng CRLF (máy Windows) hoặc LF tuỳ người chạy; snapshot đã được
kiểm tra khớp ở một trong hai dạng. Version cũ có thể khai báo tham số không khớp code hiện tại
(vd `paper_text` trước v3) — đó là hành vi thật của version đó.
