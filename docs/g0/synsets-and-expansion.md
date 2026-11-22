# Synset khởi đầu và mở rộng ứng viên bằng embedding

Ngày thực hiện: 21/11/2026. Đầu vào là bản seed v2 của chủ dự án, 10 nghĩa tách đã
duyệt và sáu quyết định ngữ cảnh đã chốt. Các bản review của nhóm vẫn chỉ tham khảo.

## Bộ synset đã tạo

- **66 entry, 71 sense, 71 synset khởi đầu**, phủ 27 nhãn cảm xúc. Năm entry đa nghĩa
  được thay bằng 10 sense đã duyệt: `66 - 5 + 10 = 71`; không giữ thêm nghĩa tổng
  hợp của năm entry đó để tránh đếm hai lần.
- Mỗi synset ban đầu có một sense thành viên. Chưa có quyết định duyệt tương đương
  giữa các lemma, nên không tự gộp từ chỉ vì cùng nhãn cảm xúc hoặc gần vector.
- **5 đề nghị gộp** được soạn riêng: yêu–thương/love, nhẹ nhõm–nhẹ lòng,
  đồng tình–tán thành, nhận ra–vỡ lẽ, lo/nervousness–lo lắng. Đây là giả thuyết đối
  chiếu định nghĩa cần duyệt, chưa phải nhóm đồng nghĩa đã được xác nhận.
- Giữ nguyên nghĩa và nhãn đã duyệt, bao gồm những nghĩa có nhiều nhãn. POS chưa
  được duyệt để null; không tự gán cường độ/confidence. Bằng chứng tách riêng
  review nghĩa và gán nghĩa theo ngữ cảnh; nhãn câu không biến thành nhãn sense.
- Schema `emotionet_research_seed_synsets_v1` là bản dữ liệu nghiên cứu cho lớp
  cảm xúc; không thay thế hoặc tự migrate bộ fixture G0 tổng quát ban đầu. ID synset
  ổn định theo sense ID; gộp nghĩa sau này cần lưu ánh xạ và lịch sử riêng.

Các file dùng trực tiếp:

| File | Nội dung |
|---|---|
| [synsets.jsonl](../../data/local/seed-synsets-v1/synsets.jsonl) | 71 định nghĩa và danh sách sense thành viên |
| [senses.jsonl](../../data/local/seed-synsets-v1/senses.jsonl) | Nghĩa, nhãn, entry/synset ID, bằng chứng |
| [entries.jsonl](../../data/local/seed-synsets-v1/entries.jsonl) | 66 lemma cùng sense ID |
| [evidence.jsonl](../../data/local/seed-synsets-v1/evidence.jsonl) | Nguồn quyết định nghĩa và ngữ cảnh |
| [merge-proposals.csv](../../data/local/seed-synsets-v1/merge-proposals.csv) | 5 cặp đề nghị gộp; decision đang trống |
| [manifest.json](../../data/local/seed-synsets-v1/manifest.json) | Số lượng, nguồn và hash từng file |

## Lượt mở rộng đã chạy

Huấn luyện **Word2Vec Skip-gram với negative sampling** trên text của **16.531 câu
train ViGoEmotions**, không dùng nhãn câu và không đọc validation/test. Tách từ bằng
PyVi, giữ dấu, chuẩn hóa Unicode NFC; giữ chữ hoa khi tách từ rồi casefold token.
Cụm seed nhiều token được ghép theo chuỗi token dài nhất trước khi bỏ dấu câu;
không ghép xuyên dấu câu. Có thể vẫn có lỗi tách từ/tên riêng nên cần rà câu ví dụ.

Word2Vec tạo vector tĩnh cho từ/cụm từ; PyVi cung cấp tách từ tiếng Việt. Tham khảo
[tài liệu Word2Vec của Gensim](https://radimrehurek.com/gensim/models/word2vec.html)
và [mã nguồn, hướng dẫn PyVi](https://github.com/trungtv/pyvi).

Cấu hình trong [embedding-expansion.json](../../configs/embedding-expansion.json):
100 chiều, cửa sổ 5, 15 epoch, negative=10, min_count=2, seed=42, một worker.
PYTHONHASHSEED=0 và hàm hash SHA-256 được cố định khi khởi tạo; phiên bản thư viện
được ghi trong manifest và [requirements-lexicon.txt](../../requirements-lexicon.txt).
Tái lập nên dùng cùng môi trường; không khẳng định bitwise giống nhau trên mọi máy.

Sau tách từ có **219.045 token**, vocabulary mô hình **7.102 token**. Truy vấn chỉ
dùng anchor xuất hiện ít nhất ba lần; ứng viên phải xuất hiện ít nhất năm lần,
không trùng 66 seed hiện có, không thuộc danh sách từ chức năng và tối đa bốn âm tiết.

Vector truy vấn là trung bình anchor chuẩn hóa được kết hợp với vector các từ nội
dung trong gloss: 75% anchor, 25% gloss, rồi chuẩn hóa. Ngưỡng cosine với truy vấn
là 0,50 và với anchor là 0,45; giữ tối đa năm ứng viên/synset. **Ngưỡng pilot chưa
được hiệu chỉnh**, cosine không phải confidence hoặc bằng chứng đồng nghĩa.
Gloss giúp định hướng truy vấn nhưng không phải mô hình WSD hay vector nghĩa được
huấn luyện riêng. Hai sense cùng lemma vẫn dùng cùng vector anchor ban đầu.

Kết quả:

- **48 synset được truy vấn, 23 synset bỏ qua** do anchor không đủ số lần xuất hiện
  sau tách từ hoặc không có trong vocabulary. Không tạo vector giả cho mục vắng mặt.
- **240 cặp ứng viên–synset**, gồm **166 từ/cụm từ khác nhau**. Một ứng viên có thể
  được đề nghị cho nhiều nghĩa; chưa tự chọn nghĩa, quan hệ hoặc nhãn của ứng viên.
- **0 thành viên mới được tự động kết nạp**. Corpus train nhỏ và informal tạo cả
  từ gần nghĩa lẫn từ cùng chủ đề, tiếng đệm, tên riêng hoặc từ trái nghĩa. Ví dụ
  pilot truy vấn “buồn cười” đưa cả “tủi thân” vào hàng chờ: điểm cao không đủ để gộp.

| File | Cách dùng |
|---|---|
| [candidate-review.csv](../../data/local/embedding-expansion-v1/candidate-review.csv) | Bảng 240 đề xuất, cosine, tần suất, câu ví dụ và ID train |
| [candidates.jsonl](../../data/local/embedding-expansion-v1/candidates.jsonl) | Đầy đủ tối đa hai câu ví dụ/ứng viên; mọi nhãn ứng viên còn rỗng |
| [query-audit.jsonl](../../data/local/embedding-expansion-v1/query-audit.jsonl) | Anchor, từ gloss và lý do bỏ qua từng synset |
| [word-vectors.kv](../../data/local/embedding-expansion-v1/word-vectors.kv) | Vector Gensim KeyedVectors đã kiểm tra lưu/nạp lại |
| [manifest.json](../../data/local/embedding-expansion-v1/manifest.json) | Cấu hình, thư viện, hash corpus/model và thống kê |

Các ví dụ là hai dòng train đầu tiên chứa token sau tách từ, **chưa được duyệt là
ví dụ đúng nghĩa ứng viên**. Lượt này dùng train đầy đủ để khám phá; khi đánh giá GA
với chia fold nội bộ, cần fit lại trên inner-train tương ứng bằng `--train-ids`,
không tái dùng vector fit toàn bộ train để coi điểm inner-validation là độc lập.

## Biên soạn tiếp trên kết quả

1. Rà năm cặp trong `merge-proposals.csv`, điền accept/reject/needs_evidence,
   reviewer, reviewed_at và lý do. Chỉ accept khi định nghĩa và phạm vi tương đương,
   không chỉ cùng nhóm cảm xúc.
2. Với `candidate-review.csv`, điền decision, relation (`synonym`, `related`,
   `antonym` hoặc `unrelated`), candidate_gloss, reviewed_emotions, reviewer,
   reviewed_at và notes. Cùng ngữ cảnh hoặc cùng chủ đề chỉ đủ gợi ý related.
3. Chỉ đề xuất thêm thành viên cùng synset khi quan hệ synonym và nghĩa ứng viên
   đã được chốt. Quan hệ khác cần bản ghi riêng. Không dùng các đề xuất còn trống
   làm seed cho vòng mở rộng tiếp theo.

## Chạy lại vào thư mục mới

```powershell
python scripts/build_seed_synsets.py --output data/local/seed-synsets-v2
$env:PYTHONHASHSEED='0'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python scripts/expand_synsets_embeddings.py --train 'D:\NCKH_GA+LSTM_Emotion_Recognition\data_external\ViGoEmotions\train.csv' --synsets data/local/seed-synsets-v2 --output data/local/embedding-expansion-v2
python -m unittest discover -s tests
```

Hai công cụ từ chối ghi đè, chỉ xuất dữ liệu chi tiết trong `data/local/` đã được
gitignore. Bản sao đầu vào và hash giúp truy nguồn; trạng thái quyền phát hành vẫn
`not_cleared`. Việc tạo synset và chạy pilot không tự hoàn thành mọi tiêu chí G0.
