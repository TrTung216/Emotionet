# G2 — Bộ rà soát khởi đầu

**Cập nhật mới nhất 24/11/2026:** đã nhận đủ 29 quyết định quan hệ (27 accept,
2 revise) và bản thảo profile WordNet. Bản nhận mới được lưu riêng tại
[g2-wordnet-review-v1](../../data/local/g2-wordnet-review-v1/). Còn ID/POS,
quan hệ sense-level và một số mâu thuẫn trong đặc tả cần xử lý trước khi nhập
snapshot; xem [báo cáo đối chiếu](wordnet-profile-audit-2026-11-24.md).
Các số liệu “29 quan hệ chưa điền” dưới đây là trạng thái của lần nhận trước.

**Đã nhận kết quả ngày 24/11/2026:** 66 synset đã rà (64 keep/2 revise về
membership), pilot đủ 18 quyết định sau xác nhận tên cặp (5 accept/4 revise/9
reject). **29 quan hệ nguồn vẫn chưa điền.** Xem
[biên bản tiếp nhận](review-receipt-2026-11-24.md) và
[bản review đã hợp nhất](../../data/local/g2-review-reconciled-v1/).
Phần hướng dẫn dưới mô tả phiếu gốc; không yêu cầu làm lại các quyết định đã nộp.

**Cập nhật định hướng 24/11/2026:** theo
[kế hoạch WordNet v2](../Ke_hoach_WordNet_cam_xuc_tieng_Viet.md), bước tiếp theo
là chốt POS, loại nghĩa và quan hệ hai cấp trong G2a. Bộ phiếu v1 bên dưới được
giữ nguyên làm đầu vào; phiên bản phiếu mới sẽ bổ sung các trường này và kế
thừa quyết định đã điền theo ID. Chưa dùng 18 cặp is_a để nghiệm thu WordNet
trước khi kiểm tra POS và phạm vi quan hệ.

Chuẩn bị ngày **24/11/2026**, sau bàn giao G1. Thư mục làm việc:
[data/local/g2-review-v1](../../data/local/g2-review-v1/).

Đây là bộ phiếu chờ nhóm duyệt, chưa phải snapshot mới và chưa hoàn thành G2.
Giữ nguyên bản nghĩa của chủ dự án, không thay bằng review của thành viên khác.
Không phát sinh bản ghi approved hoặc cạnh graph mới từ lần chuẩn bị này.

## File cần dùng

| File | Số dòng | Mục đích |
|---|---:|---|
| [synset-review.csv](../../data/local/g2-review-v1/synset-review.csv) | 66 | Rà tính nhất quán của định nghĩa, thành viên và provenance; có cờ phần thiếu metadata/nghĩa mới từ embedding |
| [sense-reference.csv](../../data/local/g2-review-v1/sense-reference.csv) | 82 | Tra gloss, ví dụ, loại ví dụ và evidence của từng sense; bảng tham chiếu, không phải phiếu quyết định |
| [relation-review.csv](../../data/local/g2-review-v1/relation-review.csv) | 29 | Chốt ID đích và quyết định riêng cho 24 related_to, 5 antonym_of |
| [is-a-pilot-review.csv](../../data/local/g2-review-v1/is-a-pilot-review.csv) | 18 | Thử quy tắc hypernym/hyponym trên các nghĩa đang có, gồm cả trường hợp dễ nhầm |
| [manifest.json](../../data/local/g2-review-v1/manifest.json) | — | Hash nguồn, hash ban đầu và số lượng |

CSV dùng UTF-8 BOM để Excel đọc dấu tiếng Việt. Các cột ID nên để kiểu **Text**.
Nếu công cụ hỏi delimiter, chọn dấu phẩy. Dấu chấm phẩy bên trong ô phân tách
danh sách ID/nhãn, không phải dấu phân cột của file.

`references/` chứa bản sao nguyên byte snapshot v2, CSV review ứng viên nguồn,
senses v1 dùng truy vết mapping và quyết định chia sẻ của chủ dự án. Locator có
dạng `references/.../file#record_id`: phần sau `#` là khóa bản ghi để tìm trong
file. Hash tính trên nội dung thực đọc lúc chuẩn bị; không sửa manifest lịch sử
v1 để che việc CSV review đã đổi.

## Thứ tự làm việc

1. Trong `synset-review.csv`, ưu tiên dòng có `embedding_added_members_check_context`
   hoặc `check_all_member_glosses_for_equivalence`. Mở `sense-reference.csv`, lọc
   theo `synset_id` để xem tất cả thành viên. Ví dụ cần chú ý: nghĩa/ví dụ của `nể`,
   `cám ơn`, hoặc mức khái quát của nhóm `buồn/đau lòng/tủi thân`.
2. Duyệt 18 cặp `is_a` để thống nhất tiêu chí loại–cha. Khi một đầu của cạnh đang
   cần sửa/tách nghĩa, để `uncertain` hoặc `revise`; không duyệt cạnh dựa trên một
   thành viên trong khi các thành viên khác không thỏa.
3. Xử lý 29 quan hệ nguồn. **28/29 từ đích chưa có synset khớp bề mặt** trong v2.
   Một từ khớp là `tủi thân`, hiện nằm trong nhóm `buồn`; đó chỉ là gợi ý tra cứu,
   không tự xác nhận quan hệ với toàn nhóm. Với từ chưa khớp bề mặt, tra nghĩa
   trong toàn bộ 66 synset trước; có thể nghĩa đã tồn tại dưới một lemma khác.
   Chỉ đề nghị tạo/duyệt concept đích mới khi chưa có nghĩa tương đương.
4. Trả các phiếu đã điền. Bước sau sẽ kiểm tra quyết định, bổ sung evidence review,
   tạo snapshot phiên bản mới và kiểm thử bằng G1. Không chạy lại builder v2 cũ
   để áp dụng các phiếu này.

Đây là lần rà tính nhất quán G2, không yêu cầu sửa lại mọi nghĩa đã chốt. Nếu giữ
nguyên, ghi `keep`; reviewer/thời điểm mới chỉ ghi nhận lần rà G2. Thông tin còn
thiếu của review lịch sử vẫn được giữ thiếu, không lấy ngày mới điền ngược vào.

## Cách điền synset-review.csv

Giữ nguyên cột nguồn và ID. Điền các cột cuối:

- `decision`: `keep`, `revise`, hoặc `uncertain` cho định nghĩa hiện tại.
- `membership_decision`: `keep`, `revise`, hoặc `uncertain` cho tập thành viên.
- `proposed_definition`, `proposed_member_sense_ids`: chỉ điền khi đề nghị sửa;
  dùng ID sense ngăn bằng `;`, không sửa trực tiếp cột gốc.
- `additional_evidence_locators`: tài liệu/dòng review hoặc ngữ cảnh hỗ trợ bổ sung.
- `reviewer`, `reviewed_at`, `resolution_notes`: người duyệt thực, thời gian thực
  dạng ISO 8601 có múi giờ, lý do giữ/sửa hoặc điểm chưa chắc.

`source_*`, `state`, các cột cờ và metadata thiếu là thông tin ban đầu. Không
đổi `state` sang approved. Giá trị `keep` không chứng nhận độc lập quyền nguồn.

## Cách điền relation-review.csv

- `decision`: `accept`, `reject`, `revise`, hoặc `uncertain` cho **quan hệ**.
- `resolved_object_synset_id`: ID nghĩa đích chính xác đã có. Một ID khớp bề mặt
  vẫn cần kiểm tra gloss. Nếu chưa có, để trống và dùng `revise`/`uncertain`.
- `proposed_object_definition`: nghĩa mới cần tạo cho từ đích chưa có ID.
- `final_predicate`: quan hệ đề nghị chốt, chẳng hạn `related_to` hoặc `antonym_of`.
- `relation_evidence_locators`, `reviewer`, `reviewed_at`, `resolution_notes`:
  bằng chứng và lý do riêng cho quan hệ hai nghĩa, không chỉ một câu chứa từ.

Trong bản phiếu v1, `target_status=no_existing_synset` có phạm vi kỹ thuật là
**không tìm thấy synset bằng khớp lemma chuẩn hóa**. Giá trị này chưa kết luận
khái niệm chưa tồn tại; không dùng nó để tự tạo 28 concept mới.

Các trường `source_decision`, `source_relation`, `source_reviewer`... giữ đúng CSV
nguồn, kể cả **5 trường hợp reject synonym nhưng được builder cũ đưa vào antonym**.
Không coi `source_decision=reject` là quyết định mới cho quan hệ. Nguồn ví dụ được
sao từ review mở rộng trên train; lần chuẩn bị này chưa đối chiếu lại từng câu
với dataset gốc. Câu chứa từ không tự chứng minh quan hệ loại–cha/trái nghĩa.

## Quy tắc thử is_a

Chiều lưu là **nghĩa hẹp → nghĩa rộng**. Parent là hypernym, child là hyponym;
chỉ cần một cạnh `is_a`, chiều ngược được truy vấn qua API.

Đánh giá theo nghĩa đã chốt, không thay bằng nhãn ViGoEmotions:

1. **Bao hàm một chiều:** mọi trường hợp thuộc nghĩa A có thuộc nghĩa B không?
2. **Không tương đương:** có trường hợp thuộc B nhưng không thuộc A không? Nếu
   hai chiều tương đương, xem xét đồng nghĩa; không dùng is_a thay thao tác gộp.
3. **Cùng loại khái niệm:** không nối một nét mặt, hành vi hoặc đối tượng thành
   loại con của trạng thái tâm lý chỉ vì chúng thường đi cùng nhau.
4. **Đặc điểm phân biệt và phản ví dụ:** nêu điều kiện làm A hẹp hơn B; tìm trường
   hợp phá vỡ bao hàm. Khác mức độ/văn phong hoặc cosine cao chưa đủ kết luận.
5. **Toàn synset:** kết luận phải phù hợp mọi member sense, không chỉ lemma đại diện.

18 dòng là **đề xuất của công cụ dựa trên gloss nguồn**, không phải 18 cạnh đúng
đã được xác minh. `subtype_candidate` và `boundary_case` là cách chọn mẫu thử,
không phải nhãn vàng hay khuyến nghị phải accept/reject.

Điền `forward_entailment`, `reverse_entailment` bằng `yes`, `no`, hoặc `uncertain`;
điền `differentia` (đặc điểm phân biệt), `counterexample` (phản ví dụ nếu có),
`decision` (`accept/reject/revise/uncertain`), `final_predicate`, evidence, reviewer,
ngày và ghi chú. Chỉ accept `is_a` khi bao hàm thuận đúng, không tương đương hai
chiều và hai synset đã đủ ổn định. Nếu bác bỏ, nêu lý do; không bắt buộc dựng cạnh
thay thế. Chỉ reject không có nghĩa tự chấp thuận một phương án khác.

Các mục `synonym_review`, `sense_revision`, `degree_relation_proposal`,
`no_relation` trong cột alternatives là **hướng xử lý để thảo luận**, không phải
predicate được Core API hiện tại hỗ trợ. Nếu cần quan hệ mức độ, đề xuất schema
và tiêu chí riêng trước khi dùng; chưa nhập chúng vào bảng relations.

## Bảo toàn và kiểm chứng

Giữ bản `g2-review-v1` ban đầu. Sao chép sang thư mục làm việc mới, ví dụ
`g2-review-submitted-v1`, rồi điền phiếu. Không sửa `references/` hoặc hash trong
manifest để làm cho file đã sửa trông như bản ban đầu. Khi tiếp nhận kết quả,
sẽ lưu phiên bản nộp và hash mới riêng.

Script chuẩn bị [prepare_g2_review.py](../../scripts/prepare_g2_review.py) kiểm
tra snapshot qua G1, truy vết duy nhất từng quan hệ đến dòng review và từ chối
ghi đè thư mục tồn tại. Có thể tái tạo vào một đường dẫn mới:

```console
python scripts/prepare_g2_review.py --output data/local/g2-review-reproduced
python -m unittest discover -s tests -p test_prepare_g2_review.py -v
```

Sau khi nhóm thống nhất pilot, mở rộng ứng viên theo từng đợt, duyệt nghĩa và
provenance rồi mới nhập snapshot mới. Mục tiêu G2 vẫn là **≥300 concept đã duyệt**;
18 proposal này không làm số lượng concept tăng từ 66 lên 84.
