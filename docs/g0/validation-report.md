# Kiểm tra kỹ thuật bản nháp G0

## Nghiệm thu profile cảm xúc — 23/11/2026

- `python scripts/prepare_g0_handoff.py --check`: đạt; 30 nghĩa từ review có sẵn,
  phủ 27 nhãn, đúng source hash và output hash. Không tự tạo review mới.
- Đối chiếu trực tiếp 30 `dataset_id` và text ví dụ với `train.csv`: khớp toàn bộ.
- `python scripts/validate_g0.py`: đạt cho 30 fixture tổng quát candidate cũ;
  kết quả này không nâng trạng thái fixture.
- Toàn bộ unit test: **49/49 đạt, 0 skip**, chạy bằng Python với `src` trong
  đường dẫn import. Bao gồm hai test mới: từ chối sense có gloss khác review gốc;
  từ chối lấy review ngữ cảnh validation làm bằng chứng train.
- Liên kết tài liệu bàn giao và diff whitespace: đạt.
- Chủ dự án chọn giữ quyền chia sẻ hiện tại, chưa cấp thêm giấy phép tái sử dụng.
  Quyết định được lưu ở [g0-handoff.json](../../configs/g0-handoff.json).

G0 hoàn thành theo [đặc tả miền cảm xúc](research-spec-v1.md) và
[biên bản bàn giao](handoff-2026-11-23.md). Đây là nghiệm thu thiết kế; không phải
đánh giá F1, chứng nhận nguồn bên ngoài hoặc hoàn thành G1. Kết quả ngày 15/11
bên dưới được giữ để truy vết fixture ban đầu.

## Lịch sử kiểm tra fixture tổng quát

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
