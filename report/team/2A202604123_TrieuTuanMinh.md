# Báo cáo cá nhân — Triệu Tuấn Minh (2A202604123)

## 1. Thông tin thành viên

- Họ tên: Triệu Tuấn Minh
- MSSV: 2A202604123
- Email: trieutuanminh004@gmail.com

## 2. Phần việc phụ trách

- Phát triển và kiểm thử UI Streamlit cho Research Agent.
- Triển khai, kiểm tra giao diện dùng thử trên Streamlit Cloud.
- Chạy live chat trên UI và kiểm tra transcript được lưu.
- Chạy test và rà soát các bằng chứng cần thiết trước khi nộp.

## 3. Đóng góp cụ thể

- Phát triển/chỉnh sửa giao diện Streamlit tại `starter_v0/app.py`, kết nối UI với luồng chạy agent và hiển thị kết quả tool.
- Cập nhật dependency Streamlit trong `starter_v0/requirements.txt`; kiểm tra môi trường Python, lệnh chạy UI và xử lý vấn đề khi cổng mặc định 8501 đã được sử dụng.
- Triển khai và xác minh UI trên Streamlit Cloud để các thành viên có thể truy cập dùng thử.
- Thực hiện live chat qua UI và lưu transcript trong `starter_v0/transcripts/`; transcript UI có tên theo mẫu `ui_mistral_*`. CLI chat 4 lượt do Đạt thực hiện, không tính là lượt chat cá nhân của tôi.
- Chạy kiểm thử và rà soát bằng chứng theo checklist: `pytest` có 115 test passed, 0 failed; có 6 run chính hợp lệ với `provider_error_cases=0` và `measured_cases=total_cases`.
- Tổng hợp các đóng góp và bằng chứng vào báo cáo cá nhân này.

## 4. Bằng chứng

- File và kết quả tham chiếu:
  - `starter_v0/app.py` — mã UI Streamlit.
  - `starter_v0/requirements.txt` — khai báo dependency cho UI.
  - `starter_v0/transcripts/ui_mistral_*.transcript.json` — transcript live chat từ UI.
  - `starter_v0/chat.py` — luồng chat CLI và lưu transcript.
  - `starter_v0/runs/` và `starter_v0/artifacts/version_log.csv` — kết quả eval và versioning.
  - Kết quả kiểm thử: `pytest`, 115 passed / 0 failed.
  - UI dùng thử trên Streamlit Cloud: [Mở Research Agent](https://k5-l3b-day03-nhom0-researchagenttooleval-e3h7zcwy24sllsjwahcte.streamlit.app/).
- AI/công cụ đã dùng và cách tự kiểm tra kết quả:
  - Dùng trợ lý AI để hỗ trợ rà soát cấu trúc UI và kiểm tra lỗi khi chạy ứng dụng.
  - Tự kiểm tra UI local và link Streamlit Cloud; xác nhận transcript UI được lưu, pytest chạy xanh, và các run được dùng làm bằng chứng không có provider error, đo đủ số case.

## 5. Tự đánh giá

- Tôi hoàn thành các phần việc được giao về UI Streamlit, triển khai demo, live chat, transcript và kiểm thử. Các kết quả có thể đối chiếu qua mã nguồn, transcript, log test và link dùng thử nêu ở trên.
- Qua nhiệm vụ này, tôi cải thiện kỹ năng tích hợp giao diện với agent, kiểm tra môi trường chạy và thu thập bằng chứng để đánh giá hệ thống.
- Nếu tiếp tục phát triển, tôi sẽ bổ sung kiểm thử tự động cho luồng UI và theo dõi lỗi của bản deploy để việc demo ổn định hơn.
