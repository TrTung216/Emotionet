# Đặc tả dữ liệu v1 — dự thảo G0

JSONL UTF-8, một object mỗi dòng. SQLite G1 sẽ dùng các bảng tương ứng;
schema version khởi đầu là `1`, data version bộ nháp là `0.0.0-g0`.

## Trường chung

Mọi thực thể có `status`, `created_at`, `updated_at` (ISO 8601 UTC),
`reviewer` (null khi chưa duyệt), `reviewed_at` (null khi chưa duyệt).
Trạng thái: candidate, needs_review, approved, rejected.

Mọi thực thể ngoài Evidence có `evidence_ids`: mảng ID bằng chứng không rỗng.
`approved` yêu cầu reviewer, reviewed_at và bằng chứng được duyệt với nguồn
có quyền sử dụng đã xác minh. Các bản ghi nháp chưa đáp ứng điều kiện này.

| Thực thể / file JSONL | Trường riêng bắt buộc |
|---|---|
| LexicalEntry / entries | entry_id, lemma, lang, pos, normalized_form |
| LexicalForm / forms | form_id, entry_id, surface, normalized_form, form_type |
| Sense / senses | sense_id, entry_id, concept_id, gloss, examples |
| Concept / concepts | concept_id, preferred_label, definition, domain |
| Relation / relations | rel_id, subject_id, predicate, object_id |
| Evidence / evidence | evidence_id, source_id, locator, excerpt, method |
| EmotionAnnotation / emotions | annotation_id, target_type, target_id, emotion, score, context_scope, context |

`examples` là mảng chuỗi; `excerpt` có thể null (không bịa trích dẫn);
`locator` chỉ vị trí có thể đối chiếu trong nguồn. License nằm trong registry nguồn,
không nhân bản chuỗi giấy phép ở mọi bản ghi. Registry gồm source_id, title, url,
license, allowed_uses, retrieved_at, rights_status, notes. Evidence trỏ source_id.
Evidence có thể có `rationale` để giải thích cách đề xuất một quan hệ; trường này
không thay thế trích dẫn hoặc kiểm chứng từ nguồn độc lập.

## Ràng buộc

- ID ổn định với prefix `lex_`, `frm_`, `sen_`, `con_`, `rel_`, `evd_`, `emo_`
  và sáu chữ số. Cấp tuần tự qua một nơi quản lý; không cấp lại ID đã xóa.
- Entry phân biệt theo `(lang, normalized_form, pos)`. Nhiều sense dùng chung
  entry khi lemma và POS giống nhau; `đá` danh từ/động từ là hai entry.
- POS khởi đầu dùng NOUN, VERB, ADJ, ADV, PROPN, X; đây là quy ước dự án.
- `lang="vi"` trong MVP. Chuỗi hiển thị giữ nguyên; normalized_form dùng
  NFC(casefold(NFC(surface))) và gộp khoảng trắng, không bỏ dấu.
- Mỗi entry có ít nhất một form canonical và một sense; canonical khớp lemma.
- Form type: canonical, abbreviation, spelling_variant. Từ đồng nghĩa có lemma
  độc lập dùng entry/sense riêng cùng concept, không giả thành quan hệ is_a.
- Form thuộc entry nên áp dụng cho các sense của entry đó. Nếu cách gọi chỉ
  áp dụng cho một nghĩa thì tạo entry riêng cùng concept, không alias cả entry đa nghĩa.
- Mỗi sense trỏ đúng một entry và một concept; concept có ít nhất một sense.
- Definition mô tả concept; gloss diễn đạt nghĩa của entry. Cả hai có provenance.
- FK phải tồn tại; không xóa cứng bản ghi đang được tham chiếu. SQLite bật foreign_keys.
- Không có cạnh tự trỏ. Không trùng `(subject_id, predicate, object_id)`;
  gộp bằng chứng bổ sung vào evidence_ids.
- Với quan hệ đối xứng, lưu một cạnh theo thứ tự ID tăng dần; API direction=both
  cho phép tìm ở hai đầu. Không tự nhân bản cạnh đảo trong JSONL.
- `is_a`, `part_of`, `subfield_of` không được tạo chu trình trong từng loại cạnh.
  Kiểm tra cả tập bản ghi không bị rejected trước khi duyệt.

## Lớp cảm xúc

`target_type` là entry hoặc sense; target_id phải trỏ đúng bảng. Không gán nhãn
concept trung tính mặc định. `context_scope` là lexical hoặc contextual;
contextual yêu cầu context không rỗng. Score null hoặc số hữu hạn trong [0,1],
biểu diễn cường độ theo hướng dẫn gán nhãn, không phải confidence mô hình.
Vocabulary nháp: joy, sadness, anger, fear, surprise, disgust; chốt rubric tại G4.
Bộ G0 để emotions rỗng, kể cả các concept mô tả cảm xúc, vì chưa có nhãn được duyệt.

## Nhập, xuất và phiên bản

- Thứ tự nhập: registry → evidence → concepts/entries → forms/senses → relations/emotions.
- Nhập trong transaction; ID trùng hoặc tham chiếu sai phải rollback, không tự ghi đè.
- Xuất đầy đủ phục vụ biên soạn giữ mọi trạng thái; xuất phát hành chỉ lấy approved
  và toàn bộ phụ thuộc approved, có quyền phân phối rõ ràng.
- Nếu phụ thuộc không đủ điều kiện, dừng xuất phát hành và liệt kê lỗi; không
  âm thầm bỏ nguồn, tự duyệt hoặc tạo dữ liệu thay thế.
- Sắp dòng theo ID để diff ổn định; lưu manifest gồm schema/data version, số lượng,
  checksum và phiên bản công cụ khi phát hành. Manifest G0 chỉ mô tả bản nháp.
- Migration SQLite đánh số và chạy transaction. Đổi nghĩa không tương thích tạo ID
  mới; lưu liên kết thay thế và lịch sử, không dùng lại ID cũ.

## Lịch sử duyệt

`reviews.jsonl` lưu sự kiện append-only: review_id, entity_type, entity_id,
from_status, to_status, reviewer, reviewed_at, rationale, evidence_ids.
Thay nội dung đã approved đưa bản ghi về needs_review, ghi sự kiện và yêu cầu duyệt lại.
Không chấp nhận tự chuyển approved chỉ vì kiểm tra kỹ thuật thành công.
