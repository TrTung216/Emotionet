# Báo cáo tiến độ Emotionet và timeline công việc còn lại

## Cập nhật kiểm tra ngày 22/11/2026

**Các mục 1–6 bên dưới giữ nguyên số liệu lịch sử ngày 21/11.** Kiểm tra ngày 22/11 phát hiện đã có review mới, snapshot v2 và mã thư viện mới; vì vậy các câu “240 cặp chờ duyệt”, “chưa có matcher/đặc trưng” trong trạng thái cũ không còn mô tả đầy đủ hiện trạng.

### Kết quả mới đã xác minh

| Hạng mục | Hiện trạng ngày 22/11 |
|---|---|
| 5 đề nghị gộp | Cả 5 đã ghi `accept`, có reviewer và thời điểm |
| 240 cặp ứng viên | 35 `accept` = 11 `synonym` + 24 `related`; 205 `reject` = 200 `unrelated` + 5 `antonym`; không còn quyết định trống |
| Snapshot v2 | 77 entry, 82 sense, 66 synset, 90 evidence, 29 relation; đã áp dụng 5 lần gộp và thêm 11 sense đồng nghĩa |
| Tính nhất quán v2 | Không trùng ID trong năm loại bản ghi; các tham chiếu sense–entry–synset/evidence và subject của relation đã kiểm tra đều hợp lệ; mọi checksum đầu ra khớp manifest v2 |
| Mã mới | Có models/loader, matcher, bộ 171 đặc trưng F1–F8, mask nhóm và head PyTorch 28 nhãn, dataset đa nhãn, hàm metric |
| Kiểm thử | Lệnh `python -m unittest discover -s tests` lỗi import `emotionet`; thêm `src` vào đường dẫn import thì 31 test đạt. Chưa có `pyproject.toml` để cài package |
| Tích hợp mô hình | Script smoke dùng hidden state ngẫu nhiên (`mock_pooled_h`), chưa chứng minh nối và train với encoder xLSTM thật; không phải kết quả đánh giá hiệu quả |
| Phiên bản được chọn | `configs/synset-selection.json` vẫn chọn v1; v2 tồn tại nhưng chưa được đồng bộ thành bản đang chọn |

Nguồn kiểm tra: [manifest v2](../../data/local/seed-synsets-v2/manifest.json), [review gộp](../../data/local/seed-synsets-v1/merge-proposals.csv), [review ứng viên](../../data/local/embedding-expansion-v1/candidate-review.csv), [mã thư viện](../../src/emotionet/), [smoke script](../../scripts/smoke_test_ga_xlstm_integration.py) và [cấu hình chọn phiên bản](../../configs/synset-selection.json).

### Phát hiện cần xử lý trước khi chạy thực nghiệm

| Ưu tiên | Phát hiện và bằng chứng | Hướng xử lý |
|---|---|---|
| Cao | `integration.py:134,174`: tính đặc trưng trên toàn bộ text, nhưng token đầu vào bị cắt theo `max_length`. Tái hiện với `a b c vui`, tokenizer theo từ, `max_length=2`: encoder chỉ thấy `a b`, đặc trưng vẫn ghi nhận joy từ `vui` | Trích đặc trưng trên đúng phần văn bản encoder nhìn thấy, dùng offset/tokenization thống nhất; kiểm tra cả feature cache |
| Cao | `integration.py:87`: điều kiện vector bằng 0 được xét cho toàn batch. Ở chế độ `eval`, cùng một mẫu có g=0 chạy riêng và ghép với mẫu g≠0 cho logit lệch tối đa khoảng 0,1268 trong phép thử seed 42 | Xác định chính sách nhánh đặc trưng theo từng mẫu/mask; bảo đảm cùng mẫu cho cùng dự đoán bất kể cách ghép batch |
| Cao | `build_synsets_v2.py:31`: chạy lại sẽ xóa toàn bộ thư mục v2 đang tồn tại trước khi đọc và kiểm tra đầu vào | Từ chối ghi đè, tạo phiên bản/thư mục đầu ra mới; kiểm tra đầu vào trước khi ghi. Trong lần audit này không chạy builder |
| Vừa | `matcher.py:259`: câu `không buồn nhưng vui` đánh dấu cả `vui` trong phạm vi phủ định; code chưa dừng tại liên từ tương phản | Chặn phạm vi tại ranh giới mệnh đề; thêm trường hợp kiểm tra tái hiện |
| Vừa | `matcher.py:232,289`: `nhưng mà vui` đếm 2 liên từ chồng lấn; `vui lắm.` không nhận modifier do dấu chấm gắn với token | Khớp marker dài nhất và xử lý dấu câu tại biên token |
| Vừa | `matcher.py:198`: gộp nhãn của mọi nghĩa nhưng chỉ trả một `synset_id` đầu tiên. `tôi lo cho con` trả nhãn caring+nervousness với ID synset nervousness | Trả đầy đủ candidate sense/synset và trạng thái chưa phân giải; không trình bày ID đầu tiên như kết quả chọn nghĩa |
| Vừa | 29 relation v2 không có `evidence_ids`/ID dòng review. Trong đó 5 cạnh antonym được tạo từ các dòng `decision=reject` | Tách rõ quyết định kết nạp synonym và quyết định duyệt quan hệ; giữ nguồn review, người duyệt và thời điểm cho từng cạnh |
| Vừa | Hai CSV review v1 đã thay đổi nên không còn khớp checksum của manifest ban đầu; manifest v2 chỉ lưu hash đầu ra, chưa khóa hash đầu vào review | Lưu snapshot review đã nộp và hash đầu vào; giữ manifest lịch sử, không sửa hash cũ để che thay đổi |
| Vừa | Ví dụ của sense mới `nể` dùng cụm `không ... nể tình bạn là con gái`, chưa chứng minh nghĩa “khâm phục tài năng/tư cách”; một số ví dụ khác có phủ định | Duyệt ví dụ đúng nghĩa riêng với duyệt lemma/gloss; không coi câu chứa từ là bằng chứng trực tiếp về cảm xúc người nói |

Các lỗi batch, truncation và matcher ở trên đã được tái hiện bằng phép thử trực tiếp, dù 31 test hiện có đều đạt khi cấu hình được import. Lần kiểm tra này không sửa mã hoặc quyết định nghĩa đã duyệt, không chọn v2 làm bản chính và không chạy huấn luyện.

### Điều chỉnh công việc gần nhất

Không yêu cầu làm lại toàn bộ 5 + 240 review. Tuần **23–29/11** ưu tiên sửa các lỗi trên, bổ sung kiểm tra hồi quy, xác minh bằng chứng/quan hệ còn nghi vấn, tạo snapshot có provenance đầy đủ rồi đồng bộ cấu hình và tài liệu. Phần review nội dung đã đi trước lịch; G1/G3/G4 đã có mã ban đầu nhưng chưa đủ điều kiện nghiệm thu. Các mốc cuối trong timeline vẫn là dự kiến, cần đánh giá lại sau khi đo thời gian train với encoder thật.

---

**Ngày chốt số liệu: 21/11/2026.** Mục tiêu nghiên cứu: xây dựng từ điển cảm xúc tiếng Việt theo nghĩa, phục vụ nhận diện cảm xúc đa nhãn trên ViGoEmotions bằng GA–xLSTM; sau đó bổ sung GA chọn đặc trưng từ điển.

**Đã hoàn thành chuỗi xử lý từ seed đã duyệt → tách nghĩa → 71 synset khởi đầu → pilot mở rộng embedding.** Hiện có 240 cặp ứng viên–synset chờ duyệt. Chưa có thư viện hoàn chỉnh, chưa tích hợp đặc trưng từ điển vào mô hình và chưa có kết quả chứng minh cải thiện F1. G0 vẫn đang thực hiện vì còn các tiêu chí đặc tả, mẫu chuẩn và quyền sử dụng dữ liệu.

## 1. Những việc đã làm

| Hạng mục | Kết quả đã có | Bằng chứng và giới hạn |
|---|---|---|
| Khởi tạo dự án và G0 | Cây thư mục, kế hoạch gốc, use case, schema dự thảo, quy trình kiểm duyệt, registry nguồn; 30 concept mẫu và công cụ kiểm tra cấu trúc | [Theo dõi G0](../g0/README.md). 30 mẫu vẫn là bản nháp `candidate`, chưa phải 30 mẫu chuẩn đã duyệt. |
| Kiểm tra ViGoEmotions và mã GA–xLSTM | Xác minh 16.531 câu train, 2.066 validation, 2.067 test; 28 nhãn gồm 27 cảm xúc và neutral; đối chiếu chỗ cần sửa trong pipeline | [Báo cáo tích hợp](../g0/local-integration-audit.md). Runner đã đối chiếu còn dùng bài toán một nhãn, `CrossEntropyLoss` và `argmax`; chưa chuyển xong sang đa nhãn. |
| Chuẩn bị seed từ NRC/VnEmoLex | Đối chiếu nguồn, chuẩn hóa và lưu provenance; nhập bản review v2 gồm 66 seed được chấp nhận về nội dung, phủ 27 nhãn cảm xúc | [Lịch sử seed](../g0/seed-source-review.md). Phủ nhãn không đồng nghĩa đủ độ phủ từ vựng; quyền phát hành còn chờ xác định. |
| Chốt bản dữ liệu chính | Giữ bản v2 của chủ dự án; lưu review của Tâm và Hoàng để tham khảo | [Quyết định phiên bản](../../configs/seed-selection.json). Không đưa 21 mục đối chiếu nhóm trở lại thành điều kiện bắt buộc. |
| Tách nghĩa và rà ngữ cảnh | Nhập 10 nghĩa tách được duyệt cho 5 biểu thức; rà 155 cặp từ–câu thuộc 148 câu train; nhập đủ 6 quyết định xử lý chất lượng | Kết quả cuối: 143 `matches_sense`, 8 `wrong_sense`, 4 `uncertain`. [Snapshot xử lý](../../data/local/quality-resolution-v1/summary.json). |
| Tạo synset theo nghĩa đã chốt | 66 entry, 71 sense, 71 synset; kèm định nghĩa, nhãn, bằng chứng và ID truy vết | [Mô tả synset](../g0/synsets-and-expansion.md). Mỗi synset đang có một sense thành viên; 5 đề nghị gộp chưa được duyệt. |
| Mở rộng ứng viên bằng embedding | Đã huấn luyện Word2Vec Skip-gram trên text train; truy vấn 48 synset, bỏ qua 23 mục thiếu anchor; sinh 240 cặp ứng viên–synset, tương ứng 166 biểu thức khác nhau | [Manifest pilot](../../data/local/embedding-expansion-v1/manifest.json). Không dùng nhãn câu để huấn luyện embedding; chưa kết nạp ứng viên nào. |
| Kiểm tra và khả năng tái lập | Có script nhập review, kiểm tra dữ liệu, dựng synset, mở rộng embedding; lưu cấu hình, snapshot và checksum; lần chạy kiểm thử gần nhất có 23 test đạt | [Scripts](../../scripts/), [tests](../../tests/), [cấu hình embedding](../../configs/embedding-expansion.json). Đây là kiểm thử phần mềm, không phải đánh giá hiệu quả mô hình. |

Các snapshot chi tiết nằm trong `data/local/`, được bỏ qua bởi Git. Những liên kết tới thư mục này dùng được trên máy dự án; báo cáo và mã nguồn không tự mang theo dữ liệu local khi chia sẻ repo.

## 2. Số liệu hiện tại và cách diễn giải

| Chỉ số | Giá trị tại ngày báo cáo | Ý nghĩa |
|---|---:|---|
| Seed được chấp nhận về nội dung | 66 | Bản nền do chủ dự án chọn |
| Sense / synset khởi đầu | 71 / 71 | `66 − 5 + 10`; chưa gộp liên lemma |
| Nhãn cảm xúc được phủ | 27 | Không tính neutral là một nhóm từ cảm xúc |
| Seed khớp chuỗi trong train | 60/66 | Kiểm tra bề mặt, chưa phân giải nghĩa |
| Câu train có seed khớp | 3.036/16.531 ≈ 18,37% | Độ phủ khớp chuỗi, không phải recall nhận diện cảm xúc |
| Mẫu đã rà | 155 cặp / 148 câu | Mẫu khám phá lấy tối đa 3 câu đầu cho mỗi seed |
| Quyết định trên mẫu | 143 khớp; 8 sai; 4 chưa chắc | Tương ứng 92,3%; 5,2%; 2,6% sau làm tròn; không phải precision/accuracy |
| Đề nghị gộp còn trống quyết định | 5 | Cần xét tương đương nghĩa trước khi gộp |
| Ứng viên embedding còn trống quyết định | 240 cặp / 166 biểu thức | Một biểu thức có thể được đề nghị cho nhiều synset |
| Thành viên mới từ embedding đã được duyệt | 0 | Chưa tăng kích thước từ điển sau pilot |

Nguồn: [seed review](../g0/seed-source-review.md), [summary rà nghĩa](../../data/local/sense-match-review-v2/summary.json), [manifest synset](../../data/local/seed-synsets-v1/manifest.json) và [kết quả pilot](../g0/synsets-and-expansion.md). Trong lần lập báo cáo đã đối chiếu số dòng hàng chờ và checksum của các snapshot hiện hành.

Các giới hạn cần giữ khi viết báo cáo nghiên cứu:

- **Nhãn sense và nhãn toàn câu là hai cấp khác nhau.** Ví dụ `ghét_s2` được giữ theo quyết định đã chốt với nhãn `anger`, còn câu `tik012211` mang nhãn `remorse;annoyance;disgust`. Không mô tả đây là sự trùng khớp hoàn toàn, cũng không tự đổi quyết định của người duyệt.
- **Gần vector chưa đủ để kết luận đồng nghĩa.** Pilot có cả ứng viên cùng chủ đề hoặc khác cảm xúc. 240 đề xuất chưa phải 240 mục từ mới được chấp nhận.
- **71 synset chưa tương đương 71 nhóm nhiều từ đồng nghĩa.** Đây là các hạt nhân nghĩa, mỗi nhóm hiện có một sense. Số synset có thể giảm sau gộp.
- **Từ điển nghiên cứu chưa được thông qua để phát hành.** Quyết định nội dung và quyền tái phân phối được quản lý riêng.
- **Chưa có kết quả downstream.** Chưa thể kết luận từ điển hoặc GA chọn đặc trưng giúp cải thiện nhận diện cảm xúc.

## 3. Timeline dự kiến cho phần còn lại

Lịch dưới đây giữ khung **12 tuần G0–G5** của [kế hoạch gốc](../Ke_hoach_xay_dung_Emotionet.md), quy ước tuần 1 là 16–22/11/2026. Phần còn lại dự kiến **23/11/2026–07/02/2027, khoảng 11 tuần**. Đây là lịch đề xuất, chưa phải deadline đã cam kết; giả định nhóm duy trì 1–3 người và có thời gian review hằng tuần. Tốc độ huấn luyện cần đo trên phần cứng thực tế trước khi chốt ngân sách GA.

Hai nhánh có thể chạy song song: **A — từ điển/thư viện** và **B — mô hình/thực nghiệm**. Vai trò trong bảng là đề xuất phân công, chưa gán bắt buộc cho thành viên cụ thể.

| Mốc dự kiến | Nhánh A: từ điển và thư viện | Nhánh B: GA–xLSTM | Điều kiện kết thúc |
|---|---|---|---|
| **23–29/11 — khép phần còn lại G0** | Duyệt 5 đề nghị gộp và 240 cặp ứng viên; bổ sung bằng chứng cho mục chưa chắc; chốt schema cảm xúc và cách nối với schema G0; hoàn tất mẫu chuẩn và ghi tình trạng quyền sử dụng | Chốt protocol đa nhãn, cách chia train nội bộ, metric và các thí nghiệm đối chứng | Có snapshot sau review, lịch sử quyết định và đặc tả đủ để triển khai; mục còn thiếu bằng chứng được giữ riêng, không tự chuyển approved |
| **30/11–13/12 — G1** | Xây models, SQLite, nhập/xuất JSONL, lookup, chuẩn hóa, validator và gói cài đặt; kiểm tra round-trip và truy vết ID | Chuyển loader sang multi-hot 28 nhãn, loss đa nhãn, sigmoid, threshold validation; chạy thử một cấu hình để đo bộ nhớ/thời gian | API cơ bản dùng được; một lượt train–validation đa nhãn chạy đúng và ghi cấu hình/metric |
| **14/12–03/01 — G2** | Mở rộng thêm theo các nghĩa đã duyệt; rà nhóm hiếm, lỗi phân đoạn, từ lóng và quan hệ; đóng băng snapshot cho nghiên cứu | Chạy baseline không từ điển và GA hiện có sau khi chuyển đa nhãn; thống nhất ngân sách so sánh | Dữ liệu đã duyệt có nguồn, định nghĩa, ví dụ và phiên bản; baseline tái lập được. Mục tiêu ≥300 concept của MVP được kiểm đếm riêng |
| **04–17/01 — G3** | Xây matcher cụm dài nhất, span và xử lý ngữ cảnh cơ bản; tạo tập đánh giá tách khỏi mẫu khám phá; thiết kế vector đặc trưng và manifest | Gắn đặc trưng vào xLSTM; kiểm tra cùng phạm vi văn bản sau truncation; chạy so sánh cố định kiến trúc có/không từ điển | Báo cáo riêng chất lượng tìm span, chọn nghĩa và phân loại cảm xúc; không đồng nhất ba loại kết quả |
| **18–31/01 — G4** | Hoàn thiện lớp cảm xúc, xử lý mục đa nghĩa và nhóm đặc trưng; rà ≥100 biểu thức theo mục tiêu gốc nếu đủ bằng chứng | Thêm mask chọn nhóm đặc trưng vào GA; so với dùng toàn bộ đặc trưng và random search cùng ngân sách | Mỗi cấu hình có log, seed, ngân sách và artifact; có kết quả ablation giải thích đóng góp từng phần |
| **01–07/02 — G5** | Đóng phiên bản, CLI, hướng dẫn sử dụng, kiểm tra cài đặt và dữ liệu được phép chia sẻ | Chốt lựa chọn bằng validation, đánh giá cuối với nhiều seed, phân tích lỗi và hoàn thiện báo cáo | Bản nghiên cứu tái lập được; bảng kết quả và giới hạn đầy đủ. Chỉ gọi là MVP v0.1.0 nếu đạt các tiêu chí MVP đã chốt |

**Điểm cần dự phòng:** 71 synset hiện tại và 166 biểu thức ứng viên không bảo đảm đạt ≥300 concept đã duyệt, vì nhiều ứng viên có thể bị loại hoặc nhập cùng nghĩa. Nếu giữ nguyên chỉ tiêu 300, dự trù thêm **2–4 tuần** cho thu thập và kiểm duyệt khi cần. Có thể hoàn thành một snapshot phục vụ thực nghiệm sớm hơn, nhưng phải ghi đúng quy mô và chưa tuyên bố đạt toàn bộ MVP. Các mức F1/chất lượng trong kế hoạch gốc là mục tiêu nghiệm thu, chưa phải kết quả đã đạt.

## 4. Việc ưu tiên trong 7 ngày tới

| Thứ tự | Việc cụ thể | Vai trò đề xuất | Đầu ra cần có |
|---|---|---|---|
| 1 | Rà [5 đề nghị gộp](../../data/local/seed-synsets-v1/merge-proposals.csv): yêu–thương/love, nhẹ nhõm–nhẹ lòng, đồng tình–tán thành, nhận ra–vỡ lẽ, lo/nervousness–lo lắng | Chủ dự án/người duyệt nghĩa | `accept`, `reject` hoặc `needs_evidence`, kèm người duyệt, thời điểm và lý do |
| 2 | Rà [240 cặp ứng viên](../../data/local/embedding-expansion-v1/candidate-review.csv), có thể chia 4 lượt × 60 cặp | Người biên soạn và người duyệt | Quyết định, quan hệ, gloss, nhãn đã duyệt và bằng chứng. Chỉ gộp cùng synset khi là `synonym` và nghĩa đã được chốt |
| 3 | Nhập quyết định vào snapshot mới, kiểm tra ID, tham chiếu, bằng chứng và lịch sử gộp | Người triển khai pipeline | Snapshot kế tiếp và báo cáo thay đổi; giữ nguyên các snapshot nguồn |
| 4 | Chốt ánh xạ schema nghiên cứu với G0, mẫu chuẩn và các trường còn thiếu như POS; ghi rõ quyền dùng/phát hành theo từng nguồn | Chủ dự án và người triển khai | Đặc tả dùng chung để bắt đầu G1; quyết định nào chưa có thì giữ trạng thái chờ |
| 5 | Viết cấu hình thử nghiệm ViGoEmotions 28 nhãn và danh sách thay đổi runner GA–xLSTM | Người phụ trách mô hình | Protocol và cấu hình train thử; chưa cần chạy GA lớn ở bước này |

Không cần làm lại review của Tâm/Hoàng để bắt đầu các việc trên. Mục `needs_evidence` có thể được loại khỏi snapshot được duyệt và tiếp tục xử lý ở lượt sau, thay vì ép duyệt để đạt số lượng.

## 5. Thiết kế thực nghiệm còn phải thực hiện

Theo [đề xuất tích hợp](../g0/vigoemotions-ga-xlstm-proposal.md), nên giữ các đối chứng sau để phân biệt hiệu quả của GA và từ điển:

| Thí nghiệm | Cấu hình | Câu hỏi được kiểm tra |
|---|---|---|
| A | xLSTM cấu hình cố định, không từ điển | Baseline trên ViGoEmotions là bao nhiêu? |
| B | GA tối ưu cấu hình xLSTM, không từ điển | GA cải thiện bao nhiêu so với A? |
| C | Giữ cấu hình B, thêm toàn bộ nhóm đặc trưng từ điển | Từ điển đóng góp bao nhiêu khi giữ kiến trúc cố định? |
| D | Giữ kiến trúc B, GA chọn nhóm đặc trưng | Chọn đặc trưng có lợi hơn dùng toàn bộ hay random search cùng ngân sách? |
| E — tùy chọn sau | GA đồng thời tối ưu kiến trúc và nhóm đặc trưng | Tối ưu chung có thêm lợi ích đủ bù chi phí? |

Cần xác minh phần “tối ưu block” trong mã hiện có: audit cho thấy một số pattern hybrid được quy định sẵn hoặc lấy ngẫu nhiên, chưa đủ bằng chứng rằng toàn bộ cấu trúc block đã nằm trong chromosome GA. Báo cáo thí nghiệm phải mô tả đúng các gene thực sự được tìm kiếm.

Điều kiện để kết quả có thể đối chiếu:

- Dùng micro-F1, macro-F1 và F1 theo nhãn; lưu threshold, random seed, số lần thử, thời gian và phiên bản dữ liệu. Giữ chính sách neutral nhất quán với dữ liệu đa nhãn, không tự ép neutral loại trừ mọi nhãn khác.
- Chỉ chọn cấu hình/threshold trên validation; không chỉnh từ điển theo lỗi test. Đã có artifact thử nghiệm cũ liên quan test trong dự án mô hình, nên không mô tả test là chưa từng được xem.
- Khi đánh giá GA bằng các fold nội bộ, fit embedding và thống kê đặc trưng trên **inner-train**. Pilot hiện tại dùng toàn bộ train để khám phá, không được coi là tài nguyên độc lập với inner-validation. Các quyết định từ điển đã dựa trên toàn bộ train cũng cần được ghi rõ hoặc kiểm soát bằng quy trình dựng tài nguyên theo fold.
- Xử lý/trình bày minh bạch các câu trùng đã audit; không tùy tiện đổi split rồi so sánh như cùng benchmark. Tạo tập đánh giá matcher theo protocol lấy mẫu riêng; không tái dùng 155 cặp khám phá để báo cáo accuracy.

## 6. Phạm vi chưa thực hiện và chưa đưa vào đường găng

Chưa triển khai đồ thị Floyd–Warshall, WSD tổng quát, thu thập corpus mạng xã hội diện rộng hoặc huấn luyện PhoBERT. Các hạng mục này không phải điều kiện bắt buộc để thử nghiệm đặc trưng từ điển đầu tiên. Chỉ bổ sung khi có câu hỏi nghiên cứu và phép đo rõ ràng; ưu tiên hiện tại là duyệt ứng viên, tạo snapshot có thể truy vết, hoàn thiện matcher và chứng minh đóng góp trên GA–xLSTM.

**Mốc bàn giao gần nhất:** bản synset sau duyệt 5 đề nghị gộp và hàng chờ 240 cặp, kèm đặc tả nhập/xuất để bắt đầu G1. Báo cáo này lập kế hoạch; chưa thực hiện các công việc còn lại hoặc thay đổi quyết định review.
