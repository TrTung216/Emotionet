# Quy tắc nghĩa, quan hệ và kiểm duyệt

**Cập nhật 23/11/2026:** 30 fixture tổng quát ở cuối tài liệu vẫn là candidate.
Bộ mẫu G0 miền cảm xúc [g0-emotion-v1](../../data/seeds/g0-emotion-v1/samples.jsonl)
kế thừa 30 quyết định nghĩa đã có trong seed v2; không phải review mới hoặc chứng
nhận độc lập. Quy tắc ánh xạ và trạng thái theo [đặc tả nghiên cứu](research-spec-v1.md).

## Phân biệt nghĩa

1. Xác định lemma, POS và cách dùng qua ví dụ.
2. Hai cách dùng có định nghĩa khác nhau thì giữ sense riêng. `đường` đi lại và
   `đường` tạo vị ngọt không chung concept; `mạng` máy tính và mạng đánh cá tương tự.
3. Chỉ gộp concept khi định nghĩa và phạm vi thực sự tương đương; không dựa riêng
   vào chuỗi giống nhau hay độ gần embedding.
4. Giữ abbreviation ở LexicalForm khi không gây nhập nhằng phạm vi nghĩa.
5. Định nghĩa ngắn, không tự lặp lại tên thay cho giải thích; ví dụ phân biệt được nghĩa.

## Quan hệ

| Predicate | Cách đọc subject → object | Đối xứng | Quy tắc |
|---|---|---|---|
| is_a | X là một loại Y | Không | Chỉ lớp/loại; không dùng cho cá thể hay ngành nghiên cứu |
| part_of | X là bộ phận của Y | Không | Nêu cấu trúc điển hình và phạm vi trong bằng chứng |
| subfield_of | X là lĩnh vực con của Y | Không | Cùng phạm vi học thuật; không thay bằng is_a |
| related_to | X liên quan đến Y | Có | Có giải thích quan hệ cụ thể, không suy ra phân cấp |
| antonym_of | X đối lập với Y trong một nghĩa | Có | Phải cùng trục nghĩa; không phải mọi cảm xúc khác nhau đều đối lập |
| same_as | X và Y là cùng khái niệm | Có | Chỉ xử lý trùng concept đã kiểm chứng; không suy luận tự động |

`same_as` chưa dùng trong mẫu G0. Không tự tạo cạnh bắc cầu/đảo thành dữ kiện
đã được duyệt. Các cạnh mẫu có lý do trong Evidence nhưng chưa có xác minh độc lập.

## Workflow

`candidate → needs_review → approved` hoặc `rejected`.

- Biên soạn: ghi định nghĩa, ví dụ, nguồn, cách tạo và phạm vi bằng chứng.
- Kiểm tra kỹ thuật: ID/FK, chuẩn hóa, cạnh trùng, chu trình, trường bắt buộc.
- Rà nguồn: đối chiếu locator với tài liệu thật, xác nhận điều kiện sử dụng.
- Rà ngữ nghĩa: xác nhận nghĩa, POS, alias, quan hệ và ví dụ.
- Người duyệt ghi danh tính, thời điểm, lý do và bằng chứng trong reviews.jsonl;
  chỉ duyệt khi cả nội dung và nguồn hợp lệ. Ưu tiên người duyệt khác người biên soạn.
- Nếu chỉ một người thực hiện, ghi rõ hạn chế; không mô tả đó là duyệt độc lập.
- Bản ghi rejected có thể quay lại candidate khi sửa và có sự kiện giải thích.
- Bản ghi approved đổi nội dung phải chuyển needs_review và duyệt lại.

## Phiếu duyệt từng mẫu

- [ ] Định nghĩa đúng, phạm vi rõ, không gộp nghĩa.
- [ ] Lemma, POS, form, ví dụ và sense liên kết đúng.
- [ ] Mỗi quan hệ đúng chiều và loại, không tạo chu trình.
- [ ] Bằng chứng đối chiếu được; method phản ánh cách tạo thực tế.
- [ ] Quyền sử dụng/phân phối được ghi rõ trong registry.
- [ ] Người duyệt, thời gian và lý do được ghi vào lịch sử.

30 mẫu G0 hiện là bản soạn có AI hỗ trợ, **không có mẫu nào đã approved**.
