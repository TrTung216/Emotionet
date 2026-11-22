# KẾ HOẠCH XÂY DỰNG THƯ VIỆN EMOTIONET

**Định hướng:** Thư viện từ điển từ vựng – ngữ nghĩa tiếng Việt, hỗ trợ từ đơn, cụm từ, khái niệm, quan hệ ngữ nghĩa và một lớp tri thức cảm xúc mở rộng  
**Loại tài liệu:** Kế hoạch kỹ thuật và nghiên cứu (đề xuất)  
**Phiên bản:** 1.0 — ngày 15/11/2026  
**Trạng thái:** Kế hoạch triển khai; các chỉ tiêu, mốc thời gian và mô hình dữ liệu dưới đây là đề xuất, chưa phải kết quả đã đạt được.

## 1. Tóm tắt điều hành

Emotionet được định hướng là một thư viện Python và bộ dữ liệu từ vựng – ngữ nghĩa cho tiếng Việt. Thay vì chỉ ánh xạ một chuỗi sang một định nghĩa, hệ thống lưu **hình thức từ/cụm từ → nghĩa trong ngữ cảnh → khái niệm → quan hệ ngữ nghĩa**, đồng thời cho phép gắn thông tin cảm xúc **khi có căn cứ**. Ví dụ, “AI” và “trí tuệ nhân tạo” có thể chỉ cùng một khái niệm; “học máy” có quan hệ `subfield_of` với “trí tuệ nhân tạo”; “mèo” có quan hệ `is_a` với “động vật có vú”. Các khái niệm trung tính không bị ép mang nhãn cảm xúc.

**Sản phẩm mục tiêu:** (1) dữ liệu có phiên bản và nguồn gốc rõ ràng; (2) thư viện Python với API tra cứu, nhận diện cụm từ, truy vấn quan hệ; (3) quy trình nhập dữ liệu và kiểm duyệt; (4) bộ kiểm thử chất lượng; (5) báo cáo thực nghiệm khi tích hợp với mô hình NLP.

**Chiến lược:** Khởi đầu bằng một bộ dữ liệu nhỏ được kiểm duyệt kỹ, sau đó mở rộng bán tự động. Ưu tiên độ đúng của nghĩa và quan hệ hơn tổng số mục từ.

## 2. Mục tiêu, phạm vi và nguyên tắc thiết kế

### 2.1. Mục tiêu

1. Lưu được **từ đơn, từ ghép, cụm từ nhiều tiếng, thuật ngữ và khái niệm** như “trí tuệ nhân tạo”, “động vật có vú”.
2. Hỗ trợ **đa nghĩa**: một mục từ có thể chỉ nhiều nghĩa/khái niệm, ví dụ “đường” (đường đi; đường ăn).
3. Hỗ trợ **nhiều cách gọi**: một khái niệm có thể có tên chuẩn, tên đồng nghĩa, viết tắt, biến thể chính tả.
4. Biểu diễn quan hệ có hướng giữa các khái niệm (`is_a`, `part_of`, `subfield_of`, `related_to`...), kèm nguồn và trạng thái kiểm duyệt.
5. Tra cứu từ/cụm từ trong văn bản tiếng Việt, ưu tiên khớp cụm dài và trả về các nghĩa ứng viên thay vì đoán chắc một nghĩa.
6. Có lớp mở rộng cảm xúc cho từ/cụm từ hoặc nghĩa cụ thể, phục vụ các thí nghiệm NLP trong tương lai.

### 2.2. Phạm vi phiên bản đầu

**Có trong MVP (v0.1):** dữ liệu tiếng Việt; từ/cụm từ; nhiều nghĩa; định nghĩa; tên gọi; quan hệ cơ bản; nguồn dữ liệu; kiểm duyệt; tìm kiếm chính xác; nhận diện cụm từ theo từ điển; CLI/API Python; lưu bằng SQLite và xuất JSONL.

**Để sau MVP:** tự động phân giải nghĩa theo ngữ cảnh (WSD); ontology suy luận phức tạp; tìm kiếm vector; đồng bộ đa ngôn ngữ quy mô lớn; cơ sở dữ liệu đồ thị chuyên dụng; gán nhãn cảm xúc ngầm bằng mô hình học sâu; trình biên tập web nhiều người dùng.

### 2.3. Nguyên tắc bắt buộc

- **Tách chuỗi và nghĩa:** không gán một concept ID duy nhất cho mọi lần xuất hiện của cùng một từ.
- **Tách quan hệ từ vựng và quan hệ khái niệm:** `alias_of`/cách gọi khác không đồng nhất với `is_a`.
- **Không tự động gán cảm xúc cho khái niệm trung tính.** Cảm xúc có thể phụ thuộc câu và ngữ cảnh.
- **Có provenance:** mỗi định nghĩa/quan hệ phải lưu nguồn, ngày cập nhật, phương pháp tạo và trạng thái xác minh.
- **Không dùng test để chỉnh dữ liệu hoặc chọn mô hình:** mọi thực nghiệm downstream chọn cấu hình trên train/validation.
- **Tôn trọng giấy phép:** không nhập hoặc tái phân phối dữ liệu khi nguồn không cho phép.

## 3. Kiến trúc tổng thể

**Luồng dữ liệu:** Nguồn được phép sử dụng → Thu thập ứng viên → Chuẩn hóa tiếng Việt → Trích xuất từ/cụm từ → Gợi ý nghĩa/quan hệ → Kiểm duyệt → Kho dữ liệu phiên bản hóa → Chỉ mục tìm kiếm → API/CLI → Ứng dụng NLP.

Hệ thống gồm bốn lớp:

| Lớp | Chức năng | Đầu ra |
|---|---|---|
| Data ingestion | Nhập từ từ điển, văn bản, CSV/JSONL; ghi nguồn và giấy phép | Ứng viên chưa kiểm duyệt |
| Semantic curation | Phân biệt nghĩa; viết định nghĩa; tạo và duyệt quan hệ | Concept/sense/relation đã duyệt |
| Storage & retrieval | SQLite, chỉ mục chuỗi, bảng liên kết; xuất JSONL | Kho dữ liệu truy vấn được |
| NLP integration | Matcher cụm từ, tra cứu ngữ nghĩa, đặc trưng cảm xúc | Kết quả API và dữ liệu phục vụ mô hình |

**Công nghệ đề xuất:** Python 3.11+, SQLite (có thể dùng FTS5 cho tìm kiếm văn bản), Pydantic hoặc dataclass để xác thực schema, pytest để kiểm thử, Ruff cho chất lượng mã. Bộ tách từ tiếng Việt (ví dụ VnCoreNLP) chỉ là công cụ hỗ trợ; chức năng nhận diện cụm từ cần hoạt động được cả khi không cài mô hình ngoài.

## 4. Mô hình dữ liệu chuẩn

Thay vì một bảng chứa mọi thứ, sử dụng các thực thể riêng để tránh nhập nhằng.

| Thực thể | Trường tối thiểu | Ý nghĩa |
|---|---|---|
| `LexicalEntry` | `entry_id`, `lemma`, `lang`, `pos`, `normalized_form` | Hình thức mục từ: từ đơn hoặc cụm từ |
| `LexicalForm` | `form_id`, `entry_id`, `surface`, `form_type` | Tên đầy đủ, viết tắt, biến thể hoặc cách viết khác |
| `Sense` | `sense_id`, `entry_id`, `concept_id`, `gloss`, `examples` | Nghĩa cụ thể của mục từ |
| `Concept` | `concept_id`, `preferred_label`, `definition`, `domain` | Đơn vị tri thức độc lập với cách gọi |
| `Relation` | `rel_id`, `subject_id`, `predicate`, `object_id`, `evidence_id`, `status` | Quan hệ giữa hai khái niệm |
| `EmotionAnnotation` | `annotation_id`, `target_type`, `target_id`, `emotion`, `score`, `context_scope` | Nhãn cảm xúc gắn có điều kiện |
| `Evidence` | `evidence_id`, `source`, `license`, `method`, `reviewer`, `status` | Nguồn gốc, quyền sử dụng và đánh giá |

**Quy ước ID:** sử dụng ID ổn định, không dùng chính chuỗi tiếng Việt làm khóa chính; ví dụ `con_000001`, `lex_000001`, `sen_000001`. Không tái sử dụng ID đã công bố.

**Quan hệ MVP:** `is_a`, `part_of`, `subfield_of`, `related_to`, `antonym_of`. `same_as` chỉ dùng khi hai concept thực sự tương đương. Quan hệ `is_a` cần kiểm tra vòng lặp và phân biệt với quan hệ “có liên quan”.

### 4.1. Ví dụ bản ghi

```json
{
  "concept_id": "con_000001",
  "preferred_label": "trí tuệ nhân tạo",
  "definition": "Lĩnh vực nghiên cứu và phát triển hệ thống thực hiện các nhiệm vụ liên quan đến trí thông minh.",
  "domain": "computer_science",
  "lexical_forms": ["trí tuệ nhân tạo", "AI"],
  "relations": [],
  "emotions": [],
  "review_status": "pending",
  "evidence": {"method": "manual_draft", "source": "example_only"}
}
```

Đây là **dữ liệu minh họa cho schema**, không phải một mục từ đã qua kiểm duyệt. Quan hệ “học máy” `subfield_of` “trí tuệ nhân tạo” và “mèo” `is_a` “động vật có vú” nên được lưu dưới dạng các cạnh riêng có nguồn dẫn.

### 4.2. Chuẩn hóa tiếng Việt

- Chuẩn Unicode NFC; lưu bản gốc và bản chuẩn hóa để đối chiếu.
- Giữ dấu tiếng Việt; chỉ dùng tìm kiếm không dấu như một chế độ tra cứu bổ sung.
- Giữ nguyên dấu cách trong cụm từ; không xem mỗi tiếng cách nhau bằng khoảng trắng là một từ độc lập.
- Tìm kiếm ưu tiên **longest match**, có trả về vị trí xuất hiện trong câu và xử lý trường hợp các cụm chồng lấn.
- Từ đa nghĩa phải trả về danh sách ứng viên (`senses`) kèm ngữ cảnh nếu có, không mặc định chọn nghĩa đầu tiên.

## 5. Quy trình xây dựng dữ liệu

### Bước 1. Chọn nguồn và kiểm tra quyền sử dụng

Ưu tiên danh mục thuật ngữ tự biên soạn, nguồn mở có giấy phép phù hợp và văn bản được phép xử lý. Lập `sources.csv` với các trường `source_id`, `url`, `license`, `allowed_uses`, `retrieved_at`, `notes`. Các nguồn tham khảo để khảo sát phương pháp gồm Princeton WordNet, ConceptNet, OntoLex-lemon, VnCoreNLP và các nghiên cứu Vietnamese WordNet; **không mặc định được phép sao chép toàn bộ dữ liệu từ các nguồn này**.

### Bước 2. Trích xuất mục từ ứng viên

Nhập danh sách từ và cụm từ bằng tay hoặc từ corpus; hỗ trợ phrase mining, phân đoạn từ và các mẫu thuật ngữ. Ví dụ câu “Học máy là một nhánh của trí tuệ nhân tạo” có thể sinh các ứng viên “học máy”, “trí tuệ nhân tạo” và quan hệ `subfield_of` cần xác minh.

### Bước 3. Chuẩn hóa và phát hiện trùng

Thống nhất Unicode, cách viết, chữ hoa/chữ thường cho mục đích tra cứu, alias và tên viết tắt. Không gộp hai nghĩa chỉ vì hai chuỗi giống nhau; không gộp hai khái niệm chỉ vì embedding gần nhau.

### Bước 4. Biên soạn nghĩa và quan hệ

Người biên soạn chọn tên chuẩn, viết định nghĩa ngắn, phân biệt nghĩa, thêm ví dụ và tạo quan hệ có hướng. Mỗi quan hệ lưu bằng chứng hoặc URL nguồn. Các gợi ý tự động/LLM luôn có trạng thái `candidate`.

### Bước 5. Kiểm duyệt hai bước

Người duyệt đối chiếu định nghĩa, từ đồng nghĩa, quan hệ phân cấp và giấy phép. Mục gây tranh cãi được đánh dấu `needs_review`; chỉ mục `approved` mới đi vào bản dữ liệu công bố. Lưu lịch sử thay đổi và người duyệt.

### Bước 6. Đóng gói và phát hành

Xuất SQLite dùng cho API, JSONL để trao đổi dữ liệu, và `CHANGELOG.md` ghi khác biệt giữa các phiên bản. Tạo tập dữ liệu đánh giá cố định để phát hiện lỗi hồi quy.

## 6. Thiết kế thư viện Python và API

Cấu trúc dự án đề xuất:

```text
emotionet/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/emotionet/
│   ├── __init__.py
│   ├── models.py           # LexicalEntry, Sense, Concept...
│   ├── storage.py          # SQLite + schema migration
│   ├── normalize.py        # Unicode, so khớp, dấu
│   ├── matcher.py          # Trie/longest phrase matching
│   ├── relations.py        # Truy vấn đồ thị, kiểm tra vòng
│   ├── curation.py         # Candidate/review/approve
│   └── api.py              # Giao diện công khai
├── data/
│   ├── seeds/              # Dữ liệu nhập mẫu
│   ├── licenses/           # Nhật ký giấy phép
│   └── evaluation/         # Gold set
├── scripts/                # Nhập liệu/kiểm tra/xuất bản
├── tests/
└── docs/
```

**API tối thiểu cần cung cấp:**

```python
from emotionet import Emotionet

net = Emotionet.open("data/emotionet.sqlite")
net.lookup("đường")                  # nhiều nghĩa ứng viên
net.lookup("trí tuệ nhân tạo")        # khái niệm và tên gọi
net.match("Tôi đang học trí tuệ nhân tạo")
net.relations("con_000001", predicate="related_to")
net.get_concept("con_000001")
```

Các lời gọi trên là **hợp đồng API mục tiêu**, chưa khẳng định các hàm đã được hiện thực. Đầu ra cần có ID, định nghĩa, confidence nếu được tính, vị trí chuỗi, nguồn, trạng thái xác minh; các giá trị thiếu phải để `null`/rỗng thay vì tự suy diễn.

## 7. Lộ trình triển khai 12 tuần

Các mốc dưới đây giả định một nhóm nhỏ 1–3 người, ưu tiên MVP và kiểm duyệt chất lượng; có thể điều chỉnh theo nguồn lực.

| Giai đoạn | Thời gian | Công việc chính | Bàn giao/tiêu chí hoàn thành |
|---|---|---|---|
| G0 — Thiết kế | Tuần 1–2 | Chốt use case, schema, quy tắc nghĩa/quan hệ, bản quyền | Đặc tả v1, 30 mẫu chuẩn được duyệt |
| G1 — Core API | Tuần 3–4 | SQLite, import/export, tra cứu, chuẩn hóa, test unit | Cài được bằng pip; API cơ bản và test chạy |
| G2 — Semantic MVP | Tuần 5–7 | Bổ sung 300 khái niệm đầu, đa nghĩa, alias, quan hệ | ≥300 concept đã duyệt, có provenance |
| G3 — Phrase matcher | Tuần 8–9 | Trie/longest match, phân giải trùng lặp, gold set | Báo cáo precision/recall trên tập đánh giá |
| G4 — Emotion layer | Tuần 10–11 | Schema cảm xúc tùy chọn; thử 100 biểu thức được duyệt | Nhãn có ngữ cảnh, không ép nhãn cho khái niệm trung tính |
| G5 — Release | Tuần 12 | Tài liệu, CLI, benchmark và phát hành bản thử | `v0.1.0`, README, CHANGELOG, QA report |

**Sau MVP:** Mở rộng có kiểm duyệt lên khoảng 500–1.000 khái niệm; bổ sung WSD, tìm kiếm gần đúng/vector và thử tích hợp NLP nếu tài nguyên cho phép. Quy mô nêu trên là mục tiêu lập kế hoạch, không phải dữ liệu hiện có.

## 8. Đánh giá chất lượng và tiêu chí nghiệm thu

Cần đánh giá riêng chất lượng **kho tri thức** và **phần mềm**. Không coi số lượng từ lớn là thước đo đúng duy nhất.

| Tiêu chí | Phương pháp đo | Mục tiêu tham khảo cho MVP |
|---|---|---|
| Độ đúng quan hệ | Lấy mẫu quan hệ và kiểm duyệt độc lập | Precision ≥90% trên mẫu đánh giá |
| Chất lượng định nghĩa | Thang điểm rõ nghĩa/chính xác/không vòng vo | ≥90% mục được duyệt đạt yêu cầu |
| Phrase matching | Precision, Recall, F1 so với gold span | F1 ≥85% trên tập thử được định nghĩa trước |
| Coverage | Tỷ lệ các cụm trong corpus mục tiêu nhận diện được | Báo cáo theo miền; chưa áp ngưỡng chung |
| Provenance | Kiểm tra mục approved có nguồn hợp lệ | 100% quan hệ/định nghĩa công bố có nguồn |
| Đa nghĩa | Bộ kiểm thử “đường”, “mạng”, “đá”... | Không gộp sai nghĩa trong gold set |
| Kiểm thử kỹ thuật | pytest, import/export round-trip | Không lỗi trong bộ test bắt buộc |

**Cách tổ chức gold set:** lấy mẫu phân tầng theo từ đơn/cụm từ, lĩnh vực, đa nghĩa và loại quan hệ; gán nhãn thủ công bởi ít nhất hai người cho một tập con; ghi tỷ lệ đồng thuận và quy tắc hòa giải. Ngưỡng trên là mục tiêu dự kiến, cần hiệu chỉnh theo dữ liệu thực tế.

## 9. Hướng tích hợp Emotionet với LSTM/xLSTM

Tích hợp được đề xuất theo ba mức tăng dần:

1. **Lexicon features:** bổ sung cờ hiện diện thuật ngữ/cảm xúc, loại khái niệm hoặc thống kê số lần khớp vào vector đặc trưng; cần tránh rò rỉ nhãn.
2. **Phrase-aware input:** bảo toàn cụm thuật ngữ khi tiền xử lý hoặc sử dụng embedding riêng cho cụm; kiểm tra ảnh hưởng đến tokenizer và từ vựng.
3. **Concept-aware representation:** ánh xạ span sang concept ID rồi kết hợp biểu diễn khái niệm với mô hình học sâu; cần cơ chế xử lý đa nghĩa.

**Thiết kế đối chứng tối thiểu:** cùng một tập train/validation/test; cùng seed và ngân sách; so sánh baseline LSTM/xLSTM với các phiên bản có/không có Emotionet; báo cáo Macro-F1, F1 từng lớp, chênh lệch ghép cặp và thời gian suy luận. Không chọn quy tắc hay từ điển bằng cách nhìn điểm test.

## 10. Rủi ro và giải pháp

| Rủi ro | Hậu quả | Biện pháp |
|---|---|---|
| Từ đa nghĩa bị gộp | Quan hệ sai và truy vấn không chính xác | Sense ID độc lập, ví dụ đối chứng, review |
| Trích xuất quan hệ sai | Đồ thị chứa thông tin không đáng tin | Lưu evidence, trạng thái candidate/approved, audit |
| Vi phạm giấy phép dữ liệu | Không thể công bố hoặc tái phân phối | Registry nguồn và quyền sử dụng, loại bỏ nguồn chưa rõ |
| Phủ ít thuật ngữ chuyên ngành | Coverage thấp | Bổ sung corpus theo miền, đo coverage theo tập |
| Gán cảm xúc máy móc | Tăng nhiễu cho mô hình phân loại | Lớp cảm xúc tùy chọn, lưu ngữ cảnh và mức tin cậy |
| Mô hình lớn/chi phí cao | Khó triển khai | Bắt đầu bằng rule-based + SQLite, tối ưu sau |
| Đánh giá thiên lệch | Kết luận không đáng tin | Gold set độc lập, giữ test cuối, báo cáo sai số |

## 11. Nhân sự và quản lý công việc

- **Kỹ thuật dữ liệu (có thể kiêm nhiệm):** xây schema, import/export, chuẩn hóa và kiểm tra nguồn.
- **Lập trình thư viện:** API, matcher, test, đóng gói Python, CI.
- **Kiểm duyệt ngữ nghĩa:** định nghĩa, phân biệt nghĩa, quan hệ, chuẩn cảm xúc.
- **Nghiên cứu đánh giá:** gold set, chỉ số chất lượng, ablation NLP và báo cáo.

Dùng GitHub Issues hoặc bảng công việc tương đương. Mỗi thay đổi dữ liệu cần PR và kiểm tra tự động: JSON schema, ID trùng, tham chiếu đích tồn tại, tính hợp lệ của quan hệ và giấy phép.

## 12. Deliverables và checklist bàn giao

- [ ] `emotionet` cài được bằng `pip install -e .`.
- [ ] Kho SQLite có thể xuất/nhập JSONL và không làm mất ID hoặc nguồn.
- [ ] API tra cứu từ đơn, cụm từ, đa nghĩa và các quan hệ cơ bản hoạt động.
- [ ] Bộ matcher nhận diện được “trí tuệ nhân tạo”, “động vật có vú”, “học máy” trong văn bản.
- [ ] Có ≥300 khái niệm được duyệt (mục tiêu MVP), kèm bằng chứng/giấy phép hợp lệ.
- [ ] Có gold set và báo cáo precision/recall/F1 cho phrase matching, precision quan hệ.
- [ ] Có bộ kiểm thử tự động, tài liệu API, ví dụ chạy và changelog.
- [ ] Có chính sách phiên bản hóa dữ liệu, sửa lỗi và tiếp nhận đóng góp.
- [ ] Có thiết kế thí nghiệm downstream; chưa tuyên bố Emotionet cải thiện LSTM/xLSTM khi chưa đo.

## 13. Nguồn tham khảo và định hướng nghiên cứu

Các nguồn sau dùng để nghiên cứu mô hình dữ liệu và phương pháp; việc lấy dữ liệu cần kiểm tra điều kiện sử dụng thực tế của từng nguồn:

1. Princeton WordNet — https://wordnet.princeton.edu/
2. ConceptNet — https://conceptnet.io/
3. BabelNet — https://babelnet.org/
4. W3C OntoLex-lemon, Lexicon Model for Ontologies — https://www.w3.org/2016/05/ontolex/
5. VnCoreNLP (công cụ xử lý ngôn ngữ tiếng Việt) — https://github.com/vncorenlp/VnCoreNLP
6. Wikidata (tham khảo mô hình khái niệm và định danh) — https://www.wikidata.org/

---

**Khuyến nghị triển khai:** Làm chắc **LexicalEntry – Sense – Concept – Relation – Evidence** trước, xây lớp cảm xúc sau. Đây là nền tảng cho một thư viện có thể mở rộng đến từ điển ngữ nghĩa tổng quát mà không bị giới hạn trong bài toán cảm xúc.
