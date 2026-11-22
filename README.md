# Emotionet

Thư viện từ vựng–ngữ nghĩa tiếng Việt, hỗ trợ từ/cụm từ, đa nghĩa,
khái niệm, quan hệ và lớp cảm xúc tùy chọn.

## Trạng thái

Đang thực hiện **G0 — thiết kế**. Đã có cấu trúc dự án, đặc tả v1 dạng
dự thảo và 30 khái niệm mẫu chờ kiểm duyệt. Chưa có API/CLI hoạt động,
chưa phát hành dữ liệu và chưa đạt mục tiêu 300 khái niệm của MVP.

Đã nhập bản review seed v2: **66 mục được chấp nhận về nội dung**, phủ đủ 27 nhãn
cảm xúc ViGoEmotions. 60 seed khớp chuỗi trong train, bao phủ 18,37% số câu;
đây chưa phải kết quả đánh giá nhận diện cảm xúc. Xem
[kết quả và lịch sử nhập review](docs/g0/seed-source-review.md).

Theo quyết định của chủ dự án ngày 20/11/2026, **giữ bản seed v2 của chủ dự án làm
bản chính**. Hai bản review của Tâm và Hoàng cùng bảng đối chiếu được lưu tham khảo;
không yêu cầu phân xử 21 mục để tiếp tục. Quyết định lưu tại
[seed-selection.json](configs/seed-selection.json).

Đã nhập **10 nghĩa tách được duyệt cho 5 biểu thức** và kết quả review 155 lượt
khớp từ/câu (148 câu train khác nhau). Sáu mục chất lượng đã được người dùng chốt;
bản review mới có 143 matches_sense, 8 wrong_sense, 4 uncertain. Giữ riêng nhãn
sense và nhãn toàn câu; đây là mẫu rà lỗi từ train, chưa dùng như gold set.

Đã tạo **71 synset khởi đầu theo từng nghĩa**, kèm 5 đề nghị gộp. Pilot Word2Vec
trên train tạo **240 cặp ứng viên–synset (166 từ/cụm từ)**, toàn bộ chờ duyệt.
Xem [bộ synset và kết quả mở rộng](docs/g0/synsets-and-expansion.md).

## Tài liệu

- [Báo cáo tiến độ và timeline đến 07/02/2027 (cập nhật 21/11/2026)](docs/reports/bao-cao-tien-do-va-timeline-2026-11-21.md)
- [Synset khởi đầu và mở rộng bằng embedding](docs/g0/synsets-and-expansion.md)
- [Chọn seed từ NRC và VnEmoLex đã tải](docs/g0/seed-source-review.md)
- [Kết quả đối chiếu mã GA–xLSTM và ViGoEmotions local](docs/g0/local-integration-audit.md)
- [Đề xuất theo mục tiêu ViGoEmotions + GA–xLSTM](docs/g0/vigoemotions-ga-xlstm-proposal.md)
- [Kế hoạch gốc](docs/Ke_hoach_xay_dung_Emotionet.md)
- [Theo dõi G0 và các quyết định](docs/g0/README.md)
- [Use case và tiêu chí nghiệm thu](docs/g0/use-cases.md)
- [Đặc tả dữ liệu v1](docs/g0/data-model.md)
- [Quy tắc ngữ nghĩa và kiểm duyệt](docs/g0/curation.md)
- [Nguồn và giấy phép](docs/g0/sources-and-licenses.md)
- [Danh mục 30 mẫu](docs/g0/sample-catalog.md)

## Cấu trúc

```text
src/emotionet/       Mã thư viện (khung ban đầu, triển khai tại G1)
data/seeds/g0/      JSONL mẫu thiết kế, toàn bộ đang candidate
data/licenses/      Registry nguồn và quyết định quyền sử dụng
data/evaluation/    Dành cho gold set độc lập
scripts/            Kiểm tra dữ liệu và công cụ phát triển
tests/              Dành cho kiểm thử phần mềm từ G1
docs/g0/            Đặc tả và quy trình G0
```

## Kiểm tra bộ mẫu G0

Yêu cầu Python 3.11+; không cần cài thư viện ngoài:

```console
python scripts/validate_g0.py
```

Lệnh kiểm tra cấu trúc và tính nhất quán của dữ liệu, không xác nhận độ đúng
ngữ nghĩa hoặc quyền phát hành. Công cụ hiện kiểm tra snapshot G0 chỉ gồm candidate;
trình kiểm tra lịch sử duyệt sẽ được triển khai tại G1. Việc đóng gói bằng pip
và API công khai thuộc G1.

`scripts/prepare_g0_samples.py` đã được chạy để tạo bộ nháp ban đầu và sẽ từ chối
ghi đè nếu dữ liệu tồn tại. Chỉnh sửa/kiểm duyệt trực tiếp bản JSONL thay vì chạy lại.

Giấy phép mã nguồn và dữ liệu đang chờ chủ dự án quyết định; chưa gán giấy phép.
