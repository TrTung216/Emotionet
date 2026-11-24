# G1 — Core API

Ngày bàn giao: **23/11/2026**. G1 triển khai API Python và SQLite theo
[đặc tả G0](../g0/research-spec-v1.md). Phiên bản package `0.1.0.dev0` là bản
phát triển, chưa phải bản phát hành G5 `v0.1.0`.

## Cài đặt

Python **3.10+**; đã kiểm chứng trên Python 3.11.6 / Windows. Tại thư mục repo:

```console
python -m pip install .
```

Core dùng thư viện chuẩn, không cần NumPy hoặc PyTorch. Cài `.[features]` khi cần
bộ đặc trưng hoặc `.[ml]` khi cần head/dataset PyTorch; chọn bản PyTorch phù hợp
môi trường của bạn. Các tên import prototype như `FeatureExtractor`,
`EmotionetClassifierHead` được giữ qua lazy import. Wheel chỉ chứa mã thư viện;
snapshot dữ liệu đọc từ đường dẫn riêng trong repo.

Để build/cài offline bằng bộ setuptools và wheel đã có:

```console
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist .
python -m pip install --no-index --no-deps dist/emotionet-0.1.0.dev0-py3-none-any.whl
```

Việc đóng gói không cấp thêm giấy phép tái sử dụng. Giữ quyết định trong
[bàn giao G0](../g0/handoff-2026-11-23.md) và
[quyền chia sẻ của chủ dự án](../../configs/data-sharing.json).

## Dùng với snapshot v2

Chạy ví dụ từ thư mục repo. Database mới được tạo khi mở; thư mục cha phải tồn tại.

```python
from emotionet import Emotionet

with Emotionet.open("data/local/emotionet-v2.sqlite", mode="research") as net:
    # Chỉ import một lần cho database này.
    if not net.manifest:
        net.import_jsonl("data/local/seed-synsets-v2")

    hits = net.lookup("  KHÓ   CHỊU ")
    for entry in hits:
        for item in entry["senses"]:
            sense = item["sense"]
            print(sense["sense_id"], sense["gloss"], sense["emotion_labels"])

    concept_id = hits[0]["senses"][0]["sense"]["synset_id"]
    concept = net.get_concept(concept_id)
    proposals = net.relations(concept_id, direction="both")
    print(net.stats())
    # Đường dẫn export phải chưa tồn tại, kể cả thư mục rỗng.
    net.export_jsonl("data/local/emotionet-v2-export")
```

Kết quả snapshot v2: **77 entry, 82 sense, 66 concept/synset, 90 evidence,
29 relation**. Nguồn v2 không có `forms.jsonl`, nên số form lưu vật lý là 0.
Lookup cung cấp `derived_forms` canonical từ lemma với ID xác định
`derived:canonical:<entry_id>`, đánh dấu `derived=True`; không tạo một lượt duyệt
hoặc sửa file nguồn. Fixture G0 tổng quát có 35 form lưu vật lý, gồm alias.

## Hợp đồng API

| Hàm | Hành vi |
|---|---|
| `Emotionet.open(path=":memory:", mode="approved")` | Mở SQLite, bật FK, kiểm tra phiên bản schema. `with` tự đóng kết nối. |
| `import_jsonl(directory)` | Nhập snapshot vào DB rỗng trong một transaction; trả số lượng. Lỗi rollback toàn bộ, có thể thử lại. |
| `lookup(text)` | NFC + casefold + gom khoảng trắng; giữ dấu tiếng Việt. Trả list entry, form, mọi sense hợp lệ và evidence. Không có mục từ trả `[]`. |
| `get_concept(id)` | Trả concept gốc, sense và evidence; ID không tồn tại/bị lọc trả `None`. Synset là concept trong profile cảm xúc. |
| `relations(id, predicate=None, direction="out")` | `out`, `in`, `both`; trả record gốc, `resolved`, `state`, evidence. Không suy cạnh mới. |
| `export_jsonl(directory, mode=None)` | Xuất toàn bộ snapshot giữ nguyên byte, mặc định theo mode của kết nối; không ghi đè. |
| `manifest`, `stats()` | Bản sao manifest và số lượng vật lý, kể cả record bị lọc bởi mode approved. |
| `publication_issues()` | Danh sách lý do snapshot chưa qua cổng xuất approved. |
| `close()` | Đóng kết nối. |

`lookup` trả envelope `entry`, `forms`, `derived_forms`, `senses`, `evidence`.
Mỗi phần tử `senses` chứa `sense`, `concept`, `evidence`, `concept_evidence`.
Các record nguồn giữ nguyên trường mở rộng, null, review và nhãn; API không gộp
nhãn đa nghĩa vào một sense. Thứ tự kết quả theo ID để tái lập, không phải xếp hạng
độ đúng. `normalize_text` cũng được export trực tiếp từ package.

## Snapshot và tính toàn vẹn

- Hỗ trợ `emotionet_research_seed_synsets_v1/v2` dùng `synsets.jsonl` và profile
  G0 `schema_version=1` dùng `concepts.jsonl`. Thư mục phẳng cần `manifest.json`,
  entries/senses/evidence và một trong hai file concept. Forms/relations tùy chọn
  khi manifest không khai báo số lượng khác 0. Không nhận symlink hoặc thư mục con.
- JSON sai, khóa JSON trùng, ID trùng, normalized form không khớp, FK thiếu,
  evidence thiếu, danh sách membership mâu thuẫn, số lượng hoặc hash sai đều bị
  từ chối. Kiểm tra chu trình riêng cho `is_a`, `part_of`, `subfield_of`.
- Một DB giữ **một snapshot bất biến**. Phiên bản mới dùng DB mới; không có API sửa
  record hay merge ghi đè. Các mapping trong `applied_merges.json` và toàn bộ file
  bổ sung được lưu nguyên byte cùng checksum; không tự phân giải ID cũ sang mới.
- JSONL phụ như reviews/emotions được lưu và kiểm tra cú pháp, chưa có API biên
  soạn hoặc validator ngữ nghĩa riêng. Export approved từ chối các JSONL phụ có
  dữ liệu mà core chưa kiểm chứng được. Nguồn ngoài thư mục import không tự được
  đóng gói; khi chia sẻ bản nghiên cứu, giữ kèm các quyết định quyền của repo.
- V1 lịch sử có CSV review đã đổi sau khi lập manifest: import sẽ báo checksum
  sai. Không sửa hash cũ để che thay đổi; dùng v2 đã xác minh hoặc tạo một snapshot
  phiên bản mới với provenance rõ ràng.
- Export ghi staging trước khi công bố. Windows đổi tên cả thư mục; trên POSIX
  đích được tạo độc quyền rồi chuyển từng file, nên không cam kết xuất nguyên tử
  nếu tiến trình bị dừng giữa chừng. Cả hai từ chối đích đã tồn tại.

## Research và approved

`research` phải chọn rõ; trả dữ liệu với trạng thái lịch sử. Các relation v2
chỉ có `object_term` được trả `resolved=False`, `state="needs_review"`; không tự
gán concept đích bằng cách đoán lemma. Muốn tìm hai chiều của một cạnh đã phân
giải, dùng `direction="both"`; API không tạo inverse hay transitive closure.

`approved` mặc định chỉ hiện record có trạng thái approved, reviewer, reviewed_at
không trống và evidence cũng có review approved. Lookup kiểm cả entry, sense,
concept và alias được dùng. `accepted_as_submitted` không tự chuyển thành approved.
Do vậy snapshot nghiên cứu hiện tại tra ở mode này sẽ trả rỗng; đây là hành vi
được thiết kế, không phải mất dữ liệu.

Export approved kiểm tra cả snapshot, không âm thầm xuất một phần: phải có
`manifest.publication_status="cleared"`, mọi record đủ review/evidence, không có
record khai báo hạn chế publication và không có relation chưa phân giải.
Đây là kiểm tra khai báo đã lưu, không xác minh pháp lý độc lập hay tự cấp giấy
phép. Research export vẫn giữ `not_cleared` lịch sử và được phép trong phạm vi
chia sẻ chủ dự án đã chọn. Lỗi xuất trả `PublicationError`; dữ liệu lỗi trả
`SnapshotError`; đích tồn tại trả `FileExistsError`.

## Kiểm thử và phạm vi tiếp theo

```console
python -m unittest discover -s tests -v
python scripts/smoke_test_core_api.py
```

Smoke test yêu cầu package đã cài, không thêm `src` vào đường dẫn import, in rõ
vị trí package đang dùng. Kết quả nghiệm thu tại
[báo cáo G1](handoff-2026-11-23.md).

G1 chưa gồm HTTP service, CLI sản phẩm, WSD, sửa triệt để matcher hoặc train
encoder xLSTM. G2 cần mở rộng lên ≥300 concept đã duyệt có provenance; G3 xây
gold set và đánh giá matcher; G4 kiểm chứng lớp cảm xúc và tích hợp encoder thật.
