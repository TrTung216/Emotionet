# Đặc tả G0 v1 — Emotionet cho ViGoEmotions và GA–xLSTM

> Đặc tả lịch sử dùng nghiệm thu G0–G1. Từ 24/11/2026, phần phát triển tiếp theo
> theo [kế hoạch WordNet cảm xúc v2](../Ke_hoach_WordNet_cam_xuc_tieng_Viet.md).
> Các điều chỉnh schema sẽ có profile và migration riêng; không sửa ngược snapshot.

Ngày chuẩn bị: **23/11/2026**. Phạm vi này cụ thể hóa mục tiêu nghiên cứu chủ dự án đã chọn. Đây là hợp đồng bàn giao thiết kế cho G1, không phải tuyên bố mọi chức năng đã triển khai. [Cấu hình bàn giao](../../configs/g0-handoff.json) ghi trạng thái nghiệm thu.

## Phạm vi đã xác định

- Tài nguyên từ/cụm từ cảm xúc tiếng Việt theo **nghĩa**, phục vụ ViGoEmotions đa nhãn và GA–xLSTM. Không chuyển bài toán thành ba nhãn sentiment hoặc ép mọi từ vào 6–7 nhóm.
- Giữ nguyên mapping [28 nhãn ViGoEmotions](../../configs/vigoemotions-labels.json): 27 cảm xúc và neutral. Không có từ điển khớp không có nghĩa câu mang neutral; nhãn neutral có thể đồng xuất hiện với nhãn khác theo dữ liệu.
- G0 bàn giao đặc tả, quy tắc biên soạn và 30 mẫu có quyết định nghĩa đã duyệt. G1 triển khai SQLite, import/export, lookup và đóng gói pip. Mốc ≥300 concept, gold set matcher, 100 biểu thức cảm xúc và release giữ ở G2–G5.
- Matcher/171 đặc trưng/head PyTorch đã có là prototype phục vụ nghiên cứu; không dùng sự tồn tại của prototype để tự nghiệm thu G1–G4.
- Chưa bao gồm WSD tổng quát, web UI, crawl mạng xã hội hay suy luận Floyd–Warshall. Không suy cạnh đồng nghĩa từ cosine hoặc từ nhãn cảm xúc giống nhau.

## Bộ 30 mẫu chuẩn cho thiết kế

[samples.jsonl](../../data/seeds/g0-emotion-v1/samples.jsonl) chứa **30 nghĩa của 30 biểu thức**, gồm một nghĩa đơn nhãn cho mỗi cảm xúc và ba mẫu bổ sung: hạnh phúc, yêu thương, khó chịu. Mỗi mẫu giữ nguyên gloss, nhãn, reviewer, thời điểm và ID sự kiện từ bản seed v2 chủ dự án chọn; kèm một câu train đã được đánh dấu `matches_sense` trong bản rà soát cuối.

Đây là **tái sử dụng quyết định đã có**, không có lượt duyệt ngữ nghĩa mới do công cụ tự tạo. Reviewer nguồn là `antigravity`; không khẳng định đó là kiểm duyệt độc lập. Review câu không ghi reviewer/thời điểm được giữ thiếu thông tin, không lấy ngày đóng gói thay ngày duyệt. POS để null vì chưa được duyệt. Các câu ví dụ không phải gold set và không dùng để báo cáo precision.

Các nghĩa tách có thời điểm review còn thiếu và các ứng viên embedding mới không được dùng để đủ số lượng 30 mẫu này. Chúng tiếp tục tồn tại trong các snapshot nghiên cứu. Không yêu cầu duyệt lại toàn bộ seed hay phân xử lại review nhóm.

30 concept tổng quát cũ tại `data/seeds/g0/` vẫn là fixture `candidate` để kiểm tra đa nghĩa, alias và quan hệ. **Không chuyển chúng thành approved.** Bộ 30 mẫu nghiệm thu G0 chuyển sang miền cảm xúc theo mục tiêu hiện tại; mẫu thiết kế không cộng thêm vào số lượng concept G2.

## Mô hình dữ liệu và ánh xạ

Giữ các thực thể trong [thiết kế tổng quát](data-model.md), áp dụng các điều chỉnh cụ thể sau cho profile nghiên cứu. Khi khác nhau, bảng này là hợp đồng G1 cho miền cảm xúc; fixture cũ giữ nguyên schema lịch sử.

| Thực thể | Khóa và trường cốt lõi | Ràng buộc |
|---|---|---|
| Entry | `entry_id`, `lemma`, `normalized_form`, `lang`, `pos` | Ngôn ngữ vi; POS null nghĩa là chưa biết, không suy từ gloss. Một entry có nhiều sense. |
| Form | `form_id`, `entry_id`, `surface`, `normalized_form`, `form_type` | Có form canonical; abbreviation/spelling_variant là biến thể chữ viết, không dùng thay synonym. |
| Sense | `sense_id`, `entry_id`, `synset_id`, `gloss`, `evidence_ids` | Mỗi sense thuộc một synset. Không gộp nghĩa chỉ vì cùng lemma hoặc cùng nhãn. |
| Synset / Concept | `synset_id`, `preferred_lemma`, `definition`, `member_sense_ids` | `synset_id` là ID concept trong profile này. Singleton hợp lệ; nhiều sense chỉ được gộp sau quyết định tương đương nghĩa. |
| Relation | `rel_id`, `subject_synset_id`, `predicate`, `object_synset_id`, `evidence_ids` | Quan hệ được chấp nhận cần cả hai đầu có ID nghĩa rõ. `object_term` chưa phân giải chỉ là đề xuất biên soạn, không tự biến thành cạnh graph đã duyệt. |
| Evidence | `evidence_id`, `source_id`, `source_record_id`, `locator`, `method` | Lưu đường dẫn/hash nguồn; phân biệt lexical-source, sense-review, corpus-example và relation-review. |
| Review | `review_id`, target, decision, reviewer, reviewed_at, rationale, evidence_ids | Append-only; bảo toàn thông tin thiếu của dữ liệu nhập. Thời điểm nhập khác thời điểm review. |
| EmotionAnnotation | `annotation_id`, `sense_id`, taxonomy/version, label, context_scope, evidence_ids | Một sense có thể có nhiều nhãn đã duyệt; score/intensity/confidence không có bằng chứng để null. |
| ContextExample | dataset/version, split, dataset_id, text, sense_id, decision, flags | Nhãn toàn câu lưu riêng nhãn sense. Text nguồn giữ nguyên Unicode; normalize trên bản dùng để đối chiếu. |

Giữ nguyên ID chuỗi của snapshot (`entry_seed_*`, `seed_*_sense`, `syn_*`...), không cấp lại ID số chỉ để khớp fixture cũ. SQLite dùng TEXT primary key và foreign key. Import profile nghiên cứu không làm mất ID hoặc metadata chưa được lớp Python prototype biểu diễn.

Snapshot v2 có 77 entry, 82 sense, 66 synset, 29 relation là đầu vào nghiên cứu; không mặc định mọi trường và mọi quan hệ đã đáp ứng hợp đồng phát hành này. Đặc biệt, relation thiếu provenance hoặc chỉ có object_term phải được nhập vào trạng thái chờ rà, giữ bản ghi nguồn.

## Trạng thái nội dung và quyền chia sẻ

Tách hai trục: **nội dung** (`candidate`, `needs_review`, `accepted_as_submitted`, `approved`, `rejected`) và **quyền/chính sách phân phối**. `accepted_as_submitted` ghi nhận quyết định người dùng nhập; không đồng nghĩa độc lập xác minh hoặc nguồn đã cấp giấy phép mở. Chỉ dùng `approved` khi bộ yêu cầu review tương ứng được đáp ứng và ghi đủ bằng chứng.

Nguồn đã nhập phải bảo toàn trạng thái lịch sử. Quyết định chia sẻ mới của chủ dự án được tham chiếu ở [data-sharing.json](../../configs/data-sharing.json), không sửa tất cả `not_cleared` cũ thành chứng nhận pháp lý. Xem [chính sách bàn giao](handoff-2026-11-23.md).

## Nghĩa, alias và quan hệ

- Một nhãn cảm xúc không phải một synset: “buồn”, “buồn bã”, “sầu” không tự gộp chỉ vì sadness.
- Sense có nhiều nhãn được giữ như đã duyệt. Không tách thành các nghĩa giả chỉ để đạt “một sense–một nhãn”. Ví dụ “yêu thương” có love/caring trong bản chốt.
- Từ đa nghĩa trả toàn bộ candidate sense. “Nhận ra danh tính” không được tự chọn realization; “ghét món ăn” không được tự chọn disgust.
- Khi gộp synset, lưu mapping ID cũ→mới, review và hash đầu vào. Không xóa lịch sử. Từ chối chạy builder ghi đè snapshot đã có.
- `related_to` và `antonym_of` phải có quyết định quan hệ riêng. Một dòng reject việc kết nạp synonym **không tự đủ** để duyệt antonym. Các cảm xúc khác nhau không mặc nhiên trái nghĩa.
- Alias viết tắt áp dụng cho entry; nếu chỉ áp dụng một sense thì tạo entry/sense riêng. Không dùng alias để né tách nghĩa.

## Use case và tiêu chí kiểm thử bàn giao

| ID | Tình huống | Kết quả yêu cầu khi triển khai |
|---|---|---|
| R01 | Lookup `  KHÓ   CHỊU ` và bản Unicode NFD | Khớp cùng entry; giữ lemma hiển thị; nhãn sense đã chốt chỉ annoyance. |
| R02 | Lookup `thương`, `lo`, `tiếc`, `ghét` | Trả các nghĩa đã tách, không tự chọn sense đầu tiên hoặc trộn nhãn rồi trình bày một ID duy nhất. |
| R03 | Tra `yêu thương` | Giữ love/caring theo review; không tự sửa thành một nhãn. |
| R04 | Match cụm dài chứa cụm ngắn | Leftmost-longest, không double-count; trả candidate sense và span trên text gốc, kể cả NFD. |
| R05 | `không buồn nhưng vui`, `buồn,không vui` | Flag phủ định đúng mệnh đề; flag không tự biến thành nhãn cảm xúc câu. |
| R06 | Câu không có mục từ hoặc concept trung tính | Không tự gán neutral; đặc trưng cho biết thiếu bằng chứng từ điển. |
| R07 | Import–export JSONL→SQLite→JSONL | Giữ ID, gloss, nhãn, nguồn, review, missing values và quan hệ; FK sai phải rollback. |
| R08 | Bản ghi không đủ review hoặc quyền theo chế độ xuất | Báo rõ lý do; export nghiên cứu giữ trạng thái và quyết định chủ dự án; không tự gọi là bản được cấp phép mở. |
| R09 | Tokenizer cắt đuôi câu | Encoder và đặc trưng dùng cùng cửa sổ; cache so toàn bộ vector, không tái dùng cache của cửa sổ khác. |
| R10 | Mẫu g=0 chạy riêng/ghép batch | Logits tương đương trong sai số khi eval; không phụ thuộc mẫu khác trong batch. |
| R11 | Nạp ứng viên gần vector | Giữ candidate; không tự thêm synonym hoặc nhãn. |
| R12 | Gộp nghĩa/xuất phiên bản mới | Giữ alias ID lịch sử, input/output hash và quan hệ phụ thuộc; không ghi đè snapshot nguồn. |

API mục tiêu G1: `Emotionet.open`, `lookup`, `get_concept`, `relations`, `import_jsonl`, `export_jsonl`, `close`. Chế độ nghiên cứu phải được chọn rõ và trả provenance/status; chế độ dữ liệu hoàn tất không tự nâng trạng thái accepted thành approved. Matcher và feature integration được nghiệm thu ở G3/G4, không phải điều kiện API đã chạy của G0.

## Kiểm chứng và tái lập

```console
python scripts/prepare_g0_handoff.py --check
python scripts/validate_g0.py
```

Lệnh đầu kiểm tra 30 nghĩa với quyết định seed gốc, review ngữ cảnh train, độ phủ 27 nhãn, số lượng và hash. Lệnh thứ hai chỉ kiểm tra fixture tổng quát cũ. Cả hai không phải phép đo độ chính xác cảm xúc.

Train/validation/test không đổi vai trò. Embedding và mọi thống kê fit theo train/inner-train phù hợp protocol. 155 cặp rà soát khám phá không trở thành gold set. Cài đặt package, SQLite và tập gold đánh giá riêng nằm trong backlog G1–G3.
