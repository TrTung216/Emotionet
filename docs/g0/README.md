# G0 — Thiết kế

Ngày bắt đầu: 15/11/2026. Trạng thái: **đang thực hiện, chờ duyệt đặc tả và mẫu**.

Xem [báo cáo tiến độ và timeline công việc còn lại, cập nhật 21/11/2026](../reports/bao-cao-tien-do-va-timeline-2026-11-21.md).

Đã chuẩn bị [bảng duyệt 66 biểu thức seed](seed-source-review.md) từ đề xuất tự soạn,
đối chiếu hai file NRC/VnEmoLex người dùng tải. Dữ liệu nguồn nhập chỉ lưu local;
62 biểu thức có khớp nguồn. Đã nhập bản review v2: 66 seed được chấp nhận về nội dung,
phủ đủ 27 nhãn cảm xúc. Ba mục bổ sung có câu train đã xác minh; “hụt hẫng” dựa trên
định nghĩa duyệt thủ công và ví dụ tự soạn. Bộ seed nằm trong `data/local/reviewed-seeds-v2/`;
bản v1 được giữ nguyên. Đã nhập 10 nghĩa tách được duyệt cho 5 biểu
thức vào `data/local/sense-match-review-v1/accepted-split-senses.jsonl`.

Cập nhật 21/11/2026: đã tạo **66 entry, 71 sense, 71 synset khởi đầu**, mỗi synset
hiện có một sense thành viên; năm đề nghị gộp liên lemma được lưu riêng. Pilot
Word2Vec train-only truy vấn 48 synset, tạo 240 cặp ứng viên–synset (166 biểu thức).
Chưa thêm ứng viên tự động. Xem [kết quả và cách duyệt](synsets-and-expansion.md).

Đã nhập bản cập nhật review 155 lượt khớp trên 148 câu train: 143 matches_sense,
8 wrong_sense, 4 uncertain. Sáu mục chất lượng đã được chốt theo quyết định người
dùng, lưu tại [kết quả xử lý ngữ cảnh](../../data/local/quality-resolution-v1/resolved-contexts.jsonl).
Mọi ID và text đều khớp train; 149 dòng ngoài hàng chờ không đổi. Đây là mẫu rà lỗi
từ train, không phải gold set độc lập hoặc ước lượng accuracy; nhãn câu được lưu
riêng với nhãn sense để không tự suy một nhãn từ nhãn kia.

Chủ dự án đã quyết định **giữ bản v2 của mình làm bản chính** ngày 20/11/2026.
Review của Tâm và Hoàng cùng bảng đối chiếu chỉ dùng tham khảo; việc phân xử 21 mục
không còn là điều kiện để tiếp tục. Giữ nguyên nhãn, nghĩa và thông tin bằng chứng
của v2. Xem [quyết định chọn phiên bản](../../configs/seed-selection.json).

Kiểm tra độ phủ train: 60/66 seed khớp chuỗi, 3.036/16.531 câu (18,37%).
Xem [kết quả v2 và bước tiếp theo](seed-source-review.md#bộ-seed-v2-và-bước-tiếp-theo).

Cập nhật 20/11/2026: [đối chiếu mã GA–xLSTM, dữ liệu và hợp đồng tích hợp](local-integration-audit.md).
Đã xác minh mapping 28 nhãn và cấu trúc split; baseline hiện tại cần chuyển từ
bảy lớp một nhãn sang đa nhãn. Chính sách neutral được điều chỉnh theo dữ liệu local.

Người dùng đã xác định mục tiêu ViGoEmotions với GA tối ưu siêu tham số/block
xLSTM và muốn bổ sung chọn đặc trưng. Xem [đề xuất điều chỉnh G0](vigoemotions-ga-xlstm-proposal.md).
Các quyết định dự thảo và mẫu bên dưới là bản thiết kế tổng quát ban đầu;
schema cảm xúc và ưu tiên triển khai đang được đề xuất điều chỉnh theo mục tiêu này.

## Phạm vi và quyết định dự thảo

- Xây thư viện Python 3.11+, SQLite và JSONL; chưa làm web hoặc mô hình WSD.
- Tách LexicalEntry, LexicalForm, Sense, Concept, Relation, Evidence.
- Làm nguồn gốc và kiểm duyệt ngay trong schema; cảm xúc là lớp tùy chọn.
- Dùng 30 khái niệm thuộc công nghệ, sinh vật, đời sống và cảm xúc để thử schema.
  Đây là lựa chọn khởi đầu; chưa xác lập miền dữ liệu chính cho toàn bộ MVP.
- Dùng `candidate`, `needs_review`, `approved`, `rejected` thống nhất;
  chuyển ví dụ `pending` trong kế hoạch sang `candidate`.
- Mẫu được soạn bằng trợ lý AI: `method=ai_assisted_draft`, không tự duyệt.
- Chưa chọn giấy phép mã nguồn/dữ liệu; registry ghi rõ `undetermined`.

## Checklist nghiệm thu

- [x] Tạo cây thư mục dự án và lưu bản kế hoạch gốc.
- [x] Soạn use case và tiêu chí kiểm chứng hành vi.
- [x] Soạn schema v1, ID, tham chiếu, quy tắc chuẩn hóa và API mục tiêu.
- [x] Soạn quy tắc ngữ nghĩa, workflow và tiêu chí duyệt nguồn.
- [x] Chuẩn bị 30 concept cùng entry/form/sense/relation/evidence liên quan.
- [x] Cung cấp lệnh kiểm tra tính nhất quán bộ mẫu.
- [ ] Chủ dự án chốt phạm vi miền và đặc tả v1.
- [ ] Chủ dự án quyết định giấy phép mã nguồn và dữ liệu.
- [ ] Người biên soạn/người duyệt xác minh từng định nghĩa, quan hệ và nguồn.
- [ ] Có đủ 30 mẫu chuẩn được người duyệt chấp thuận, lưu lịch sử duyệt.

**G0 chỉ hoàn thành khi các mục duyệt ở trên hoàn tất.** Bộ kiểm tra kỹ thuật
không thay thế kiểm duyệt chuyên môn và không chuyển trạng thái dữ liệu.

Kết quả đã chạy và giới hạn kiểm tra: [báo cáo kỹ thuật G0](validation-report.md).

## Trình tự tiếp theo

1. Duyệt `data-model.md` và các ví dụ đa nghĩa trong danh mục mẫu.
2. Ghi quyết định nguồn/giấy phép tại `data/licenses/sources.csv`.
3. Bổ sung bằng chứng có thể đối chiếu; rà từng dòng JSONL và ghi review.
4. Chốt đặc tả; chuyển G1 để triển khai models, migration SQLite, nhập/xuất,
   lookup, đóng gói và kiểm thử. Matcher đầy đủ thuộc G3.

## Bàn giao G1

Ưu tiên các kiểm thử chấp nhận trong `use-cases.md`; không dùng 30 mẫu nháp
làm dữ liệu đã duyệt mặc định. Các module dự kiến: `models.py`, `storage.py`,
`normalize.py`, `api.py`, `relations.py`, `curation.py`, sau đó `matcher.py`
và `cli.py`. Chỉ tạo module khi triển khai chức năng tương ứng.
