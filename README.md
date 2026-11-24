# Emotionet

WordNet chuyên miền cảm xúc tiếng Việt: tổ chức từ/cụm từ theo nghĩa,
synset và quan hệ, kèm API và lớp chú giải cảm xúc.

## Trạng thái

Định hướng từ **24/11/2026**: ưu tiên xây và phát hành tài nguyên WordNet dùng
độc lập; GA–xLSTM chuyển sang đánh giá ứng dụng sau bản lõi. Xem
[kế hoạch v2 và timeline 12 tuần](docs/Ke_hoach_WordNet_cam_xuc_tieng_Viet.md).

Cập nhật **23/11/2026**: đã hoàn thành [G0](docs/g0/handoff-2026-11-23.md) và
[G1 — Core API](docs/g1/handoff-2026-11-23.md). Có SQLite, import/export giữ
nguyên snapshot, lookup theo nghĩa/alias, chuẩn hóa Unicode và package cài bằng
pip. **69/69 unit test đạt**; wheel đã chạy trong môi trường sạch không có
NumPy/PyTorch. Phiên bản hiện tại `0.1.0.dev0`, chưa phải release G5.

G0 có 30 mẫu kế thừa review đã chốt, phủ 27 nhãn. Chủ dự án chọn giữ quyền chia
sẻ hiện tại, chưa cấp thêm giấy phép tái sử dụng. Bước tiếp theo là **G2a — Profile
WordNet**: chốt POS, synset và quan hệ hai cấp, rồi chuẩn hóa bộ lõi và mở rộng
đến ≥300 synset cảm xúc đã duyệt. CLI phục vụ phát hành; gold set matcher và
GA–xLSTM thuộc giai đoạn ứng dụng G6.

## Dùng Core API

```console
python -m pip install .
```

```python
from emotionet import Emotionet

with Emotionet.open(":memory:", mode="research") as net:
    net.import_jsonl("data/local/seed-synsets-v2")
    hits = net.lookup("  KHÓ   CHỊU ")
    print(hits[0]["senses"][0]["sense"]["emotion_labels"])  # ['annoyance']
```

Xem [hướng dẫn G1](docs/g1/README.md) cho SQLite lưu lâu dài, export, chế độ
approved và phần cài đặt tùy chọn phục vụ ML.

## Dữ liệu nghiên cứu

Cập nhật **24/11/2026**: đã [tiếp nhận review G2](docs/g2/review-receipt-2026-11-24.md)
cho 66 synset và 18 cặp pilot hypernym/hyponym. Membership có 64 keep/2 revise;
pilot có 5 accept/4 revise/9 reject sau xác nhận của chủ dự án. Đã nhận thêm
29 quyết định quan hệ nguồn (27 accept/2 revise) và bản thảo profile WordNet.
[Đối chiếu mới nhất](docs/g2/wordnet-profile-audit-2026-11-24.md) còn ghi nhận
ID đích/POS chưa hoàn thiện, ba antonym cần đối soát và schema sense-level
chưa triển khai. Quyết định được lưu riêng, chưa áp dụng vào snapshot/graph.

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

Đã tạo **71 synset khởi đầu theo từng nghĩa**. Sau 5 lần gộp và bổ sung ứng viên,
snapshot v2 có **66 synset, 82 sense, 77 entry**. Pilot Word2Vec trên train tạo
**240 cặp ứng viên–synset (166 từ/cụm từ)**, đã có quyết định review; quan hệ v2
chưa đủ ID đích/provenance được API giữ ở trạng thái chờ rà.
Xem [bộ synset và kết quả mở rộng](docs/g0/synsets-and-expansion.md).

## Tài liệu

- [Kế hoạch hiện hành: WordNet cảm xúc tiếng Việt v2](docs/Ke_hoach_WordNet_cam_xuc_tieng_Viet.md)

- [Hướng dẫn cài đặt và dùng G1 Core API](docs/g1/README.md)
- [Bàn giao và kiểm chứng G1 ngày 23/11/2026](docs/g1/handoff-2026-11-23.md)
- Cập nhật 22/11/2026: chủ dự án xác nhận được phép chia sẻ và yêu cầu đưa
  `data/local/` lên Git bằng cách thông thường. Repo nay bao gồm review, snapshot
  synset và vector Word2Vec. Các ghi chú cũ về việc loại thư mục này khỏi Git
  mô tả trạng thái trước cập nhật; metadata lịch sử trong snapshot được giữ nguyên.
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
src/emotionet/       Core SQLite/API và prototype matcher/ML
data/seeds/g0/      JSONL mẫu thiết kế, toàn bộ đang candidate
data/licenses/      Registry nguồn và quyết định quyền sử dụng
data/evaluation/    Dành cho gold set độc lập
scripts/            Kiểm tra dữ liệu và công cụ phát triển
tests/              Unit test core, dữ liệu và tích hợp prototype
docs/g0/            Đặc tả và quy trình G0
docs/g1/            Hướng dẫn API và kết quả nghiệm thu G1
```

## Kiểm tra bộ mẫu G0

Yêu cầu Python 3.11+; không cần cài thư viện ngoài:

```console
python scripts/validate_g0.py
```

Lệnh kiểm tra cấu trúc và tính nhất quán của dữ liệu, không xác nhận độ đúng
ngữ nghĩa hoặc quyền phát hành. Công cụ này kiểm tra fixture G0 tổng quát gồm
candidate; core G1 có kiểm tra FK, provenance, checksum và chế độ approved riêng.

`scripts/prepare_g0_samples.py` đã được chạy để tạo bộ nháp ban đầu và sẽ từ chối
ghi đè nếu dữ liệu tồn tại. Chỉnh sửa/kiểm duyệt trực tiếp bản JSONL thay vì chạy lại.

Ngày 23/11/2026, chủ dự án chọn giữ quyền chia sẻ hiện tại và chưa cấp thêm giấy
phép tái sử dụng. Chưa gán giấy phép mở cho toàn repo; metadata/điều kiện nguồn
được giữ riêng. Xem [quyết định G0](configs/g0-handoff.json).
