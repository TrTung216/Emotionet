# Chọn seed từ NRC và VnEmoLex

Ngày kiểm tra: 20/11/2026. Đã chuẩn bị 66 biểu thức đề xuất cho 27 nhãn cảm xúc
ViGoEmotions để người dùng duyệt. Có 62 biểu thức khớp chuỗi trong ít nhất một
nguồn, trong đó 40 xuất hiện ở cả hai.

## Quyết định chọn bản chính

Cập nhật 21/11/2026: đã [tạo 71 synset khởi đầu và chạy mở rộng ứng viên bằng
embedding](synsets-and-expansion.md). Các phần phía dưới ghi lại lịch sử review;
bộ seed v2 và các quyết định đã chốt tiếp tục là nguồn dữ liệu chính.

Ngày 20/11/2026, chủ dự án yêu cầu **“giữ bản của tôi”**. Bản chính được chọn là
[seed v2 gồm 66 mục](../../data/local/reviewed-seeds-v2/accepted-seeds.jsonl), giữ
nguyên nhãn, nghĩa và quyết định review. Review của Tâm và Hoàng chỉ dùng tham khảo;
không cần hoàn thành bảng phân xử 21 mục để tiếp tục dự án. Lựa chọn được ghi tại
[seed-selection.json](../../configs/seed-selection.json).

Đây là quyết định chọn phiên bản, không phải tuyên bố nhóm đã đồng thuận hoặc một
vòng duyệt nghĩa mới. Giữ nguyên reviewer, ngày duyệt và loại bằng chứng trong v2;
“hụt hẫng” tiếp tục là seed dựa trên định nghĩa duyệt thủ công và ví dụ tự soạn.

## Đã nhập quyết định cuối cho sáu mục chất lượng

Người dùng đã cập nhật đủ quyết định, sense ID, context flags, lý do, reviewer và
thời điểm duyệt cho sáu dòng trong `quality-review-queue.csv`. Các quyết định đã
khớp với `match-review-samples.csv`; ghi chú ở bảng mẫu là bản rút gọn, bản giải
trình đầy đủ được giữ riêng. Đã kiểm tra tham chiếu sense, ID/text train và 149
dòng ngoài hàng chờ không đổi. Giữ nguyên bộ seed v2 và 10 nghĩa đã chọn.

- [Snapshot review mới](../../data/local/sense-match-review-v2/summary.json):
  **143 matches_sense, 8 wrong_sense, 4 uncertain trên 155 cặp từ–câu/148 câu**.
- [Sáu quyết định ngữ cảnh](../../data/local/quality-resolution-v1/resolved-contexts.jsonl):
  lưu sense ID, nhãn sense, nhãn toàn câu, context flags, hai bản ghi chú,
  `reviewer=antigravity`, `reviewed_at=2026-11-20T23:05:00+07:00` như nguồn.
- [Kiểm tra nguồn và hash](../../data/local/quality-resolution-v1/summary.json).

Sáu mục được đóng ở trạng thái **resolved_as_submitted**. Không đổi quyết định
thay người duyệt, không tự nâng các nhãn ngữ cảnh thành gold WSD. Thời điểm review
được giữ đúng như người dùng ghi, tách riêng thời điểm nhập.

Hai điểm cần diễn đạt chính xác khi dùng kết quả:

1. Sense “ghét” **s1 = disgust**, **s2 = anger**, giữ nguyên registry đã duyệt.
   Câu 3531 có nhãn toàn câu disgust/annoyance, nhưng s1 không vì vậy tự thêm
   annoyance. Câu tik012211 có nhãn toàn câu remorse/annoyance/disgust, **không có
   anger**; chọn s2 là quyết định duyệt nghĩa, không phải anger được nhãn câu xác
   nhận. Không đổi s2 thành anger/disgust theo chú thích rút gọn trong bảng mẫu.
2. “Buồn” ở 1004 được người duyệt loại theo cách diễn giải ngữ cảnh phủ định mức
   độ/mỉa mai. Nhãn câu không có sadness không chứng minh từ “buồn” đã đổi nghĩa,
   cũng không đủ chứng minh người nói hoàn toàn không buồn. Lưu `degree_negation`
   riêng; `wrong_sense` ở dòng này phản ánh quyết định loại ngữ cảnh của bản review,
   không được dùng như chứng cứ nghĩa từ vựng sai trong bộ gold WSD.

Các tỷ lệ 92,3% / 5,2% / 2,6% chỉ mô tả nhãn review trên mẫu ba câu đầu mỗi seed,
không phải precision/accuracy của hệ thống. Sự trùng nhãn câu và nhãn sense chỉ là
đối chiếu hai cấp chú thích; không chứng minh một từ riêng lẻ mang mọi nhãn câu.
Hàng chờ sáu mục không còn là điều kiện cần hoàn thành trước bước tạo synset.

## Lịch sử: nhập kết quả duyệt 10 nghĩa và 155 lượt khớp lần đầu

Đã xác minh hai CSV local được cập nhật: 10/10 dòng nghĩa có `decision=accept`,
`reviewer=antigravity`; 155 dòng mẫu đều đã điền quyết định và ghi chú. Tạo snapshot
[sense-match-review-v1](../../data/local/sense-match-review-v1/summary.json), lưu
bản gốc nguyên byte, nội dung người dùng gửi, hash, lịch sử nhập và
[10 nghĩa được chấp nhận](../../data/local/sense-match-review-v1/accepted-split-senses.jsonl).
Giữ nguyên status cũ trong CSV nguồn; bản xuất ghi `accepted_as_submitted` theo
decision mới. Không suy ngày review từ ngày nhập; reviewer/ngày review của từng
lượt khớp chưa có trong schema nguồn nên để null trong lịch sử nhập.

Đã tạo lại mẫu từ seed v2 và **train**, đối chiếu đủ cặp seed ID/dataset ID, term,
text, split và cách chọn mẫu: tất cả khớp, chỉ hai cột review thay đổi.
**155 lượt khớp thuộc 148 câu khác nhau**, vì một câu có thể khớp nhiều seed.
Phân bố được ghi nhận đúng theo CSV: 144 matches_sense (92,9%), 7 wrong_sense
(4,5%), 4 uncertain (2,6%). Đây là tỷ lệ đánh dấu trên mẫu lấy tối đa ba câu đầu
cho mỗi seed, không phải precision/accuracy trên corpus hay tập đánh giá độc lập.

Hai lỗi nhất quán cần xử lý:

| Mục | CSV hiện tại | Vấn đề |
|---|---|---|
| tiếc — x001421 | wrong_sense | Câu nói về tiếc nuối, nhưng notes lại nói nhận diện danh tính “nhận ra tôi”; ghi chú không thuộc dòng này |
| nhận ra — 28036 | matches_sense | Câu “đừng ai nhận ra toi” là nhận diện; nội dung tổng kết của người dùng cũng ghi wrong_sense, trái CSV |

Không tự chuyển ghi chú hoặc đổi quyết định thay người duyệt. Hai dòng được lưu
cùng bốn mục cần rà ngữ nghĩa trong
[quality-review-queue.csv](../../data/local/sense-match-quality-v1/quality-review-queue.csv).
Điền `final_sense_match_decision`, `final_sense_id` nếu xác định được, `context_flags`,
`resolution_notes`, `reviewer`, `reviewed_at`. Bốn mục rà thêm:

- **buồn — 1004:** “đéo đến mức buồn quá” có thể phủ định mức độ; từ vẫn dùng nghĩa
  buồn. Cần tách khớp nghĩa từ vựng khỏi phủ định/mức độ và cảm xúc người nói; không
  suy đây là phủ định hoàn toàn sadness hoặc nghĩa từ khác.
- **ghét — 3531:** “per ghét ghê bây” thiếu cơ sở chọn s1 hay s2; ghi chú “s1/s2”
  chưa giải nghĩa ngữ cảnh. Nhãn annoyance trong bản tổng kết không nằm trong hai
  sense disgust/anger đã duyệt cho từ này.
- **ghét — 20431:** không thích ăn trân châu chưa đủ để khẳng định ghê tởm/disgust.
- **ghét — tik012211:** cần xác nhận nghĩa của ghét bản thân trong ngữ cảnh hối hận;
  không suy anger chỉ từ việc có từ ghét. Đây là yêu cầu rà thêm, không phải tự bác nhãn.

Một số ID trong văn bản tổng kết bị lệch; ID đúng theo CSV và train:

| Ngữ cảnh được trích | ID trong tổng kết | ID đúng |
|---|---|---|
| phẫn nộ — lấy nick clone bấm reaction | 16554 | 4574 |
| phẫn nộ — những người thả phẫn nộ | 3475 | 1924 |
| đồng tình — Kỳ Đồng tình cảm thế | tik000067 | 24877 |
| thất vọng — bạn trai người khác không bao giờ… | 2598 | 508 |

[Bảng sửa tham chiếu](../../data/local/sense-match-quality-v1/summary-id-corrections.csv)
lưu nguyên văn câu để truy xuất. Trường hợp uncertain thứ tư chưa liệt kê trong
tổng kết là **hạnh phúc — 31057**. Phân loại reaction/tên tác phẩm cũng cần lưu
ngữ cảnh sử dụng: một lượt nhắc đến reaction hoặc tiêu đề không tự xác nhận hay
phủ định cảm xúc của người nói.

Việc tách 10 nghĩa giúp định nghĩa rõ các lựa chọn nhưng **chưa giải quyết chọn
nghĩa theo câu**. Một nhãn hạt nhân cho mỗi nghĩa ở vòng này là quyết định thiết kế
cục bộ, không phải quy tắc cấm đa nhãn cho mọi nghĩa trong dự án. Giữ nguyên 66 seed
v2 của chủ dự án; chưa tạo synset tự động hoặc dùng 144 matches_sense làm gold.

## Lịch sử đối chiếu review của Tâm và Hoàng — chỉ tham khảo

Đã đối chiếu hai file `seed-review(tam).csv` và `seed-rw(Hoang).csv`, mỗi file 66 mục,
với bảng gốc và bản v2. ID, từ và thông tin nguồn khớp; khác biệt TRUE/True do cách
ghi boolean được coi là tương đương. Bản sao nguyên byte và hash được lưu local.

| Người duyệt trong file | accept | revise | reject | needs_evidence |
|---|---:|---:|---:|---:|
| Phan Giang Tâm | 53 | 0 | 1 | 12 |
| Hoàng | 50 | 12 | 0 | 4 |

**45 mục** được cả hai accept với cùng bộ nhãn như v2; **20 mục** cần phân xử vì
chưa cùng chấp nhận/còn khác nhãn; **1 mục “yêu thương”** được cả hai accept với
`love`, khác `love;caring` trong v2. Đối chiếu tạo **21 mục trong hàng chờ phân xử**;
hàng chờ này hiện chỉ được lưu tham khảo theo quyết định chọn bản v2 ở trên.
45 mục còn lại trùng quyết định và nhãn; so sánh này không xác nhận nghĩa tương đương.

Hai người trùng quyết định ở 51/66 mục, trùng tập nhãn ở 56/66 mục và trùng cả hai
ở 48/66 mục. So sánh nhãn bỏ qua thứ tự. Những con số này không chứng minh các
định nghĩa tương đương hoặc các vòng review độc lập; v2 không được tính là phiếu
thứ ba. Không tự hợp nhãn hay quyết định theo đa số.

- [Bảng đối chiếu đủ 66 mục](../../data/local/team-seed-review-v1/comparison.csv).
- [Bảng phân xử 21 mục](../../data/local/team-seed-review-v1/adjudication-queue.csv).
- [Thống kê, hash và nguồn đầu vào](../../data/local/team-seed-review-v1/summary.json).

Nếu mở lại vòng phân xử trong tương lai, người phân xử điền `final_decision`, `final_emotions` (ngăn cách bằng `;`),
`final_gloss`, `adjudicator`, `adjudicated_at` (có múi giờ) và `resolution_notes`.
Các cột `review_a_*` là bản Tâm, `review_b_*` là bản Hoàng; giữ nguyên để truy vết.
Nếu quyết định khác v2, ghi lý do và nghĩa được giữ/loại. Chưa có quyết định cuối
nào được tự điền; bộ seed v2 được chọn làm bản chính theo yêu cầu của chủ dự án.

Các điểm khác biệt lưu tham khảo:

1. **Hài hước, đau thương:** chốt phạm vi từ điển có bao gồm từ tả sự việc/tính chất
   gợi cảm xúc hay chỉ trạng thái cảm xúc của chủ thể. Nếu giữ cả hai, cần phân biệt
   loại nghĩa khi tạo đặc trưng, không coi mọi lần khớp là cảm xúc người nói.
2. **Thích thú, bối rối, hoang mang, tiếc, nản, ghê sợ, ghét, đau buồn:** chốt nhãn
   theo nghĩa/ngữ cảnh, không gộp mọi nhãn mà mỗi người đang cân nhắc.
3. **Thương, quan tâm, nhận ra, lo, tức, khó chịu:** phân biệt khác biệt trạng thái
   accept/revise với khác biệt phạm vi nghĩa. “Khó chịu” cùng chọn annoyance và
   loại nghĩa thể chất; “lo” cùng đề xuất nervousness, “tức” cùng đề xuất anger.
   Các ghi chú vẫn cần đối chiếu trước khi chốt các sense trong bản nháp tách nghĩa.
4. **Lo lắng cho, nhẹ lòng, vỡ lẽ, hụt hẫng:** xem bằng chứng đã có bên dưới.
5. **Yêu thương:** xác nhận đề nghị cùng bỏ caring, chỉ giữ love, hoặc tách sense
   nếu nhóm muốn giữ nghĩa chăm sóc riêng.

Bằng chứng đã xác minh nằm ở
[verified-train-evidence.jsonl](../../data/local/seed-analysis-v2/verified-train-evidence.jsonl):
“nhẹ lòng” có ba câu `3276`, `you001630`, `you002139`, đều có relief;
“vỡ lẽ” có `you003294` nhưng nhãn câu là remorse, nên realization vẫn là quyết định
duyệt nghĩa; “lo lắng cho” có `you001771` (nervousness/remorse/fear), còn caring
được minh họa bởi biến thể “lo cho” ở `24921`. “Hụt hẫng” chưa có câu train đã xác
minh; có thể giữ với bằng chứng thủ công nếu nhóm chấp nhận chính sách này.
Không tự đổi needs_evidence thành accept thay người duyệt chỉ vì tìm được câu.

Cả hai bản để trống `reviewed_at` ở toàn bộ 66 mục. Đã giữ nguyên, không suy ngày
duyệt từ thời điểm gửi file. Nhóm bổ sung thời điểm nếu có thể xác nhận; lịch sử cần
phân biệt ngày review với ngày nhập. Bảng so sánh này chưa được nhập bằng bộ nhập
review chính thức vốn yêu cầu thời điểm duyệt có múi giờ.

```powershell
python scripts/compare_seed_reviews.py --review-a 'C:\Users\ADMIN\Downloads\seed-review(tam).csv' --review-b 'C:\Users\ADMIN\Downloads\seed-rw(Hoang).csv' --output data/local/team-seed-review-v2
```

## Bộ seed v2 và bước tiếp theo

Đã nhập bản cập nhật do người dùng gửi: **66 accept**, phủ đủ 27 nhãn cảm xúc.
[Bộ seed v2](../../data/local/reviewed-seeds-v2/accepted-seeds.jsonl) và lịch sử review
được lưu trong snapshot mới; lần nhập này không sửa v1. Kiểm tra phát hiện bảng
`pending-review.csv` của v1 đã có các quyết định accept và khác hash lúc tạo v1;
các file v1 còn lại vẫn khớp hash. V2 dùng bản người dùng gửi đã xác minh, toàn bộ
file v2 khớp manifest. `accept` ghi nhận quyết định về nội dung
của bản review; chưa đồng nghĩa với việc mọi sense đều đã có bằng chứng corpus.

[Hồ sơ bằng chứng](../../data/local/seed-analysis-v2/evidence-profiles.jsonl) phân biệt:
62 mục có ghi nhận NRC/VnEmoLex; ba mục mới có câu train đã xác minh (“lo lắng cho”,
“nhẹ lòng”, “vỡ lẽ”); “hụt hẫng” dựa trên định nghĩa duyệt thủ công và ví dụ tự soạn.
Bằng chứng caring cho “lo lắng cho” thuộc biến thể “lo cho”; câu chứa “vỡ lẽ” có nhãn
toàn câu remorse, không phải realization. Nhãn từ vựng giữ theo quyết định duyệt nghĩa.
Các câu đã đối chiếu có ID và nội dung gốc tại
[verified-train-evidence.jsonl](../../data/local/seed-analysis-v2/verified-train-evidence.jsonl).

Đã chạy khớp bề mặt chỉ trên **train**: chuẩn hóa NFC, chữ thường, khoảng trắng và
ranh giới từ Unicode; giữ cả số đếm thô lẫn số đếm ưu tiên cụm dài, không chồng lấn.
**60/66 seed xuất hiện; 3.036/16.531 câu có ít nhất một seed (18,37%).**
Sáu seed chưa xuất hiện là phấn khích, cảm kích, sửng sốt, ngượng ngùng, hụt hẫng,
không tán thành. Vắng mặt trong train không tự phủ định nghĩa từ vựng của seed.

- [Độ phủ theo seed](../../data/local/seed-coverage-v2/coverage-by-seed.csv).
- [Câu mẫu để rà nghĩa khớp](../../data/local/seed-coverage-v2/match-review-samples.csv):
  tối đa ba câu đầu tiên khớp mỗi seed; điền `sense_match_decision` bằng
  `matches_sense`, `wrong_sense` hoặc `uncertain`, kèm ghi chú. Đây là mẫu kiểm tra
  lỗi, không phải tập ngẫu nhiên để ước lượng precision hay bộ gold độc lập.
- [Bảng tách nghĩa đã được điền accept](../../data/local/seed-analysis-v2/sense-split-review.csv):
  10 sense cho thương, lo, tiếc, ghét, lo lắng cho; đã nhập vào snapshot mới phía trên.
  Cột status gốc còn needs_review được giữ để truy vết, decision mới là accept.
  Nhãn kép chỉ nên cùng tồn tại trên
  một sense khi người duyệt xác nhận chúng cùng mô tả nghĩa đó.

Thứ tự thực hiện tiếp:

1. Rà câu khớp và chốt ranh giới sense; ưu tiên các từ ngắn, đa nghĩa như lo, thương,
   tức, ghét. Từ có chung nhãn cảm xúc không tự động là từ đồng nghĩa.
2. Tạo synset từ những sense tương đương, lưu quan hệ và nguồn; không gom cả nhóm
   anger hoặc sadness thành một synset lớn.
3. Mở rộng ứng viên bằng embedding trên train/corpus độc lập, giữ ứng viên trong
   hàng chờ. Chưa đưa kết quả mở rộng tự động vào seed được duyệt.
4. Khi lớp dữ liệu đã ổn định, xây matcher và đặc trưng từ điển; so sánh xLSTM với
   xLSTM + đặc trưng cố định trước khi cho GA chọn nhóm đặc trưng.

Độ phủ ở trên chưa xử lý phủ định, mỉa mai, đa nghĩa hoặc cường độ. Không khớp seed
không có nghĩa là neutral. Script không đọc validation/test và không gán nhãn dự đoán.

```powershell
python scripts/audit_seed_coverage.py --train 'D:\NCKH_GA+LSTM_Emotion_Recognition\data_external\ViGoEmotions\train.csv' --output data/local/seed-coverage-v3
python -m unittest discover -s tests
```

## Lịch sử: kết quả nhập bản review v1

Đã nhập `seed-review-completed.csv` do người dùng xác nhận là bản đã review:
**55 accept, 7 revise, 4 needs_evidence, 0 reject**. Cả 66 ID và các cột nguồn/gợi ý
đều khớp bảng gốc. Giữ nguyên `reviewer=antigravity` và thời điểm duyệt từ CSV;
việc nhập không chứng nhận một vòng kiểm duyệt độc lập khác.

- [55 seed chấp nhận về nội dung](../../data/local/reviewed-seeds-v1/accepted-seeds.jsonl)
  phủ đủ 27 nhãn cảm xúc ViGoEmotions. Một mục có thể có nhiều nhãn; đây chưa phải
  55 synset và chưa có nhóm đồng nghĩa được tự động tạo.
- [11 mục còn cần xử lý](../../data/local/reviewed-seeds-v1/pending-review.csv)
  giữ nguyên quyết định, nhãn và ghi chú để tiếp tục chỉnh lý.
- [Lịch sử 66 quyết định](../../data/local/reviewed-seeds-v1/review-events.jsonl)
  lưu dòng gốc, dòng review, hash CSV và thời điểm nhập.
- [Thống kê và hash snapshot](../../data/local/reviewed-seeds-v1/summary.json)
  cho phép kiểm tra đầu vào và từng file đầu ra. Snapshot chứa bản sao nguyên byte
  của CSV đã review, bảng gốc, bằng chứng, taxonomy và thống kê nguồn.

Các mục `revise`: **buồn cười, thương, lo, tiếc, ghét, tức, khó chịu**. Cần chốt nghĩa
được giữ và tách nghĩa khi cần trước khi đổi thành `accept`. Riêng “khó chịu”, cột
nhãn ghi `annoyance;disgust` nhưng ghi chú yêu cầu giữ nghĩa tâm lý cho `annoyance`;
bộ nhập giữ nguyên mâu thuẫn này trong hàng chờ, không tự chọn nhãn thay người duyệt.

Các mục `needs_evidence`: **lo lắng cho, nhẹ lòng, vỡ lẽ, hụt hẫng**. Bổ sung câu có
nguồn truy xuất được từ tập train hoặc corpus độc lập; ví dụ tự soạn trong ghi chú
không tự trở thành bằng chứng corpus. Không khai thác validation/test để mở rộng seed.

Seed xuất ra có `semantic_status=accepted`, `publication_status=not_cleared`;
không suy ra intensity/confidence từ cờ nguồn. Nhãn cuối lấy từ `reviewed_emotions`,
không lấy từ gợi ý hoặc phép hợp nhãn NRC/VnEmoLex. Quyết định review nội dung không
thay đổi quyền phát hành nguồn. Toàn bộ dữ liệu chi tiết tiếp tục nằm trong `data/local/`.

Chạy lại vào thư mục mới khi có bản review cập nhật:

```powershell
python scripts/import_seed_review.py --review data/local/seed-review-check-v2/submitted-review.csv --output data/local/reviewed-seeds-v3
python -m unittest discover -s tests -p 'test_import_seed_review.py'
```

Công cụ yêu cầu đủ ID của bảng gốc và chỉ cho sửa sáu cột review bên dưới. Muốn thêm
biểu thức mới, cần tạo bảng ứng viên và bằng chứng tương ứng ở vòng chuẩn bị tiếp theo.

## File cần mở để duyệt

Mở [seed-review.csv](../../data/local/seed-review-v1/seed-review.csv) bằng Excel.
File dùng UTF-8 có BOM để hiển thị tiếng Việt. Mỗi dòng là một biểu thức cần xét
nghĩa; các cột cần điền là:

| Cột | Nội dung người duyệt điền |
|---|---|
| decision | accept / revise / reject / needs_evidence |
| reviewed_emotions | Nhãn ViGoEmotions sau khi đối chiếu nghĩa; nhiều nhãn ngăn bằng dấu chấm phẩy |
| sense_gloss | Nghĩa cụ thể mà từ/cụm từ biểu đạt trong seed |
| reviewer | Người rà nội dung |
| reviewed_at | Thời điểm duyệt có múi giờ |
| notes | Ví dụ tự soạn hoặc tham chiếu nguồn được phép dùng; lý do sửa/loại |

`proposed_vigoemotions` là gợi ý do trợ lý soạn, không phải nhãn được nhập từ
NRC/VnEmoLex. Người duyệt có thể sửa hoặc bác bỏ. Đặc biệt rà các mục đa nghĩa như
thương, lo, tiếc, ghét, khó chịu. Một từ không nhất thiết thuộc duy nhất một nhãn.

`source_emotions_summary` chỉ gom tên nhóm có cờ 1 để tiện xem. Khi cần xét khác
biệt giữa các ghi nhận, xem [review-evidence.jsonl](../../data/local/seed-review-v1/review-evidence.jsonl):
mỗi dòng nguồn vẫn có từ gốc, từ tiếng Anh nếu có, locator và toàn bộ cờ 0/1/null.
Có 35 biểu thức mà các vector liên hệ khác nhau giữa các dòng nguồn hoặc giữa hai
bộ. Không lấy phép hợp những cờ này làm nhãn cuối cùng của seed.

Các biểu thức chưa tìm thấy bằng khớp chuỗi chuẩn hóa: **lo lắng cho, nhẹ lòng,
vỡ lẽ, hụt hẫng**. Chúng vẫn là đề xuất ngôn ngữ cần tìm bằng chứng, không phải mục
đã được hai nguồn xác nhận.

Việc điền `accept` là kết quả rà nội dung; chưa tự chuyển bản ghi thành approved
hoặc cấp quyền phát hành. Quy trình nhập quyết định đã có trong
`scripts/import_seed_review.py`; duyệt nguồn và tạo synset vẫn là các bước riêng.

## Hai file đã đọc

| Nguồn local | Dòng dữ liệu | Chuỗi khác nhau sau chuẩn hóa | Dòng có ít nhất một trong tám cờ cảm xúc bằng 1 |
|---|---:|---:|---:|
| NRC Vietnamese trong ZIP | 14.154 | 10.313 | 4.454 |
| VnEmoLex.xlsx | 10.627 | 10.626 | 4.414 |

Đây là số đếm từ hai file người dùng đã tải, không dùng tổng số trong bài giới
thiệu thay cho số liệu thực tế. Hai nguồn có 2.948 chuỗi chuẩn hóa giao nhau.

NRC Vietnamese chứa 3.841 dòng trùng chuỗi vượt quá lần đầu; 1.593 chuỗi có các
vector cờ khác nhau giữa các dòng. Điều này có thể liên quan đến nhiều từ tiếng
Anh cùng được dịch sang một chuỗi tiếng Việt hoặc các nghĩa khác nhau. Script
giữ các dòng riêng, không tự gộp sense hoặc synset.

VnEmoLex có một chuỗi trùng với vector cờ khác nhau và bốn ô nhãn trống trên bốn
dòng. Ô trống được giữ là null. Cột tổng hợp M không có tên được bỏ qua; công thức
trong cột này không được thực thi hoặc dùng làm điểm cảm xúc.

Hai bộ chứa cờ liên hệ 0/1 cho tám cảm xúc và positive/negative. Cờ 1 không phải
intensity=1 hoặc confidence=1. Nhiều mục là vật/sự kiện gợi liên tưởng cảm xúc,
không trực tiếp biểu đạt cảm xúc, nên không lấy tất cả làm seed.

## Nguồn gốc và giới hạn

- NRC: `C:/Users/ADMIN/Downloads/NRC-Emotion-Lexicon.zip`, thành viên
  `NRC-Emotion-Lexicon/OneFilePerLanguage/Vietnamese-NRC-EmoLex.txt`.
  README ghi phiên bản 0.92, bản dịch tự động tháng 8/2022; mục IX cho nghiên cứu
  phi thương mại/giáo dục và cấm tái phân phối dữ liệu.
- VnEmoLex: `C:/Users/ADMIN/Downloads/VnEmoLex.xlsx`, sheet Sheet1. Bản workbook
  chưa cung cấp điều kiện phân phối rõ ràng trong phần đã kiểm tra.
- Hash hai file nguồn và số liệu tổng hợp được lưu tại
  [seed-source-audit.json](../../reports/g0/seed-source-audit.json).
- Theo mô tả nguồn đã đối chiếu, VnEmoLex xây từ NRC và Viet WordNet. Không coi việc
  trùng ở hai nguồn là hai bằng chứng độc lập hoặc tự tăng confidence.
- Không tự ánh xạ anticipation/trust sang optimism/approval hoặc các nhãn chi tiết
  khác. Hai taxonomy cần đối chiếu bằng nghĩa và ví dụ.

Các file nguồn vẫn ở Downloads. Dữ liệu nhập và bảng review nằm dưới `data/local/`,
đã được `.gitignore` bỏ qua. Repo chia sẻ được mã xử lý, danh sách đề xuất tự soạn
và thống kê tổng hợp; bản nhập nguồn chưa phải từ điển được phép phát hành.

## Chạy lại

```powershell
python scripts/prepare_seed_review.py --nrc-zip 'C:\Users\ADMIN\Downloads\NRC-Emotion-Lexicon.zip' --vnemolex 'C:\Users\ADMIN\Downloads\VnEmoLex.xlsx' --output data/local/seed-review-v2
python -m unittest discover -s tests -p 'test_prepare_seed_review.py'
```

Công cụ chỉ cho ghi trong `data/local/` và từ chối ghi đè thư mục đã có để bảo vệ
kết quả review. File đầu vào phải giữ đúng schema đã kiểm tra; nếu khác, công cụ
báo lỗi thay vì đoán vị trí cột.

Sau khi rà bảng, chọn các mục rõ nghĩa nhất làm seed, xây synset theo nghĩa và
tách các biểu thức còn mơ hồ sang hàng chờ. Chỉ dùng seed đã duyệt để mở rộng
bằng embedding; chưa đưa ứng viên tự động trở lại làm seed.
