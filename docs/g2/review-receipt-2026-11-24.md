# Tiếp nhận kết quả rà soát G2 ngày 24/11/2026

Đã tiếp nhận các quyết định của nhóm trong
[g2-review-submitted-v1](../../data/local/g2-review-submitted-v1/), đối chiếu với
phiếu gốc và lưu bản hợp nhất tại
[g2-review-reconciled-v1](../../data/local/g2-review-reconciled-v1/).
Không yêu cầu làm lại phần rà soát đã nộp. Bản nguồn và các cột nghĩa/ID ban đầu
được giữ nguyên; chưa áp dụng thay đổi vào snapshot synset hoặc graph.

## Kết quả đã đối chiếu

| Hạng mục | Kết quả |
|---|---|
| Định nghĩa 66 synset | 66 keep |
| Membership 66 synset | 64 keep, 2 revise: nhóm khâm phục/nể/phục và nhóm buồn/đau lòng/tủi thân |
| Pilot is_a sau xác nhận | 18/18 có quyết định: 5 accept, 4 revise, 9 reject |
| Quan hệ nghiên cứu cũ | 29/29 dòng relation-review.csv vẫn chưa có quyết định |
| Lịch sử tiếp nhận | 84 quyết định được ghi nhận; không tạo record approved hoặc cạnh mới |
| Kiểm thử chạy lại | 74/74 unit test đạt, không skip, trước khi thêm công cụ tiếp nhận này |

Số 66 keep ở cột decision là quyết định giữ **định nghĩa**, không thay thế cột
membership_decision. Hai yêu cầu sửa membership vẫn còn hiệu lực.

## Bổ sung được chủ dự án xác nhận

CSV đã nộp thực tế có 17 quyết định pilot: 5 accept, 3 revise, 9 reject. Dòng
`g2_isa_56675b2120fa`, **sửng sốt → ngạc nhiên**, còn trống. Tóm tắt dùng tên
“kinh ngạc → bất ngờ”; chủ dự án xác nhận áp dụng quyết định đó cho đúng cặp
trong phiếu gốc.

Bản tiếp nhận chỉ bổ sung dòng này thành `decision=revise`,
`final_predicate=related_to`, kèm lý do đã gửi và
[xác nhận của chủ dự án](../../data/local/g2-review-reconciled-v1/user-confirmation.json).
Người xác nhận ghi `project_owner`, ngày xác nhận 24/11/2026. Không gán người
review là antigravity cho dòng bổ sung, không tự điền thời điểm chính xác hoặc
kết quả forward/reverse entailment mà người dùng chưa cung cấp.

Các dòng còn lại giữ nguyên reviewer/thời gian như bản nộp, không xác minh hay
thay đổi danh tính người review. Trạng thái pending trong cột nguồn được giữ
để bảo toàn phiếu; manifest mới ghi nhận việc đã tiếp nhận, không đổi thành
approved theo chuẩn phát hành.

## Quyết định được kế thừa sang profile WordNet

- **Nể:** giữ quyết định cần làm rõ nghĩa nể phục và điều kiện ngữ cảnh; bản
  này chưa sửa matcher hoặc tự tạo thêm nghĩa kiêng nể.
- **Tủi thân:** giữ đề nghị loại `sense_cand_d6b678c30a79` khỏi nhóm buồn, giữ
  hai sense buồn/đau lòng. Việc tạo synset đích, mapping và quan hệ nằm ở bước
  chuẩn hóa dữ liệu tiếp theo.
- **Năm cặp is_a được accept:** giữ quyết định đã nộp. Khi triển khai WordNet,
  kiểm POS, phạm vi quan hệ và tính ổn định của hai đầu trước khi đưa vào graph.
- **Các cặp reject/revise:** giữ lý do và phương án thay thế. Không biến mọi
  trường hợp reject is_a thành một cạnh related_to tự động.

Profile WordNet mới cần tập trung bổ sung vào các điểm sau, không đổi ngầm
quyết định keep của lượt review trước:

| Nhóm | Điểm cần giải quyết trong profile mới |
|---|---|
| biết ơn / cám ơn | Phiếu giữ chung nhưng ghi khác trạng thái nội tâm và hành vi phát ngôn; cần POS và tiêu chí tương đương nghĩa |
| sợ hãi / sợ sệt | Membership giữ, nhưng pilot nêu nội bộ chưa đồng nhất; cần đối chiếu định nghĩa từng sense |
| hối hận / tiếc nuối / day dứt / hối tiếc | Ghi chú về tiếc cơ hội khách quan cần tách phạm vi với sense tự trách đã chốt; ảnh hưởng đầu cha của ăn năn |
| Các cặp khác cường độ hoặc cảm xúc kết hợp | Rà theo POS và quy tắc bao hàm; profile mới không mặc định mọi quan hệ là cây một cha |

## Việc còn lại theo thứ tự

1. Chốt profile WordNet/POS/quan hệ hai cấp ở G2a; kế thừa 84 quyết định đã nhận
   khi tạo phiếu phiên bản mới.
2. Giải quyết hai đề nghị sửa membership và các điểm cần bổ sung theo profile,
   rồi mới tạo snapshot lõi mới với mapping và evidence.
3. Hoàn thành **29 quan hệ nguồn chưa điền**, gồm 24 related_to và 5 antonym_of;
   phân giải ID nghĩa đích, ghi quyết định và lý do riêng.
4. Sau khi bộ lõi ổn định, tiếp tục mở rộng ứng viên theo kế hoạch v2.

## File và truy vết

- [Phiếu synset đã tiếp nhận](../../data/local/g2-review-reconciled-v1/synset-review.csv).
- [Phiếu pilot đã hợp nhất xác nhận](../../data/local/g2-review-reconciled-v1/is-a-pilot-review.csv).
- [Phiếu 29 quan hệ còn lại](../../data/local/g2-review-reconciled-v1/relation-review.csv).
- [Các quyết định đã ghi nhận](../../data/local/g2-review-reconciled-v1/received-decisions.jsonl).
- [Manifest tiếp nhận](../../data/local/g2-review-reconciled-v1/manifest.json).

`source-submission/` giữ nguyên mọi byte của bản nộp, kể cả manifest mẫu ban đầu.
Manifest mẫu đó vẫn mô tả phiếu trắng; không sửa hash lịch sử để khớp file đã
điền. Manifest tiếp nhận ghi hash mới riêng cho nguồn và đầu ra. Bản tóm tắt
đính kèm được lưu trong `submission-summary.txt`.

[receive_g2_review.py](../../scripts/receive_g2_review.py) kiểm tra ID, các cột
nguồn, file tham chiếu và từ chối ghi đè đích đã tồn tại. Việc tiếp nhận chỉ
ghi lại quyết định và provenance, không thay thế review theo profile WordNet.
