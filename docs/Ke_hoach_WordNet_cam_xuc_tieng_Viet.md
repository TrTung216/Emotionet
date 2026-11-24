# Kế hoạch xây dựng WordNet cảm xúc tiếng Việt

**Dự án:** Emotionet  
**Phiên bản kế hoạch:** 2.0 — ngày 24/11/2026  
**Ưu tiên:** Xây tài nguyên từ vựng theo nghĩa để cộng đồng NLP tiếng Việt sử dụng độc lập; đánh giá ứng dụng với GA–xLSTM sau.  
**Trạng thái:** Định hướng triển khai hiện hành. Các mốc và chỉ tiêu phía trước là mục tiêu, không phải kết quả đã đạt.

Kế hoạch này thay lộ trình tương lai trong [kế hoạch v1](Ke_hoach_xay_dung_Emotionet.md)
và [đặc tả nghiên cứu G0](g0/research-spec-v1.md). Kết quả nghiệm thu G0–G1 và
quyết định nghĩa đã có được bảo toàn. Thay đổi schema, POS hoặc membership sẽ đi
qua đề xuất và review, không tự sửa snapshot nguồn.

## 1. Mục tiêu sản phẩm

Emotionet xây dựng **WordNet chuyên miền cảm xúc tiếng Việt**: từ/cụm từ được
phân biệt theo nghĩa, tổ chức thành synset và liên kết bằng quan hệ từ vựng,
ngữ nghĩa có nguồn gốc rõ ràng. Người dùng có thể tra từ đa nghĩa, duyệt mạng
quan hệ, tải dữ liệu có phiên bản và sử dụng trong nhiều bài toán NLP.

Nền tảng WordNet nhóm các nghĩa đồng nghĩa vào synset và liên kết chúng bằng
quan hệ có loại xác định. Đây là cơ sở mô hình hóa; Emotionet cần quy tắc biên
soạn phù hợp tiếng Việt thay vì sao chép máy móc cách phân loại tiếng Anh.
[Mô hình Princeton WordNet](https://wordnet.princeton.edu/).

Sản phẩm đầu tiên là **bản thử nghiên cứu có phạm vi công bố rõ**, mục tiêu ít
nhất 300 synset cảm xúc đã duyệt. Con số này không chứng minh đã bao phủ toàn bộ
từ vựng cảm xúc tiếng Việt. Thuật ngữ “lexical ontology” mô tả định hướng tổ chức
tri thức; bản thử không cam kết ontology OWL có hệ suy luận hình thức.

Bộ bàn giao gồm dữ liệu, API Python, công cụ tra cứu CLI, định dạng trao đổi
WordNet, tài liệu biên soạn, báo cáo chất lượng và quy trình tiếp nhận đóng góp.
Kết quả phân loại của GA–xLSTM không phải điều kiện hoàn thành tài nguyên lõi.

## 2. Hiện trạng và phần được kế thừa

**Lượt nhận bổ sung 24/11:** 29 phiếu quan hệ đã có 27 accept/2 revise và có
bản thảo profile WordNet. Snapshot v2 chưa thay đổi; còn hoàn thiện ID/POS,
quan hệ hai cấp và các mâu thuẫn đặc tả theo
[báo cáo đối chiếu](g2/wordnet-profile-audit-2026-11-24.md). Số liệu chưa điền
ở đoạn tiếp theo là lịch sử của lượt nhận trước.

**Cập nhật tiếp nhận trong ngày 24/11:** nhóm đã rà 66 synset (64 keep/2 revise
membership) và chốt 18 cặp pilot (5 accept/4 revise/9 reject, gồm một xác nhận
bổ sung của chủ dự án). 29 quan hệ nguồn chưa điền. Đây là kết quả review trước
profile WordNet, được kế thừa khi bổ sung POS/quan hệ hai cấp. Xem
[biên bản tiếp nhận](g2/review-receipt-2026-11-24.md).

| Thành phần | Hiện trạng ngày 24/11/2026 | Cách sử dụng tiếp |
|---|---|---|
| G0 | Có đặc tả và 30 mẫu kế thừa review đã chốt | Bổ sung profile WordNet; không làm lại toàn bộ G0 |
| G1 | SQLite, FK, transaction, lookup, import/export giữ byte, package `0.1.0.dev0` | Giữ core, nâng schema có phiên bản để hỗ trợ WordNet |
| Kiểm thử G1 | 69/69 test đạt tại bàn giao 23/11; wheel chạy trong môi trường sạch | Là baseline kỹ thuật, không phải chứng nhận ngữ nghĩa |
| Snapshot nghiên cứu v2 | 77 entry, 82 sense, 66 synset, 90 evidence | Tập khởi đầu; rà POS, tính tương đương nghĩa và provenance |
| Quan hệ v2 | 24 related_to, 5 antonym_of; chưa có ID đích rõ và evidence gắn trực tiếp | Giữ proposal, phân giải và duyệt riêng từng quan hệ |
| Bộ G2 v1 | 66 phiếu synset, 29 phiếu quan hệ, 18 cặp thử is_a, bảng tham chiếu 82 sense | Bổ sung POS và quy tắc WordNet trong phiên bản phiếu mới |
| Pipeline embedding | Có quy trình đề xuất và CSV review | Dùng tìm ứng viên; không tự kết nạp synonym hoặc cạnh |
| Nhãn ViGoEmotions | Có nhãn sense đã chốt và dữ liệu ngữ cảnh | Giữ thành một lớp chú giải, không làm cây khái niệm mặc định |
| Matcher và GA–xLSTM | Có prototype, đặc trưng và smoke test | Bảo trì tương thích; phát triển thực nghiệm sau bản lõi |

Nguồn hiện trạng: [bàn giao G0](g0/handoff-2026-11-23.md),
[bàn giao G1](g1/handoff-2026-11-23.md),
[manifest v2](../data/local/seed-synsets-v2/manifest.json),
[bộ G2](g2/README.md). Năm test mới của công cụ chuẩn bị G2 đã đạt; đây là lượt
kiểm tra riêng, không đổi số test ghi trong báo cáo bàn giao G1 lịch sử.

66 synset là số lượng vật lý của snapshot nghiên cứu, chưa được tính đồng loạt
vào mục tiêu 300 synset đạt chuẩn phát hành. Bộ 30 mẫu G0 và 18 đề xuất quan hệ
không làm tăng số synset. Việc giữ bản review của chủ dự án làm nguồn chính
tiếp tục có hiệu lực.

## 3. Phạm vi WordNet cảm xúc

### 3.1. Phạm vi từ vựng

Ưu tiên từ và cụm từ đã được từ vựng hóa, có nghĩa ổn định liên quan trực tiếp
đến cảm xúc: trải nghiệm, trạng thái, thái độ và cách biểu đạt cảm xúc. Mỗi mục
cần được phân loại để tránh trộn trạng thái với hành vi, đặc điểm tính cách hay
phản ứng cơ thể. Bộ loại cụ thể sẽ được chốt trong G2a.

Từ khẩu ngữ, vùng miền, từ lóng và biến thể mạng xã hội có thể được đưa vào nếu
có nghĩa đủ ổn định và bằng chứng sử dụng. Lưu thông tin register/miền sử dụng;
không tạo một sense mới cho mỗi cách viết khác nhau.

Khái niệm rộng dùng làm đầu nối phân cấp được phép bổ sung khi cần, có nguồn và
review riêng. Thống kê riêng các synset cảm xúc lõi và synset hỗ trợ; không dùng
các nút khái quát để đạt chỉ tiêu 300 synset lõi.

### 3.2. Ngoài phạm vi bản thử

Chưa ưu tiên WordNet tổng quát bao phủ mọi lĩnh vực, WSD tổng quát, giao diện web
biên tập nhiều người, suy luận OWL, crawl quy mô lớn hoặc căn chỉnh đa ngôn ngữ
toàn diện. Không yêu cầu nối mọi nút thành một đồ thị liên thông hay chạy
Floyd–Warshall để sinh quan hệ ngữ nghĩa.

## 4. Kiến trúc và mô hình dữ liệu

Tổ chức thành ba lớp có thể phát triển độc lập:

1. **Lõi từ vựng:** entry, form, sense, synset, POS, gloss, ví dụ và quan hệ.
2. **Chú giải cảm xúc:** taxonomy/version, nhãn, phạm vi ngữ cảnh, evidence và
   mức độ/confidence khi thực sự có dữ liệu hỗ trợ.
3. **Ứng dụng:** matcher, chọn nghĩa, trích đặc trưng và GA–xLSTM.

ViGoEmotions là một taxonomy của lớp chú giải. Nhãn `neutral` của câu không
đồng nghĩa một nghĩa từ trung tính; thiếu mục từ cũng không suy ra neutral.
Không dùng nhãn giống nhau để quyết định membership hoặc tự tạo cạnh is_a.
Cách bổ sung lớp thông tin cảm xúc cho synset có thể tham khảo
[WordNet-Affect](https://aclanthology.org/L04-1208/).

| Thực thể | Điều chỉnh cho profile WordNet |
|---|---|
| LexicalEntry | Lemma, ngôn ngữ, POS, dạng chuẩn hóa; xử lý entry khác POS có lịch sử ID rõ |
| Form | Canonical, biến thể chính tả/viết tắt và register; không thay thế quan hệ đồng nghĩa |
| Sense | Một nghĩa của một entry, thuộc một synset; lưu gloss, ví dụ đối chứng và nguồn |
| Synset | Khái niệm từ vựng có định nghĩa, member senses và POS tương thích theo rubric |
| SynsetRelation | Hai đầu là synset ID; loại quan hệ và ràng buộc riêng |
| SenseRelation | Hai đầu là sense ID; phục vụ quan hệ từ vựng chỉ đúng cho những nghĩa từ cụ thể |
| Evidence và Review | Giữ nguồn, phương pháp, reviewer/thời điểm và lịch sử thay đổi; không bịa metadata thiếu |
| EmotionAnnotation | Nhãn theo taxonomy có phiên bản, tách khỏi quyết định gộp nghĩa |
| ContextExample | Câu, nguồn/dataset ID, split nếu có, loại ví dụ và quyết định phù hợp sense |

WN-LMF phân biệt lexical entry, sense, synset và hai cấp quan hệ. Profile G2a sẽ
chốt phiên bản WN-LMF cụ thể, bảng ánh xạ và validator dùng để xuất; chưa tuyên
bố JSONL hiện tại đã tương thích chỉ vì có tên trường tương tự.
[Global WordNet Formats](https://globalwordnet.github.io/schemas/).

Giữ JSONL và SQLite làm định dạng làm việc. Export WN-LMF kèm gói provenance
riêng cho trường nội bộ không biểu diễn được trực tiếp; công bố rõ phần nào
được trao đổi hai chiều, phần nào nằm trong sidecar. Không giả ID liên ngôn ngữ
hoặc tự đặt confidence=1 để điền trường còn thiếu.

Nâng schema qua migration có kiểm thử và tạo DB phiên bản mới. Đổi nghĩa không
tương thích hoặc tách/gộp cần mapping ID cũ–mới, lý do và review. Loader lịch sử
và API G1 được duy trì tương thích trong phạm vi đã công bố.

## 5. Quy tắc biên soạn nghĩa và quan hệ

### 5.1. Nghĩa và từ loại

Chốt quy tắc POS tiếng Việt trước khi duyệt hàng loạt. Một hình thức có nhiều
vai trò cần được phân biệt dựa trên nghĩa và cách dùng; không tự lấy nhãn tiếng
Anh để gán POS. Trong nghiên cứu có thể giữ chưa biết; mục chưa rõ POS không
được tính vào bộ lõi đã chuẩn hóa của bản phát hành.

Synset gom các nghĩa tương đương trong phạm vi đã xác định, không gom mọi từ
liên tưởng đến cùng cảm xúc. Khi các gloss thành viên khác nhau về nội dung
cốt lõi, đề nghị tách hoặc chỉnh membership thay vì làm định nghĩa chung mơ hồ.

Gloss là định nghĩa, ví dụ là bằng chứng cách dùng. Có thể chọn ví dụ từ corpus
hoặc biên soạn câu minh họa và ghi rõ loại; không gọi câu tự viết là trích dẫn
corpus. Câu chứa từ chưa đủ chứng minh sense đang xét, nhất là khi có phủ định,
châm biếm hoặc diễn đạt hành vi.

### 5.2. Loại quan hệ và phạm vi

| Nhóm quan hệ | Cách xử lý trong bản thử |
|---|---|
| Hypernym/hyponym | Duyệt nghĩa hẹp → rộng; lưu một chiều chuẩn, tra chiều ngược qua API; chặn cycle |
| Quan hệ động từ | Xem xét cách thức cụ thể hơn và entailment khi có rubric; không suy chỉ bằng cường độ |
| Antonym | Chốt sense/synset phù hợp, phạm vi đối lập và bằng chứng riêng; reject synonym không đủ duyệt antonym |
| Similar/related | Phân biệt gần nghĩa có tiêu chí với liên tưởng chung; không biến related_to thành synonym |
| Quan hệ từ vựng khác | Chỉ thêm khi đủ quy tắc, dữ liệu và ánh xạ định dạng; không cần triển khai hết mọi quan hệ WordNet |
| Quan hệ mức độ | Giữ đề xuất riêng nếu cần; chưa mặc định là predicate của bản thử |

Cấu trúc quan hệ cần xét POS: danh từ thường có phân cấp loại–cha, động từ có
thể phân biệt cách thức, còn tính từ có mạng trái nghĩa và tương tự. Vì vậy
18 cặp is_a hiện có là mẫu để thảo luận, không phải bộ cạnh đã chuẩn hóa.
[Quan hệ trong Princeton WordNet](https://wordnet.princeton.edu/).

Một cạnh is_a chỉ được chấp nhận khi có bao hàm đúng chiều, điều kiện phân biệt
nghĩa hẹp, không tương đương hai chiều và phù hợp toàn bộ nghĩa thành viên.
Nếu đang tranh luận về POS hoặc cần sửa một đầu cạnh, giữ needs_review.

Không đặt chỉ tiêu số cạnh để buộc nối các synset. Có thể giữ nút chưa nối khi
chưa có bằng chứng, đồng thời báo cáo số thành phần liên thông và lý do.

## 6. Quy trình xây dựng và kiểm duyệt

1. **Khảo sát và chọn nguồn.** Ghi registry cho nguồn từ vựng, corpus và tài
   nguyên WordNet tham khảo, gồm phiên bản, điều kiện sử dụng, phương pháp và
   locator. Khảo sát khả năng tái sử dụng WordNet tiếng Việt hiện có trước khi
   quyết định biên soạn mới hoặc căn chỉnh; không mặc định phải xây mọi thứ từ đầu.
2. **Rà bộ lõi.** Bắt đầu từ 66 synset và 82 sense, ưu tiên nhóm nhiều thành viên,
   nghĩa mới từ embedding và điểm thiếu metadata. Giữ quyết định lịch sử, ghi
   riêng lượt rà theo profile WordNet.
3. **Tạo phiếu phiên bản mới.** Bổ sung POS entry/synset, loại khái niệm, phạm vi
   dùng, cấp quan hệ sense/synset và bằng chứng vào bộ G2. Không ghi đè phiếu
   g2-review-v1 hoặc phiếu nhóm đã điền; kế thừa quyết định bằng ID và kiểm tra hash.
4. **Mở rộng ứng viên.** Kết hợp nguồn từ vựng và embedding; mỗi đợt khoảng
   40–60 synset mục tiêu để nhóm xử lý được. Số ứng viên không tính là số đã duyệt.
5. **Biên soạn và review.** Viết gloss, rà đồng nghĩa, tách nghĩa, gán POS, kiểm
   ví dụ và quan hệ. Người phụ trách chốt trường hợp bất đồng; phiếu mới lưu đúng
   người và thời điểm thực, không suy review từ một chữ accept thiếu ngữ cảnh.
6. **Đóng phiên bản.** Chỉ những mục đủ tiêu chí mới được đưa vào tập phát hành;
   lập manifest, mapping, changelog và kiểm tra qua API. Lưu đầy đủ quyết định
   bị loại/hoãn trong kho biên soạn, không âm thầm xóa lịch sử.

28/29 từ đích trong phiếu quan hệ hiện tại chưa khớp bề mặt với lemma trong v2.
Cần tìm nghĩa tương đương dưới lemma khác trước khi tạo concept mới; không tự
tạo 28 synset từ kết quả không khớp chuỗi.

## 7. Lộ trình và timeline dự kiến

G0–G1 đã hoàn thành trong phạm vi cũ. Lộ trình còn lại dùng **12 tuần từ
24/11/2026 đến 15/02/2027** làm khung dự kiến. Giả định có hai người tham gia
biên soạn/review, mỗi người khoảng 6–8 giờ/tuần, và người phụ trách kỹ thuật
khoảng 8–12 giờ/tuần; vai trò có thể kiêm nhiệm nhưng phải tính lại tổng thời gian.
Sau hai đợt review đầu, điều chỉnh lịch theo tốc độ duyệt thực tế. Không hạ chuẩn
nghĩa để đạt ngày hoặc số lượng.

| Giai đoạn | Thời gian dự kiến | Công việc chính | Bàn giao và tiêu chí hoàn thành |
|---|---|---|---|
| G0 — Thiết kế nền | Đã hoàn thành 23/11/2026 | Giữ quyết định phạm vi, nguồn, ID và 30 mẫu | Kế thừa nghiệm thu lịch sử |
| G1 — Core API | Đã hoàn thành 23/11/2026 | Giữ SQLite, lookup, import/export và package | Kế thừa kiểm thử; phần WordNet bổ sung được nghiệm thu riêng |
| G2a — Profile WordNet | Tuần 1, 24–30/11/2026 | Chốt POS, synset, phạm vi miền, quan hệ hai cấp, nguồn và schema đích | Đặc tả WordNet v1, rubric có ví dụ đúng/sai/chưa chắc, phiếu G2 v2 và thiết kế migration |
| G2b — Chuẩn hóa bộ lõi | Tuần 2–3, 01–14/12/2026 | Rà 66 synset/82 sense, 29 proposal và 18 cặp pilot; triển khai schema/API cần thiết | Mỗi mục có quyết định giữ/sửa/hoãn; tạo snapshot lõi mới cho phần đủ chuẩn, không buộc giữ đúng 66 |
| G2c — Mở rộng có kiểm duyệt | Tuần 4–7, 15/12/2026–11/01/2027 | Mở rộng theo đợt, bổ sung provenance, gloss, POS, ví dụ và quan hệ | ≥300 synset cảm xúc lõi đã duyệt; thống kê entry/sense/nút hỗ trợ riêng; không có quota cạnh |
| G3 — Chú giải và trao đổi WordNet | Tuần 8–9, 12–25/01/2027 | Chuẩn hóa lớp cảm xúc, mapping taxonomy và export WN-LMF | Nhãn có nguồn và scope, tách khỏi cấu trúc synset; exporter/validator đạt; sidecar giữ provenance |
| G4 — Đánh giá tài nguyên | Tuần 10–11, 26/01–08/02/2027 | Audit độc lập, xử lý bất đồng, đánh giá lookup, lỗi nghĩa/quan hệ và coverage | Báo cáo chất lượng có mẫu, phương pháp, sai số, giới hạn; đóng lỗi nghiêm trọng |
| G5 — Bản thử cho cộng đồng | Tuần 12, 09–15/02/2027 | Gói dữ liệu, SQLite, API/CLI, tài liệu, citation, changelog và chính sách đóng góp | Bản thử v0.1.0 khi qua toàn bộ cổng chất lượng và phân phối |
| G6 — Đánh giá ứng dụng | Sau khi đóng băng bản lõi; lập lịch riêng | Matcher/WSD theo phạm vi, tích hợp encoder thật và GA–xLSTM | Gold matcher, baseline và ablation tái lập; không dùng smoke test làm kết quả thực nghiệm |

Thay đổi so với kế hoạch cũ: hypernym/hyponym nằm ở G2 cùng POS và biên soạn
nghĩa; lớp cảm xúc/chuẩn trao đổi ở G3; G4 ưu tiên đánh giá tài nguyên. Gold set
matcher và thử nghiệm GA–xLSTM chuyển sang G6. Matcher prototype vẫn được giữ,
nhưng điểm F1 của nó không chặn phát hành bộ WordNet lõi.

## 8. Tiêu chí chất lượng và phát hành

### 8.1. Ràng buộc bắt buộc của bản lõi

- Mọi synset được tính vào chỉ tiêu có định nghĩa, POS đã chốt, member senses
  hợp lệ, ít nhất một ví dụ được duyệt và provenance. Ví dụ ghi rõ trích corpus
  hay do người biên soạn tạo; sense dễ nhầm cần ví dụ phân biệt.
- Mọi record phát hành có quyết định review truy vết được; quan hệ có ID hai
  đầu đúng cấp, bằng chứng và lý do riêng. Mục chưa đủ metadata giữ trong kho
  nghiên cứu, không tự chuyển thành approved.
- Không có ID trùng, FK sai, cạnh tự trỏ, cạnh trùng không được xử lý hoặc cycle
  trong phân cấp đã chọn. Kiểm tra POS và miền áp dụng của từng loại quan hệ.
- JSONL/SQLite giữ đầy đủ dữ liệu; WN-LMF đạt validator phiên bản đã chốt. Bài
  kiểm tra round-trip phân biệt rõ phần lõi trao đổi được và sidecar nội bộ.
- API và CLI chạy trong môi trường sạch; test hồi quy G1 đạt; có hướng dẫn tải,
  tra cứu đa nghĩa, truy vấn quan hệ và báo lỗi.

### 8.2. Đánh giá ngữ nghĩa độc lập

Lấy mẫu phân tầng theo POS, loại quan hệ, đa nghĩa, nguồn và phương thức mở rộng.
Mục tiêu audit ban đầu: ít nhất 100 synset và 100 quan hệ, hoặc toàn bộ nếu tập
nhỏ hơn. Lấy mẫu ngẫu nhiên có seed; công bố số lượng từng tầng và cách tính
tỷ lệ chung khi phân tầng không tỷ lệ. Pilot 18 cặp không dùng thay mẫu đánh giá.

Hai người chấm độc lập trên mẫu audit trước khi hòa giải; tối thiểu có một
người không trực tiếp biên soạn mục đó. Nếu chưa bố trí được, báo đúng là rà
nội bộ và chưa hoàn thành tiêu chí audit độc lập. Báo cáo tỷ lệ đồng thuận,
chỉ số phù hợp như Cohen's kappa khi áp dụng được, số bất đồng và cách xử lý.

Mục tiêu ban đầu là **≥90% đạt rubric** riêng cho chất lượng synset và tính đúng
quan hệ trên mẫu. Báo cáo kèm khoảng tin cậy, số mẫu và tỷ lệ chưa chắc; không
gọi tỷ lệ mẫu là độ chính xác đã biết của toàn bộ WordNet. Nếu không đạt, sửa
nguyên nhân và kiểm tra lại trên mẫu mới, không chỉ chấm lại những dòng đã sửa.

Coverage đo trên corpus độc lập theo miền được chọn trước, phân biệt khớp
lemma với đúng sense. Chưa đặt một ngưỡng coverage chung hoặc dùng độ phủ
ViGoEmotions để khẳng định bao phủ cảm xúc tiếng Việt nói chung.

### 8.3. Đóng gói và quyền tái sử dụng

Giữ nguyên quyết định của chủ dự án: repo và dữ liệu hiện có được chia sẻ trong
phạm vi đã chọn, chưa cấp thêm giấy phép tái sử dụng. Kế hoạch này không tự cấp
LICENSE hoặc thay điều kiện của nguồn NRC, VnEmoLex, corpus và tài nguyên khác.

G5 cần chốt điều kiện tái sử dụng rõ cho mã, dữ liệu tự biên soạn và phần bên
thứ ba. Gói phát hành chỉ chứa các record và phụ thuộc đủ điều kiện của gói đó;
metadata quyền được ghi bằng quyết định mới, không sửa ngược lịch sử nguồn.
Nếu chưa thể cung cấp gói cho cộng đồng tái sử dụng theo mục tiêu, tiếp tục bản
nghiên cứu chia sẻ hiện tại và ghi G5 chưa hoàn tất. Xem
[quyết định G0](g0/handoff-2026-11-23.md).

## 9. Kế hoạch ứng dụng sau bản lõi

Đóng băng phiên bản WordNet trước khi đo trên test. Chọn cấu hình bằng train/
validation; không dùng nhãn hoặc kết quả test để bổ sung từ, gộp nghĩa hay sửa
quan hệ rồi báo điểm trên chính test đó. Công bố corpus đã dùng để xây tài
nguyên, nhất là phần train ViGoEmotions, để người đọc đánh giá mức độc lập.

G6 trước hết xử lý matcher trả candidate sense và span đúng, rồi xây gold set
riêng. Tiếp theo nối encoder xLSTM thật, so sánh baseline, đặc trưng từ điển và
đặc trưng quan hệ với ngân sách tương đương. GA có thể tối ưu siêu tham số,
block xLSTM và nhóm đặc trưng theo protocol đã khóa. Các kiểm tra cửa sổ token,
cache và độc lập batch tiếp tục là ràng buộc kỹ thuật.

Không yêu cầu WordNet phải cải thiện mọi mô hình mới có giá trị nghiên cứu.
Chất lượng tài nguyên và lợi ích downstream là hai câu hỏi được đánh giá riêng.

## 10. Phân công và công việc bắt đầu ngay

| Vai trò | Trách nhiệm |
|---|---|
| Chủ dự án | Chốt phạm vi, rubric, xử lý bất đồng và chính sách phát hành |
| Người biên soạn | Đề xuất nghĩa/POS/gloss/ví dụ, ghi nguồn và phân biệt nghĩa |
| Người rà soát | Kiểm tra membership và quan hệ, tìm phản ví dụ; audit độc lập khi đủ điều kiện |
| Kỹ thuật | Schema, migration, công cụ review, API, validator, export và đóng gói |
| Phụ trách đánh giá | Thiết kế mẫu audit, tính chỉ số và báo cáo giới hạn |

Không tự gán quyết định cho thành viên nhóm chỉ vì file review cũ có tên họ.
Công cụ hỗ trợ chuẩn bị phiếu, kiểm tra kỹ thuật và đề xuất; quyết định ngữ
nghĩa mới phải ghi nhận từ người duyệt thực.

Công việc đầu tiên của G2a:

1. Viết profile WordNet v1, quy tắc POS và phân loại nghĩa cảm xúc; chốt phạm vi
   quan hệ cần cho bản thử.
2. Tạo phiếu G2 v2 kế thừa ID/nguồn và mọi quyết định nhóm đã điền, bổ sung POS,
   loại khái niệm, cấp quan hệ và tiêu chí tương đương nghĩa.
3. Rà một pilot gồm các nhóm dễ lẫn trạng thái/hành vi, đồng nghĩa/loại–cha và
   khác biệt mức độ; chốt rubric trước khi duyệt hàng loạt.
4. Thiết kế migration quan hệ hai cấp và ánh xạ WN-LMF, giữ tương thích G1.
5. Lập danh mục nguồn có thể dùng cho biên soạn, khả năng tái sử dụng tài nguyên
   hiện có và corpus đánh giá độc lập. Sau đó mới mở rộng vòng embedding tiếp.

## 11. Theo dõi tiến độ

Mỗi đợt báo cáo riêng số entry, sense, synset lõi, synset hỗ trợ, quan hệ theo
loại, mục approved/needs_review, tỷ lệ thiếu POS/provenance và nguồn phát sinh.
Không dùng số dòng review hoặc số lemma để thay số synset đã duyệt.

G0–G1 giữ trạng thái hoàn thành lịch sử. G2 hiện đang **chuẩn bị profile WordNet**;
đã nhận review 66 synset, 18 cặp pilot và quyết định cho 29 quan hệ nguồn.
Còn chốt profile, POS, ID nghĩa đích và migration; chưa nghiệm thu WordNet.
Bản thử chỉ được
đánh dấu hoàn thành khi cả dữ liệu, QA, định dạng trao đổi và điều kiện phân
phối đạt; ngày trong timeline không tự tạo quyết định nghiệm thu.
