# Use case và tiêu chí chấp nhận v1 (dự thảo)

**Cập nhật 23/11/2026:** bảng dưới giữ các tình huống tổng quát ban đầu. Use case
nghiệm thu miền cảm xúc R01–R12 nằm tại [đặc tả nghiên cứu v1](research-spec-v1.md).

Người dùng chính: lập trình viên NLP tra cứu tiếng Việt; người biên soạn và
kiểm duyệt dữ liệu. Chưa có màn hình web hoặc xử lý đa người dùng trong MVP.

| ID | Tình huống | Kết quả cần có khi triển khai |
|---|---|---|
| UC01 | Tra `trí tuệ nhân tạo` và `AI` | Cùng concept; giữ surface và form type |
| UC02 | Tra `đường` | Hai sense đường đi/đường ăn; không tự chọn một nghĩa |
| UC03 | Tra `mạng` | Hai concept mạng máy tính/dụng cụ đánh cá |
| UC04 | Tra `đá` | Trả cả entry danh từ và động từ với sense riêng |
| UC05 | Tra `  TRÍ TUỆ   NHÂN TẠO `, bản Unicode NFD | Khớp bản chuẩn NFC, không bỏ dấu |
| UC06 | Match `Tôi học trí tuệ nhân tạo.` | Span đúng chuỗi gốc; ứng viên sense đầy đủ |
| UC07 | Match cụm dài có cụm con trong từ điển | Mặc định leftmost-longest, không chồng lấn; chế độ all trả tất cả |
| UC08 | Match `mai` khi có form `AI` | Không khớp bên trong token |
| UC09 | Truy vấn `học máy` | Có cạnh đi ra subfield_of → trí tuệ nhân tạo nếu đã duyệt |
| UC10 | Thêm A is_a B khi đã có B is_a A | Từ chối và báo đường đi tạo chu trình |
| UC11 | Xuất rồi nhập JSONL | Giữ ID, nguồn, trạng thái, Unicode và quan hệ |
| UC12 | Xuất bản khi còn candidate hoặc license undetermined | Không đưa bản ghi đó vào dữ liệu công bố; báo tham chiếu thiếu |
| UC13 | Tra concept trung tính | Danh sách cảm xúc rỗng; không bịa score |
| UC14 | Không tìm thấy mục từ | Trả danh sách rỗng; get_concept ID không có trả None |

## Hợp đồng Python mục tiêu

Các hàm dưới đây là thiết kế, **chưa được triển khai**:

```python
net = Emotionet.open("data/emotionet.sqlite")
net.lookup("đường")
net.match("Tôi học trí tuệ nhân tạo.", overlap="longest")
net.relations("con_000002", predicate="subfield_of", direction="out")
net.get_concept("con_000001")
net.close()
```

- `lookup`: danh sách entry, mỗi entry chứa forms và toàn bộ senses ứng viên,
  concept và evidence tương ứng. Không sắp hạng nghĩa khi chưa có mô hình.
- `match`: danh sách `{text, start, end, entries}`; end loại trừ, chỉ số ký tự
  Python trên chuỗi gốc, kể cả đầu vào NFD. Phải có ánh xạ vị trí khi chuẩn hóa.
- Chuẩn hóa lookup: NFC → casefold → NFC → gộp khoảng trắng, giữ dấu câu/dấu tiếng Việt.
- Biên token matcher: chữ/số/dấu kết hợp Unicode/underscore là thành phần token;
  không khớp bên trong token, không nối cụm qua dấu câu. Khoảng trắng có thể gộp.
- `overlap="longest"`: chọn vị trí trái nhất rồi cụm dài nhất tại vị trí đó;
  `overlap="all"`: giữ mọi span. Cùng span thì gộp ứng viên, không bỏ nghĩa.
- `relations`: mặc định cạnh đi ra đã lưu; `in` và `both` là lựa chọn tường minh.
- API mặc định chỉ đọc dữ liệu approved với phụ thuộc approved. Chế độ biên soạn
  `include_unapproved=True` phải bật tường minh và luôn trả trạng thái.
- ID lạ không tạo bản ghi mới. Tham số sai và DB sai schema báo lỗi rõ ràng.
- Confidence không được tính thì để `null`; không dùng giá trị giả mặc định.

MVP chưa thực hiện WSD, truy vấn vector, suy luận bắc cầu tự động hoặc thử nghiệm
LSTM/xLSTM. Các chỉ tiêu F1 trong kế hoạch chỉ được báo sau khi có gold set độc lập.
