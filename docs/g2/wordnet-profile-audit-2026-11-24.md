# Đối chiếu đặc tả WordNet và 29 quyết định quan hệ

Ngày **24/11/2026**. Đã tiếp nhận đặc tả và 29 dòng quan hệ mới tại
[g2-wordnet-review-v1](../../data/local/g2-wordnet-review-v1/).
Phiếu biên soạn quan hệ đã đủ quyết định; **G2a chưa đủ điều kiện nghiệm thu**
vì đặc tả còn mâu thuẫn và migration dữ liệu/API chưa được thực hiện.

## Kết quả xác minh trực tiếp

| Hạng mục | Kết quả |
|---|---|
| Hai CSV quan hệ người dùng cập nhật | Khớp byte; giữ đúng ID và cột nguồn của phiếu gốc |
| Quyết định | 27 accept, 2 revise; predicate đề nghị gồm 26 related_to và 3 antonym_of |
| Định nghĩa từ đích | 29 dòng đã có định nghĩa, tương ứng **24 nhóm từ–định nghĩa**, không phải 29 concept khác nhau |
| ID nghĩa đích | 28 dòng trống; một dòng ghi syn_tui_than nhưng ID này chưa tồn tại trong snapshot v2 |
| Từ đích chưa ghi ID | 28 dòng tương ứng **23 hình thức từ khác nhau**; số synset cuối phải qua kiểm tra nghĩa/POS |
| Evidence của quan hệ | 29 ô relation_evidence_locators vẫn trống; quyết định/rationale nguồn đã được lưu để làm evidence review khi migration |
| Snapshot hiện có | Vẫn 66 synset, 82 sense; tủi thân còn trong nhóm buồn; chưa thêm sense nể ở nghĩa kiêng nể vào snapshot v2 |
| POS dữ liệu | Cả 77 entry trong snapshot v2 còn pos=null; POS trong tài liệu mới là đề xuất biên soạn |
| Core G1 | Bảng relations trỏ FK đến concepts; chưa có nơi lưu cạnh sense-to-sense |
| Test chạy lại | **74/74 đạt, 0 skip** trước khi thêm script audit; chưa kiểm chứng migration WordNet chưa được viết |

Các từ đích lặp gồm đau xót, xót xa, tội nghiệp, ác độc và khinh. Không cấp ID
concept mới theo từng dòng quan hệ. Bảng
[target-definition-groups.csv](../../data/local/g2-wordnet-review-v1/target-definition-groups.csv)
đã gom các dòng có cùng từ/định nghĩa để hỗ trợ biên soạn; bảng này không tự
duyệt synset hoặc giải quyết đa nghĩa.

## Những điểm cần sửa trong đặc tả trước khi nhập graph

### 1. Thống nhất chiều phân cấp

Sơ đồ hiện ghi cha → con với nhãn chung `is_a / hypernym_of`, trong khi API và
pilot sử dụng is_a theo chiều con → cha. Cần chọn chiều lưu chuẩn:

```text
nghĩa hẹp --is_a--> nghĩa rộng
nghĩa rộng --hypernym_of--> nghĩa hẹp   (chiều truy vấn ngược)
```

`is_a` và `hypernym_of` không phải hai tên thay thế cùng chiều. Chỉ lưu một cạnh
chuẩn rồi suy chiều truy vấn, tránh tạo cycle do nhập cả hai hướng như is_a.

### 2. Ba antonym chưa đáp ứng profile vừa đề xuất

| Review ID | Cặp | Vấn đề cần chốt |
|---|---|---|
| g2_rel_7e6b6ca2fa47 | yêu thương — ích kỷ | POS nguồn v/a chưa xác định, đích a; cần chứng minh đối lập giữa đúng hai sense, không chỉ vị tha/vị kỷ |
| g2_rel_0b7cc1161a8f | yêu/thương — ác độc | Bảng ghi nguồn v, đích a, trái ràng buộc cùng POS của profile |
| g2_rel_9d327117f2c6 | thương — ác độc | Cùng lỗi POS; quan tâm người khác và tính cách tàn nhẫn chưa tự chứng minh một cặp trái nghĩa từ vựng |

Cả ba chưa có subject_sense_id/object_sense_id. Quyết định accept được giữ như
đã nộp, nhưng chưa chuyển thành cạnh đã nghiệm thu. Cần chốt hai sense và POS,
hoặc đề xuất lại predicate với lý do; không tự thay ba quyết định này bằng
related_to và cũng không tự đổi POS để làm chúng hợp lệ.

WN-LMF tách quan hệ cấp sense và synset, với bộ loại quan hệ được định nghĩa.
Việc chọn chỉ lưu antonym ở cấp sense là quy ước profile của dự án; tính tương
thích còn cần bảng ánh xạ và kiểm tra định dạng, không được suy từ tên gọi.
[Global WordNet Formats](https://globalwordnet.github.io/schemas/).

### 3. Phân biệt quy tắc dự án với đặc tính chung của WordNet

Giới hạn bốn POS và cách xử lý phân cấp tính từ cần được công bố là profile
của Emotionet. Princeton WordNet tổ chức tính từ qua trái nghĩa/tương tự và
có thể dùng cường độ cảm xúc trong phân biệt cách thức động từ. Vì vậy, quy
tắc không nhận cạnh chỉ dựa trên cường độ là lựa chọn thận trọng của pilot,
không phải bằng chứng rằng WordNet quốc tế cấm mọi phân cấp liên quan cường độ.
[Mô hình quan hệ WordNet](https://wordnet.princeton.edu/).

Chọn một bộ mã POS nội bộ chuẩn và bảng ánh xạ n/v/a/r. `v/a` không phải một
POS đã chốt. Rubric cần nhiều dấu hiệu cú pháp/ngữ nghĩa và ví dụ đối chứng;
không tự quyết định POS chỉ bằng phép kết hợp với “rất” hoặc “nỗi/sự/niềm”.
Tài liệu cũng cần phân biệt lớp động từ nhận thức với hành vi phát ngôn, thay
vì dùng speech-act như tên chung cho mọi động từ được liệt kê.

### 4. Membership và nghĩa của toàn synset

- Định nghĩa gộp “biết ơn” với “lời biểu lộ sự cảm kích” vẫn chứa trạng thái và
  hành vi khác nhau. Cần xử lý bằng các sense có phạm vi rõ; không chỉ nối hai
  nghĩa bằng chữ “và” để kết luận đồng nghĩa. Giữ nguyên quyết định keep lịch
  sử trong khi làm rõ yêu cầu profile mới.
- Cạnh ăn năn → hối hận là cạnh đến **toàn synset**. Nếu giữ tiếc nuối do lỡ cơ
  hội khách quan trong cùng nhóm, không thể nói cạnh chỉ trỏ vào “phần tự trách”
  mà không có ID nghĩa/nhóm riêng cho phần đó.
- Với tủi thân, quyết định người dùng mới là related_to đến buồn. Dòng đặc tả
  ghi thêm “hoặc hyponym_of” phải được chốt riêng trước khi triển khai; không
  tự tạo hai cạnh từ một lựa chọn chưa rõ.
- Nể_s2 cần entry/sense/synset ID, POS đã chốt, evidence và liên kết lịch sử.
  Tên ký hiệu trong tài liệu chưa thay cho các bản ghi JSONL thực tế.

### 5. Quy tắc dùng related_to

Cho phép cross-POS không có nghĩa bất kỳ từ thường đi cạnh nhau đều tạo quan
hệ ngữ nghĩa. Với những cặp như nhận ra–chợt, cần xác định đó là quan hệ biên soạn
được định nghĩa trong profile hay chỉ là đồng xuất hiện/cách kết hợp từ. Từ chối
antonym cũng không bắt buộc phải thêm related_to nếu chưa đủ bằng chứng.

## Tiếp nhận phiên bản mới và bảo toàn lịch sử

File relation-review.csv trong g2-review-reconciled-v1 đã đổi sau lần lập
manifest trước, nên hash không còn khớp; manifest source của lần tiếp nhận cũ
cũng không còn mô tả CSV mới tại thư mục submitted. Đây là thay đổi sau tiếp
nhận, không sửa lại hash cũ để che lịch sử.

Lần này lưu riêng đặc tả, hai CSV mới, manifest cũ, code core đang kiểm tra và
snapshot tham chiếu dưới inputs/ của g2-wordnet-review-v1. Manifest mới ghi
hash theo nội dung thực nhận; 29 quyết định được lưu trong
[received-relation-decisions.jsonl](../../data/local/g2-wordnet-review-v1/received-relation-decisions.jsonl).
Lần nộp tiếp theo dùng thư mục phiên bản mới thay vì chỉnh sửa tiếp bản đã nhận.

## Bước tiếp theo

1. Chốt các mâu thuẫn trong profile: chiều cạnh, mã POS, ba antonym và các nhóm
   nghĩa không tương đương; giữ riêng lịch sử quyết định đã nộp.
2. Tạo bảng POS theo entry/sense/synset và bảng mục từ đích sau khi loại trùng,
   có evidence và quyết định mới khi cần.
3. Triển khai schema quan hệ hai cấp và validator tương ứng; kiểm thử cạnh
   sai cấp, khác POS, ID chưa tồn tại và cycle.
4. Tạo snapshot phiên bản mới: áp dụng hai thay đổi membership, cấp ID có
   mapping, bổ sung nghĩa đích và chỉ nhập các quan hệ đã đáp ứng profile.

Trạng thái hiện tại: **đã hoàn thành lượt điền 29 phiếu quan hệ và có bản thảo
profile; đang hoàn thiện đặc tả và dữ liệu G2a/G2b**. Chưa kết luận đã chuẩn hóa
xong WordNet hay sẵn sàng nhập toàn bộ các cạnh vào Core G1.
