# Tích hợp Emotionet với mã GA và xLSTM hiện tại

Ngày đối chiếu: 20/11/2026.

Mã tại `D:/NCKH_GA+LSTM_Emotion_Recognition` hiện huấn luyện UIT-VSMEC với bảy
lớp, một nhãn mỗi câu. Để dùng toàn bộ ViGoEmotions, cần thêm luồng huấn luyện
đa nhãn 28 đầu ra trước khi đo đóng góp của Emotionet. Điểm ghép đặc trưng phù
hợp là vector sau masked-mean pooling, ngay trước classifier head.

## Thành phần có thể tái sử dụng

Các đường dẫn mã dưới đây tương đối với thư mục GA–xLSTM của người dùng.

| Thành phần | Hiện trạng đọc từ mã | Thay đổi cần thiết |
|---|---|---|
| `scripts/compare_lstm_xlstm.py:70` | Dataset trả token IDs và một label_id | Đọc labels JSON, tạo tensor float32 `[batch, 28]` |
| `scripts/compare_lstm_xlstm.py:91` | Embedding học từ đầu; backbone LSTM hoặc mLSTM | Giữ encoder để có đối chứng cùng cấu hình |
| `scripts/compare_lstm_xlstm.py:111` | Mask padding, lấy trung bình vector token, head 7 lớp | Tách `encode(ids)`; ghép đặc trưng sau pooling và đổi head |
| `scripts/compare_lstm_xlstm.py:149` | Weighted CrossEntropyLoss và nhãn số nguyên | BCEWithLogitsLoss, đa nhãn; cân bằng lớp nếu dùng phải tính lại từ train |
| `scripts/compare_lstm_xlstm.py:123` | Metric 7 lớp, predict bằng argmax | Sigmoid, threshold, Macro/Micro-F1 và F1 từng nhãn |
| `scripts/sequence_variants.py:8` | sLSTM-only và hybrid mLSTM→sLSTM, head 7 lớp | Dùng chung đầu đa nhãn và feature interface |
| `scripts/controlled_models.py:42` | Backbone theo pattern l/m/s, projection và masked mean | Có thể dùng cho bước tìm kiếm kiến trúc sau pilot |
| `scripts/ga_search.py` | GA categorical tổng quát, callback evaluate, loại cấu hình trùng | Thêm gene chọn nhóm đặc trưng sau khi có evaluator đa nhãn |

Tokenizer hiện dùng SentencePiece unigram, fit trên train, chuẩn hóa NFC. Baseline
có vocab mục tiêu 4.000, max length 128, embedding 64, hai tầng, batch 32, float32.
Các cấu hình GA có thể thay những giá trị được khai báo trong search space.
Tokenizer/checkpoint UIT-VSMEC không được coi là tokenizer/checkpoint đã học trên
ViGoEmotions. Pilot mới nên fit tokenizer trên train ViGoEmotions tương ứng với
giao thức split; nếu tái sử dụng tokenizer cũ phải ghi là thí nghiệm transfer riêng.

## Phân biệt GA và quy trình thử block

`configs/ga_lstm_xlstm_comparison.json` khai báo sáu gene: embedding_dim, num_layers,
dropout, learning_rate, weight_decay và class_weight_alpha. GA này thay số tầng;
nhánh xLSTM trong runner đó là mLSTM-only. Cấu hình có 18 trial, proxy 5 epoch,
rerank top 2 trên hai seed.

Các mẫu mLSTM/sLSTM như mmss, msms nằm trong `configs/mechanism_controls.json`
và `scripts/control_protocol.py`. Quy trình hiện tại thử các pattern định trước,
sau đó lấy mẫu ngẫu nhiên. Chưa có gene pattern lai ghép/đột biến trong GA đã đọc.
Khi bổ sung tìm chung kiến trúc và đặc trưng, cần nối hai phần này tường minh và
đặt tên đúng cho từng thí nghiệm.

## Dữ liệu ViGoEmotions thực tế

Nguồn local: `D:/NCKH_GA+LSTM_Emotion_Recognition/data_external/ViGoEmotions`.
Revision trong manifest: `30f14fcef576a641929a3ec0cbc8194caa4f8d3d`.
Hash và số byte của README/train/val/test đều khớp manifest nguồn.

| Split | Số câu | Câu có nhiều nhãn phân biệt | Neutral cùng cảm xúc khác |
|---|---:|---:|---:|
| Train | 16.531 | 11.100 | 251 |
| Validation | 2.066 | 1.387 | 19 |
| Test | 2.067 | 1.372 | 36 |
| Tổng | 20.664 | 13.859 | 306 |

Schema CSV là `id,text,labels`; labels là chuỗi JSON chứa danh sách ID 0–27.
Không có ID trùng trong từng split, không có ID giao nhau giữa các split và không
có nhãn sai kiểu/ngoài miền trong lần kiểm tra. Có một mẫu test lặp lại ID nhãn;
multi-hot phải đánh dấu hiện diện, không cộng hai lần. Giữ nguyên CSV nguồn.

Sau chuẩn hóa NFC, chữ thường và khoảng trắng: train có ba dòng trùng vượt quá
lần đầu; không có nhóm trùng trong train mang tập nhãn khác nhau. Train–test có
một nhóm văn bản trùng, train–val và val–test không có giao nhau chính xác.
Chưa kiểm tra paraphrase hoặc cùng hội thoại. Chốt chính sách xử lý trước khi train:
giữ split gốc để đối chiếu và báo overlap; nếu loại mẫu giao nhau khỏi train,
tạo biến thể riêng có manifest và dùng thống nhất cho mọi mô hình. Không sửa test.

### Neutral cần theo dữ liệu thực tế

Đề xuất ngày 15/11 dựa trên hướng dẫn gán nhãn nói neutral độc quyền. Bản local
có 306 câu không theo quy tắc này. Vì vậy baseline chính nên giữ nhãn gốc và cho
phép 28 sigmoid độc lập, chưa thêm bộ giải mã ép neutral độc quyền.

Biến thể sửa neutral, nếu cần, là một nghiên cứu độ nhạy riêng với quy tắc được
chốt trước và báo rõ không còn cùng gold labels. Không tự động xóa các nhãn đang có.
Ngưỡng đầu tiên là 0.5; hiệu chỉnh trên dev sau khi chốt giao thức, không dùng test
để chọn threshold. Nếu không có nhãn vượt ngưỡng, giữ tập dự đoán rỗng trong baseline
threshold thuần và báo tỷ lệ; không tự suy neutral từ việc không khớp từ điển.

### Lịch sử dùng test

`configs/external_vigo_protocol.json` quy định đánh giá zero-shot trên tập con sáu
nhãn đơn, ánh xạ sang UIT-VSMEC. Repo hiện có artifacts external_runs và
external_verification; thư mục dữ liệu có evaluations/mechanism_controls.
Vì test ViGoEmotions đã có artifacts đánh giá trước, không mô tả nó là tập test
hoàn toàn mới chưa từng được đánh giá. Kết quả sáu nhãn đơn không so trực tiếp với
Macro-F1 của bài toán đa nhãn 28 đầu ra. Điểm số cũ không được dùng để chọn mục từ.

## Hợp đồng ghép đặc trưng đề xuất

```text
ids:            int64   [B, T]
targets:        float32 [B, 28]
features:       float32 [B, F]
group_mask:     bool    [8]
pooled:         float32 [B, D]
logits:         float32 [B, 28]
```

Mapper nhóm cần chuyển tám bit thành mask đúng các cột trong feature manifest;
không broadcast trực tiếp tám bit lên F cột. Encoder có thể trả `pooled` qua
`encode(ids)`, rồi head nhận `concat(pooled, masked_features)`. Với mask toàn 0,
nhánh đặc trưng phải đóng góp bằng 0. Vẫn giữ mô hình không có nhánh đặc trưng làm
đối chứng vì thêm lớp/projection có thể thay đổi số tham số dù đầu vào là zero.

Emotionet nhận văn bản Unicode gốc, trả đặc trưng kèm lexicon_version và
feature_schema_version. Nếu xLSTM cắt câu ở T token, phải chốt phạm vi đặc trưng:
pilot ưu tiên cùng đoạn văn bản encoder nhìn thấy, dùng offset tokenizer hoặc
giới hạn văn bản chung trước hai nhánh. Không âm thầm để từ điển đọc phần cuối
mà baseline đã bị cắt rồi quy toàn bộ cải thiện cho tri thức cảm xúc.

## Tài nguyên và thứ tự triển khai

Máy hiện có NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4.096 MiB VRAM. Bắt đầu smoke
test một batch, một bước forward/backward ở embedding 64 và max length 128;
thử batch 8 hoặc 16 rồi đo peak VRAM và thời gian. Đây là cấu hình khởi đầu để đo,
không phải bảo đảm đủ bộ nhớ. Backend sLSTM vanilla đang tắt automatic mixed
precision; không bật AMP cho toàn bộ stack trước khi kiểm tra tương thích.

1. Chốt mapping và chính sách nhãn: [cấu hình 28 nhãn](../../configs/vigoemotions-labels.json).
2. Thêm loader multi-hot, loss/metrics đa nhãn và smoke test, dùng runner mới.
3. Soạn schema annotation cảm xúc và 30 biểu thức pilot; kiểm duyệt nguồn/ngữ nghĩa.
4. Triển khai matcher và feature manifest F1–F8, ghép sau pooling.
5. Chạy baseline không từ điển và cùng cấu hình có từ điển, sau đó GA chọn nhóm.

## Tái chạy kiểm tra dữ liệu

Từ `D:/Emotionet`, dùng Python 3.11+, không cần cài thư viện ngoài:

```powershell
python scripts/audit_vigoemotions.py --data-dir 'D:\NCKH_GA+LSTM_Emotion_Recognition\data_external\ViGoEmotions' --output reports/g0/vigoemotions-audit.json
python -m unittest discover -s tests -p 'test_audit_vigoemotions.py'
```

[Báo cáo JSON](../../reports/g0/vigoemotions-audit.json) chỉ chứa số liệu tổng hợp
và hash file, không xuất câu gốc hoặc dự đoán từng dòng. Chưa chạy huấn luyện mới
hoặc chỉnh sửa repo GA–xLSTM trong lần đối chiếu này.
