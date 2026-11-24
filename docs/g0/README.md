# G0 — Thiết kế và bàn giao

Ngày bắt đầu: 15/11/2026. **Hoàn thành ngày 23/11/2026** theo phạm vi từ điển cảm xúc tiếng Việt cho ViGoEmotions và GA–xLSTM.

Tài liệu chính: [bàn giao G0](handoff-2026-11-23.md), [đặc tả nghiên cứu v1](research-spec-v1.md), [trạng thái nghiệm thu](../../configs/g0-handoff.json).

## Checklist nghiệm thu

- [x] Lưu cấu trúc dự án và kế hoạch gốc.
- [x] Xác định phạm vi miền cảm xúc và 12 use case có đầu ra kiểm chứng.
- [x] Đặc tả entry/form/sense/synset/relation/evidence/review/emotion/context cho G1.
- [x] Chốt quy tắc đa nghĩa, đa nhãn, alias, gộp nghĩa và provenance quan hệ.
- [x] Đóng gói 30 mẫu miền cảm xúc từ các quyết định seed v2 đã duyệt, phủ 27 nhãn.
- [x] Giữ bằng chứng, reviewer/thời điểm của nghĩa, ví dụ train và hash nguồn.
- [x] Ghi nhận quyền chia sẻ dữ liệu đã được chủ dự án cấp ngày 22/11.
- [x] Chủ dự án chọn giữ quyền chia sẻ hiện tại, chưa cấp thêm giấy phép tái sử dụng ngày 23/11.

Không phân xử lại review của Tâm/Hoàng: chủ dự án đã chọn seed v2 của mình. Không tự tạo lượt duyệt ngữ nghĩa mới để đóng checklist.

## Bộ mẫu và kiểm tra

- [Danh mục 30 mẫu](reviewed-samples-v1.md) và [JSONL đầy đủ](../../data/seeds/g0-emotion-v1/samples.jsonl): kế thừa review đã chốt; không phải gold set hay đánh giá độc lập mới.
- [Manifest](../../data/seeds/g0-emotion-v1/manifest.json): số lượng, taxonomy và hash nguồn/đầu ra.
- [30 fixture tổng quát cũ](../../data/seeds/g0/README.md): vẫn candidate để kiểm tra schema, không tự nâng approved. Bộ nghiệm thu thiết kế chuyển sang miền cảm xúc theo mục tiêu nghiên cứu.

```console
python scripts/prepare_g0_handoff.py --check
python scripts/validate_g0.py
```

Các mẫu giữ POS null khi chưa duyệt; reviewer nguồn là antigravity. Review câu thiếu danh tính/thời điểm được ghi rõ, không lấy ngày đóng gói thay ngày duyệt. Việc hoàn thành G0 không chứng nhận quyền cấp phép của nguồn ngoài hoặc độ chính xác mô hình.

## Bàn giao G1

Triển khai SQLite/FK/transaction, import/export, lookup, chuẩn hóa và đóng gói pip theo [đặc tả v1](research-spec-v1.md). Prototype matcher, 171 đặc trưng và head PyTorch không thay thế tiêu chí nghiệm thu G1–G4. Chưa chuyển giai đoạn bằng cách tự chạy thực nghiệm trong lượt hoàn thiện G0 này.

Lịch sử: [seed review](seed-source-review.md), [synset/embedding](synsets-and-expansion.md), [báo cáo tiến độ](../reports/bao-cao-tien-do-va-timeline-2026-11-21.md). Các snapshot lịch sử được giữ nguyên.
