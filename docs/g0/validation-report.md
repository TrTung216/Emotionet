# Kiểm tra kỹ thuật bản nháp G0

Ngày ghi nhận: 15/11/2026. Môi trường: Python 3.11.6 trên Windows.

## Kết quả

`python scripts/validate_g0.py` chạy thành công:

| Loại | Số lượng |
|---|---:|
| Concept | 30 |
| LexicalEntry | 32 |
| LexicalForm | 35 |
| Sense | 34 |
| Relation | 14 |
| Evidence | 44 |
| EmotionAnnotation | 0 |
| Review event | 0 |

Tất cả thực thể là candidate; không có concept approved.
Kiểm tra đạt: trường bắt buộc, ID, tham chiếu, Unicode NFC, chuẩn hóa tra cứu,
canonical form, đa nghĩa mẫu, cạnh trùng, hướng cạnh đối xứng, chu trình phân cấp
và số lượng trong manifest.

Đã thử lỗi bằng cách thay dữ liệu đọc trong bộ nhớ, không sửa file mẫu:

- ID concept trùng: bị phát hiện.
- Sense tham chiếu concept không tồn tại: bị phát hiện.
- normalized_form sai: bị phát hiện.
- Evidence không tồn tại: bị phát hiện.
- Cạnh is_a tạo chu trình: bị phát hiện.

Các kiểm tra bổ sung đạt: cú pháp các file Python, liên kết tài liệu nội bộ,
bản kế hoạch sao chép trùng SHA-256 với file gốc. Chạy lại công cụ tạo mẫu bị
từ chối như thiết kế để bảo vệ dữ liệu đã có.

## Giới hạn

Đây là kiểm tra snapshot mẫu G0, không phải bộ xác thực mọi đầu vào tùy ý.
Chưa triển khai API, SQLite, importer, matcher, kiểm tra lịch sử duyệt hoặc
EmotionAnnotation. Các chức năng đó cần kiểm thử riêng tại giai đoạn triển khai.

Chưa đo precision/recall/F1; chưa kiểm duyệt ngữ nghĩa độc lập hoặc xác nhận
quyền phân phối. Kết quả kỹ thuật này không làm G0 chuyển sang hoàn thành.
