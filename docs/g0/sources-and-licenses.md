# Nguồn và giấy phép — quy trình G0

**Cập nhật 23/11/2026:** chủ dự án đã cho phép chia sẻ `data/local/` và push Git
ngày 22/11, lưu tại [quyết định chia sẻ](../../configs/data-sharing.json). Phần
quy trình bên dưới ghi yêu cầu thẩm định nguồn, không hủy quyền chia sẻ đã cấp.
Lựa chọn cấp giấy phép tái sử dụng riêng được trình bày trong [bàn giao G0](handoff-2026-11-23.md).

Registry: `data/licenses/sources.csv`. Mỗi Evidence phải tham chiếu một nguồn
đã đăng ký. Tách quyết định giấy phép của mã nguồn khỏi giấy phép dữ liệu.

## Quy trình trước khi nhập nguồn ngoài

1. Ghi URL tài liệu và URL điều kiện sử dụng cụ thể; lưu ngày truy cập và phiên bản.
2. Xác định nội dung sẽ dùng: định nghĩa, ví dụ, quan hệ hay chỉ phương pháp.
3. Ghi điều kiện cho việc sửa đổi, sử dụng và phân phối; ghi yêu cầu ghi công nếu có.
4. Lưu tài liệu chứng minh quyết định tại `data/licenses/`, liên kết trong notes.
5. Khi chưa xác minh, đặt rights_status=pending, license=undetermined;
   dữ liệu chỉ là ứng viên, không đưa vào bản phát hành.

Nguồn được nhắc trong kế hoạch (WordNet, ConceptNet, OntoLex, VnCoreNLP,
Wikidata...) hiện chỉ là danh sách khảo sát. Chưa lấy dữ liệu hoặc kết luận
quyền sử dụng từ những nguồn này.

## Bộ mẫu hiện tại

`src_g0_draft` là nội dung soạn mới với trợ lý AI phục vụ thử thiết kế, không phải
dữ liệu trích từ từ điển đã kiểm duyệt. Locator dẫn đến chính bản nháp để kiểm
toán cách tạo, **không thay thế nguồn xác minh độc lập**. Người duyệt cần bổ sung
bằng chứng phù hợp và chủ dự án cần quyết định quyền phân phối trước khi approved.

`rights_status` dùng pending, cleared hoặc denied. `allowed_uses` là danh sách
phân cách bằng dấu chấm phẩy; giá trị redistribution chỉ được thêm sau khi xác minh.
Ngày soạn bản nháp ghi trong created_at của bản ghi; retrieved_at để trống vì
không có thao tác thu thập từ nguồn ngoài.

Chưa tạo LICENSE với một giấy phép tự chọn. Quyết định còn mở: giấy phép mã nguồn,
giấy phép dữ liệu tự biên soạn và chính sách tiếp nhận đóng góp.
