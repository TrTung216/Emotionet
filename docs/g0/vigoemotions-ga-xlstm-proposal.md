# Đề xuất Emotionet cho ViGoEmotions và GA–xLSTM

Ngày: 15/11/2026. Trạng thái: đề xuất để thảo luận, chưa triển khai hoặc đo kết quả.

## Mục tiêu đã được người dùng xác định

- Dataset: ViGoEmotions.
- Mô hình đang dùng: xLSTM; GA tối ưu siêu tham số và các block.
- Hướng mở rộng: GA chọn đặc trưng từ Emotionet.
- Đã đối chiếu mã và dataset local ngày 20/11/2026; xem [báo cáo tích hợp](local-integration-audit.md).
  Mã huấn luyện hiện tại là UIT-VSMEC bảy lớp một nhãn. GA tìm siêu tham số/số tầng;
  quy trình thử pattern mLSTM/sLSTM hiện dùng mẫu định trước và random sampling.

## Bài toán và nguồn đã kiểm tra

ViGoEmotions hỗ trợ nhiều nhãn trên mỗi bình luận. Mapping chính thức có 27 cảm xúc
và neutral, tức 28 ID; phải lấy đúng thứ tự ID của bản dữ liệu dùng thực nghiệm.
[Dataset card của UIT NLP](https://huggingface.co/datasets/uitnlp/vigoemotions/blob/main/README.md).

Hướng dẫn gán nhãn quy định neutral không đi cùng các cảm xúc khác.
Nghiên cứu cũng cho thấy lựa chọn xử lý emoji ảnh hưởng kết quả tùy mô hình.
[Bài báo ViGoEmotions](https://aclanthology.org/2026.eacl-long.129/).

xLSTM có các block sLSTM và mLSTM; nối gene pattern của chúng vào GA là phần
mở rộng cần thực hiện sau khi có baseline ViGoEmotions đa nhãn.
[Bài báo xLSTM](https://arxiv.org/abs/2405.04517).

Các phần sau là phương án thiết kế cho Emotionet, chưa phải kết luận thực nghiệm.

## Điều chỉnh trọng tâm G0

Ưu tiên từ điển biểu thức cảm xúc tiếng Việt trên mạng xã hội. Giữ cấu trúc
entry–form–sense và provenance, nhưng đưa annotation cảm xúc và matcher cụm từ
lên sớm. Mở rộng ontology tổng quát và các quan hệ is_a/subfield_of có ưu tiên thấp.

30 concept G0 ban đầu vẫn hữu ích để kiểm tra schema; cần bộ mẫu biểu thức cảm xúc
riêng, không coi các concept công nghệ/sinh vật là từ điển cảm xúc đã sẵn sàng.
Vocabulary sáu cảm xúc trong đặc tả đầu tiên cần thay bằng taxonomy ViGoEmotions
có phiên bản nếu chọn phương án này. Không chuyển nhãn tự động giữa hai taxonomy.

## Nội dung từ điển

| Nhóm | Ví dụ tự soạn để minh họa | Vai trò |
|---|---|---|
| Từ/cụm cảm xúc | biết ơn, hụt hẫng, bực mình | Gợi ý nhãn theo sense và phạm vi ngữ cảnh |
| Thành ngữ/biểu thức | nhẹ cả người, tức muốn khóc | Bảo toàn cụm trước khi xét từ con |
| Biến thể mạng xã hội | ko, khum, bùn | Ứng viên biến thể, có điều kiện ngữ cảnh |
| Emoji/emoticon | biểu tượng cười/khóc, chuỗi :)) | Dấu hiệu hỗ trợ; có thể mỉa mai hoặc đa nghĩa |
| Phủ định | không, chẳng, chưa | Đánh dấu phạm vi tác động |
| Mức độ | rất, cực kỳ, hơi | Dấu hiệu tăng/giảm mức độ biểu đạt |
| Cấu trúc câu | nhưng, tuy…nhưng, dấu câu lặp | Dấu hiệu tương phản và nhấn mạnh |

Không ánh xạ biến thể mơ hồ trên toàn văn bản một cách vô điều kiện. Giữ cả văn bản
gốc và bản chuẩn hóa, các span gốc, dấu câu và emoji. Một chuỗi có thể gợi ý nhiều
cảm xúc; chỉ xem đó là bằng chứng đầu vào cho mô hình.

Ví dụ tự soạn: `Tôi không vui nhưng rất biết ơn bạn.` có tín hiệu phủ định quanh
`vui` và tín hiệu gratitude quanh `biết ơn`. Không suy ra `không vui` luôn là sadness,
không đảo joy thành một nhãn đối lập cố định, không gán nhãn câu từ một từ duy nhất.
Không khớp từ điển có nghĩa là thiếu bằng chứng từ điển, không chứng minh neutral.

## Schema cảm xúc đề xuất

Annotation trỏ sense_id, có taxonomy/version, emotion_label, evidence_ids,
context_scope, điều kiện áp dụng/ngoại lệ, status và thông tin người duyệt.
Cường độ chỉ lưu khi có rubric; confidence hoặc trọng số thống kê chưa đo để null.
Không gán các điểm như 0.9 để tạo cảm giác đã có hiệu chuẩn.

Marker phủ định, mức độ và tương phản dùng bảng riêng, không ép thành nhãn cảm xúc.
Phiên bản đầu không tạo từ điển neutral bằng cách gán mọi từ thông thường là neutral.
Một mục có thể có nhiều annotation cảm xúc nhưng không được coi là nhãn chắc chắn
của mọi câu chứa mục đó.

Mục tiêu pilot đề xuất: khoảng 300–500 biểu thức được rà soát, có đại diện cho 27
nhãn cảm xúc và các nhóm marker. Đây là ngân sách khởi đầu, không phải tiêu chí
đủ bao phủ hoặc cam kết đạt F1. Báo cáo số mục và mức phủ trên train theo từng nhãn.

## Tích hợp đầu tiên: ghép đặc trưng ở đầu phân loại

```text
Văn bản → tokenizer/embedding hiện tại → xLSTM → pooling có mask → h
       └→ Emotionet matcher → đặc trưng f → mask nhóm do GA chọn → g
                                                        [h; g] → MLP → 28 logits
```

Đầu tiên giữ nguyên encoder, tokenizer, embedding và kiến trúc xLSTM đã chọn.
Chuẩn hóa đặc trưng bằng tham số fit trên train; ghép với vector câu rồi dự đoán
đa nhãn. Đề xuất huấn luyện bằng BCEWithLogitsLoss; sigmoid khi suy luận.
Class weights nếu có chỉ tính từ train, so sánh với loss không trọng số.

Đặt ngưỡng dự đoán ban đầu cố định 0.5 cho mọi nhãn khi so sánh kiến trúc/mask.
Sau khi chốt mô hình mới hiệu chỉnh một ngưỡng chung trên dev; chỉ thử ngưỡng riêng
nếu đủ dữ liệu và có kiểm soát overfit. Kiểm tra local ngày 20/11 phát hiện 306 mẫu
neutral đi cùng nhãn cảm xúc, khác hướng dẫn gán nhãn. Baseline đề xuất giữ nguyên
nhãn nguồn và chưa ép decoder neutral độc quyền. Khi không có nhãn vượt ngưỡng,
giữ tập dự đoán rỗng và báo tỷ lệ; không suy neutral từ việc không khớp từ điển.

Các nhóm đặc trưng phiên bản đầu:

| Nhóm mask | Thành phần |
|---|---|
| F1 | Số lần khớp theo 27 nhãn cảm xúc, chuẩn hóa theo độ dài |
| F2 | Cờ hiện diện theo 27 nhãn, để giữ tín hiệu khi câu dài |
| F3 | Khớp cụm nhiều tiếng/thành ngữ theo nhãn |
| F4 | Khớp emoji/emoticon theo nhãn và số lượng tín hiệu chưa rõ nghĩa |
| F5 | Số tín hiệu cảm xúc trong phạm vi phủ định, theo nhãn |
| F6 | Marker mức độ và tương tác cục bộ với biểu thức cảm xúc |
| F7 | Tương phản mệnh đề, dấu câu lặp, kéo dài ký tự |
| F8 | Mức phủ, số match mơ hồ và cờ không có match |

Tên, thứ tự, chiều vector và lexicon_version phải cố định trong feature manifest.
Đếm một span đa nhãn cần quy tắc tường minh; có thể đóng góp vào từng nhãn ứng viên,
đồng thời tăng số match mơ hồ. Đây là thống kê tín hiệu, không phải phân bố xác suất.
Nhóm F1/F2/F3 có thể trùng thông tin có chủ đích để GA và ablation kiểm tra tính hữu ích.

Giai đoạn sau mới so sánh ghép đặc trưng ở từng token với embedding. Phương án đó
cần ánh xạ span–token chính xác và làm thay đổi đầu vào encoder, nên tốn công hơn
để tách tác động của từ điển khỏi thay đổi kiến trúc.

## Mở rộng GA theo hai bước

1. Cố định cấu hình xLSTM tốt hiện có, bổ sung chromosome gồm 8 bit chọn nhóm F1–F8.
   Cho phép mask toàn 0 làm đối chứng. Huấn luyện lại cùng quy trình cho mỗi mask.
2. Khi đã có tín hiệu cải thiện ổn định, kết hợp gene siêu tham số, gene block và
   gene mask. Khởi tạo bằng các cấu hình tốt từ bước 1 để giới hạn chi phí tìm kiếm.

GA chọn cấu hình/mask; trọng số mạng được tối ưu bằng backpropagation như hiện tại.
Chưa dùng một gene cho mỗi mục từ hoặc mỗi nhãn, tránh tăng mạnh không gian tìm kiếm.
Chỉ thêm gene chọn mức trọng số/rule khi đã có đối chứng chứng minh nhu cầu.

Fitness đề xuất: Macro-F1 trên tập search-validation nội bộ được tách từ train.
Khi điểm gần tương đương theo dung sai chốt trước, ưu tiên ít nhóm hoặc chi phí thấp
hơn. Nếu dùng hàm phạt số nhóm/GPU time thì hệ số phải được chốt và ghi rõ.

Dùng cùng ngân sách đánh giá và giới hạn tài nguyên khi so với random search;
ghi cả số cấu hình độc nhất, epoch thực tế và tổng GPU-hours. Cache cấu hình trùng,
xử lý cấu hình block không hợp lệ trước khi train, lưu seed và phiên bản từ điển.
Đánh giá lại ứng viên tốt trên nhiều seed; final đề xuất 3–5 seed nếu đủ tài nguyên.

## Tránh rò rỉ và overfit do tìm kiếm

- Giữ split chính thức nếu được cung cấp; chốt ID/hash trước khi làm thí nghiệm.
- Tách inner-train/search-validation từ train cho GA, phù hợp phân bố đa nhãn;
  kiểm tra mẫu trùng/gần trùng trước khi định nghĩa giao thức.
- Rút ứng viên từ inner-train trong vòng tìm kiếm; không đọc search-validation/dev/test
  để bổ sung mục từ, viết rule hoặc gán nhãn cho mục từ.
- Khi chốt thiết kế, fit lại từ điển thống kê/preprocessing trên train đầy đủ;
  dev chỉ dùng cho lựa chọn cuối/hiệu chỉnh đã định trước. Test giữ kín đến cuối.
- Nếu dùng nhãn train để ước lượng trọng số từ–cảm xúc, cần tạo đặc trưng out-of-fold
  cho các mẫu huấn luyện để nhãn của chính mẫu không tham gia tạo đặc trưng của nó.
  Dev/test dùng bản fit trên train; các fold nội bộ cũng phải tuân thủ ranh giới này.
- Pilot ưu tiên annotation từ điển được duyệt và không dùng trọng số học từ nhãn câu,
  giúp thiết kế đối chứng dễ kiểm tra hơn.
- Cache đặc trưng phải có split ID, lexicon hash, feature schema và preprocessing hash.
- Giữ test cuối cho toàn bộ biến thể đã chốt, không chọn phiên bản theo điểm test.

## Thực nghiệm cần có

| Mã | Cấu hình | Câu hỏi |
|---|---|---|
| A | xLSTM cấu hình cố định, không từ điển | Baseline nền |
| B | GA–xLSTM hiện tại, không từ điển | GA hiện tại đóng góp gì? |
| C | Kiến trúc/siêu tham số của B + toàn bộ nhóm từ điển | Từ điển có ích ở cấu hình cố định không? |
| D | Giữ kiến trúc/siêu tham số B, GA chỉ chọn nhóm từ điển | Chọn đặc trưng có ích hơn dùng tất cả không? |
| E | GA tìm chung block + siêu tham số + nhóm đặc trưng | Tìm kiếm chung có đáng chi phí không? |

Thêm random search cùng không gian/ngân sách với D hoặc E khi muốn kết luận về
ưu thế của GA. Giữ preprocessing, embedding, dữ liệu và training budget so sánh được.
Báo cáo Macro-F1 trên cả 28 nhãn, Micro-F1, F1/support từng nhãn, mean/std qua seed,
thời gian và bộ nhớ. Nếu báo Macro-F1 không gồm neutral, phải ghi là chỉ số bổ sung.

Phân tích thêm các nhóm có phủ định, emoji, nhiều cảm xúc và không có match. Không
chỉ nhìn accuracy hoặc hứa tăng F1 trước khi đo. Mô hình tham chiếu ngoài chỉ so điểm
khi khớp split, xử lý đầu ra, nhãn và cách tính metric.

## Phân phối dữ liệu

Dataset card hiển thị metadata MIT nhưng phần điều kiện sử dụng và repo tác giả
ghi phạm vi nghiên cứu phi lợi nhuận, cấm thương mại và tái phân phối dataset.
Vì có sự không thống nhất này, phương án repo hiện tại là chỉ lưu mã/cấu hình, trỏ
người dùng đến nguồn chính thức và chưa đưa câu gốc hoặc bản sửa đổi lên GitHub.
[Điều kiện tác giả công bố](https://github.com/ricardo-tran/ViGoEmotions#license).

Từ điển soạn độc lập cần provenance riêng. Không mặc định mọi biểu thức/định nghĩa
rút từ dataset đều được phép phát hành thành sản phẩm mới; phạm vi xuất bản của
artifact dẫn xuất cần được làm rõ trước khi phát hành. Đây là điểm cần kiểm tra
với chủ nguồn, chưa phải kết luận pháp lý về giấy phép áp dụng.

## Công việc G0 tiếp theo theo phương án này

1. Chốt taxonomy 28 ID từ bản ViGoEmotions đang dùng và đặc tả đa nhãn/neutral.
2. Đối chiếu mã GA–xLSTM hiện tại: input, pooling, output/loss, gene block và fitness.
3. Soạn 30 mẫu biểu thức cảm xúc riêng với tình huống đa nhãn, phủ định, emoji,
   biến thể và mỉa mai; giữ trạng thái candidate đến khi được duyệt.
4. Chốt schema annotation/marker và feature manifest F1–F8.
5. Chốt giao thức split, seed, metric, ngân sách và các đối chứng A–D trước khi train.

Đường dẫn mã/dữ liệu, split, tokenizer/embedding và GPU đã được đối chiếu trong
[báo cáo tích hợp local](local-integration-audit.md). Cần đo thời gian và VRAM của
luồng ViGoEmotions mới bằng smoke test trước khi chốt ngân sách GA.
