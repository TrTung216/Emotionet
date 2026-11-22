"""Create the initial G0 drafts once; refuse to overwrite existing review work."""

import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "seeds" / "g0"

# Original AI-assisted drafts, not verified dictionary entries.
SAMPLES = [
    ("trí tuệ nhân tạo", "trí tuệ nhân tạo", "NOUN", "computer_science", "Lĩnh vực nghiên cứu và xây dựng hệ thống thực hiện các nhiệm vụ liên quan đến trí thông minh.", "Cô ấy nghiên cứu trí tuệ nhân tạo.", ["AI"]),
    ("học máy", "học máy", "NOUN", "computer_science", "Lĩnh vực xây dựng phương pháp để hệ thống học quy luật từ dữ liệu nhằm thực hiện nhiệm vụ.", "Nhóm dùng học máy để phân loại văn bản.", ["ML"]),
    ("khoa học máy tính", "khoa học máy tính", "NOUN", "computer_science", "Ngành nghiên cứu tính toán, thuật toán và các hệ thống xử lý thông tin.", "Anh ấy học khoa học máy tính.", ["CS"]),
    ("máy tính", "máy tính", "NOUN", "computing", "Thiết bị có khả năng thực hiện chương trình để xử lý và lưu trữ dữ liệu.", "Máy tính đang chạy chương trình.", []),
    ("phần mềm", "phần mềm", "NOUN", "computing", "Chương trình và các thành phần liên quan dùng để điều khiển hoặc thực hiện công việc trên hệ thống máy tính.", "Phần mềm này hỗ trợ soạn văn bản.", []),
    ("phần cứng", "phần cứng", "NOUN", "computing", "Các thành phần vật lý của một hệ thống máy tính.", "Kỹ thuật viên kiểm tra phần cứng.", []),
    ("mạng máy tính", "mạng", "NOUN", "computing", "Hệ thống các thiết bị tính toán được kết nối để trao đổi dữ liệu.", "Mạng trong phòng máy bị gián đoạn.", []),
    ("mạng đánh cá", "mạng", "NOUN", "daily_life", "Dụng cụ gồm các sợi đan thành mắt dùng để bắt cá.", "Người ngư dân vá mạng trước chuyến ra khơi.", []),
    ("Internet", "Internet", "PROPN", "computing", "Hệ thống kết nối các mạng máy tính trên phạm vi toàn cầu sử dụng bộ giao thức Internet.", "Tôi tìm tài liệu trên Internet.", []),
    ("động vật", "động vật", "NOUN", "biology", "Sinh vật thuộc giới Động vật, có cơ thể đa bào và lấy chất hữu cơ từ nguồn khác làm dinh dưỡng.", "Khu rừng có nhiều loài động vật.", []),
    ("động vật có vú", "động vật có vú", "NOUN", "biology", "Nhóm động vật có xương sống mà con cái có tuyến sữa để nuôi con.", "Cá voi là động vật có vú.", []),
    ("mèo", "mèo", "NOUN", "biology", "Loài động vật có vú thuộc họ Mèo thường được nuôi trong nhà làm bạn hoặc bắt chuột.", "Con mèo ngủ cạnh cửa sổ.", []),
    ("chó", "chó", "NOUN", "biology", "Loài động vật có vú thuộc họ Chó đã được thuần hóa, thường được nuôi làm bạn hoặc hỗ trợ con người.", "Con chó chạy ra sân.", []),
    ("chim", "chim", "NOUN", "biology", "Nhóm động vật có xương sống có lông vũ, mỏ và hai chi trước biến đổi thành cánh.", "Chim làm tổ trên cây.", []),
    ("cây", "cây", "NOUN", "biology", "Thực vật thường có rễ, thân và lá; trong nghĩa này không chỉ vật dài dùng làm đơn vị đếm.", "Cây trước nhà đang ra lá.", []),
    ("hoa", "hoa", "NOUN", "biology", "Cơ quan sinh sản của thực vật có hoa, thường mang các bộ phận tạo giao tử.", "Hoa của cây bắt đầu nở.", []),
    ("lá", "lá", "NOUN", "biology", "Cơ quan của cây thường mọc từ thân hoặc cành, thường đảm nhiệm quang hợp và trao đổi khí.", "Lá cây chuyển màu vàng.", []),
    ("rễ", "rễ", "NOUN", "biology", "Cơ quan của cây thường giúp bám vào giá thể và hấp thu nước cùng chất khoáng.", "Rễ cây lan trong đất.", []),
    ("phương tiện giao thông", "phương tiện giao thông", "NOUN", "transport", "Phương tiện được sử dụng để vận chuyển người hoặc hàng hóa trong hoạt động giao thông.", "Xe buýt là một phương tiện giao thông.", []),
    ("xe đạp", "xe đạp", "NOUN", "transport", "Phương tiện thường có hai bánh, vận hành chủ yếu bằng lực đạp của người đi.", "Em đạp xe đạp đến trường.", []),
    ("ô tô", "ô tô", "NOUN", "transport", "Phương tiện cơ giới đường bộ thường có từ bốn bánh, dùng để chở người hoặc hàng hóa.", "Chiếc ô tô dừng trước cổng.", []),
    ("đường đi", "đường", "NOUN", "daily_life", "Lối hoặc dải không gian được dùng cho người và phương tiện đi lại.", "Con đường dẫn vào làng.", []),
    ("đường ăn", "đường", "NOUN", "food", "Chất tạo vị ngọt dùng trong thực phẩm, thường ở dạng tinh thể và thường chứa chủ yếu sucrose.", "Tôi cho một thìa đường vào trà.", []),
    ("đá (vật chất)", "đá", "NOUN", "geology", "Vật chất tự nhiên rắn cấu tạo từ một hoặc nhiều khoáng vật, thường tạo thành khối.", "Viên đá nằm cạnh suối.", []),
    ("đá (hành động)", "đá", "VERB", "daily_life", "Dùng chân tác động vào một vật bằng một động tác nhanh và có lực.", "Bạn ấy đá quả bóng về phía khung thành.", []),
    ("vui", "vui", "ADJ", "emotion", "Có trạng thái cảm xúc dễ chịu khi gặp điều phù hợp mong muốn hoặc đem lại sự hài lòng.", "Tôi rất vui khi gặp lại bạn.", []),
    ("buồn", "buồn", "ADJ", "emotion", "Có trạng thái cảm xúc không vui, thường gắn với mất mát, thất vọng hoặc thiếu điều mong muốn.", "Cô ấy buồn vì phải chia tay bạn.", []),
    ("giận", "giận", "VERB", "emotion", "Có cảm xúc bực bội hoặc bất bình đối với người hay sự việc bị cho là không phù hợp.", "Anh ấy giận vì lời hứa bị quên.", []),
    ("sợ", "sợ", "VERB", "emotion", "Có cảm xúc lo ngại trước điều được cảm nhận là nguy hiểm hoặc có thể gây hại.", "Em sợ khi nghe tiếng động lớn.", []),
    ("ngạc nhiên", "ngạc nhiên", "ADJ", "emotion", "Có trạng thái bất ngờ trước điều khác với dự đoán hoặc hiểu biết trước đó.", "Tôi ngạc nhiên trước kết quả này.", []),
]

# The last column records the draft rationale, not an external citation.
RELATIONS = [
    (2, "subfield_of", 1, "Học máy được đề xuất là lĩnh vực con của trí tuệ nhân tạo; cần người duyệt xác minh phạm vi."),
    (1, "subfield_of", 3, "Trí tuệ nhân tạo được xét trong phạm vi khoa học máy tính; cần rà phạm vi liên ngành."),
    (12, "is_a", 11, "Mèo trong sense động vật nuôi thuộc nhóm động vật có vú."),
    (13, "is_a", 11, "Chó trong sense động vật nuôi thuộc nhóm động vật có vú."),
    (11, "is_a", 10, "Động vật có vú là một nhóm động vật."),
    (14, "is_a", 10, "Chim là một nhóm động vật; khả năng bay không phải điều kiện định nghĩa."),
    (16, "part_of", 15, "Hoa là bộ phận của cây có hoa; không khẳng định mọi cây đều có hoa."),
    (17, "part_of", 15, "Lá là bộ phận của cây trong cấu trúc điển hình, không khẳng định mọi cây đều có lá ở mọi thời điểm."),
    (18, "part_of", 15, "Rễ là bộ phận của cây trong cấu trúc điển hình; cần rà các ngoại lệ sinh học."),
    (20, "is_a", 19, "Xe đạp được phân loại là phương tiện giao thông trong nghĩa đã chọn."),
    (21, "is_a", 19, "Ô tô được phân loại là phương tiện giao thông trong nghĩa đã chọn."),
    (5, "related_to", 6, "Phần mềm thực thi trên phần cứng; đây không phải quan hệ đồng nghĩa."),
    (7, "related_to", 9, "Internet kết nối các mạng máy tính; không dùng is_a để đồng nhất mạng bất kỳ với Internet."),
    (26, "antonym_of", 27, "Vui và buồn đối lập trên trục trạng thái cảm xúc trong các sense đang xét; cần kiểm duyệt ngôn ngữ."),
]


def normalize(value):
    return " ".join(unicodedata.normalize("NFC", unicodedata.normalize("NFC", value).casefold()).split())


def main():
    catalog = ROOT / "docs" / "g0" / "sample-catalog.md"
    names = ("concepts", "entries", "forms", "senses", "relations", "evidence", "emotions", "reviews")
    targets = [DEST / f"{name}.jsonl" for name in names] + [DEST / "manifest.json", catalog]
    if any(path.exists() for path in targets):
        raise SystemExit("Refusing to overwrite existing G0 drafts or review work.")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    common = dict(status="candidate", created_at=timestamp, updated_at=timestamp, reviewer=None, reviewed_at=None)
    records = {name: [] for name in names}
    entry_map = {}
    catalog_rows = []

    def form(entry_id, surface, form_type, evidence):
        records["forms"].append(dict(common, form_id=f"frm_{len(records['forms']) + 1:06d}", entry_id=entry_id,
                                     surface=surface, normalized_form=normalize(surface), form_type=form_type,
                                     evidence_ids=[evidence]))

    for number, (label, lemma, pos, domain, definition, example, aliases) in enumerate(SAMPLES, 1):
        concept_id, sense_id, evidence_id = f"con_{number:06d}", f"sen_{number:06d}", f"evd_{number:06d}"
        records["evidence"].append(dict(common, evidence_id=evidence_id, source_id="src_g0_draft",
                                        locator=f"data/seeds/g0/concepts.jsonl#{concept_id}", excerpt=None,
                                        method="ai_assisted_draft"))
        records["concepts"].append(dict(common, concept_id=concept_id, preferred_label=label,
                                        definition=definition, domain=domain, evidence_ids=[evidence_id]))
        key = (normalize(lemma), pos)
        if key not in entry_map:
            entry = dict(common, entry_id=f"lex_{len(entry_map) + 1:06d}", lemma=lemma, lang="vi", pos=pos,
                         normalized_form=normalize(lemma), evidence_ids=[evidence_id])
            entry_map[key] = entry
            records["entries"].append(entry)
            form(entry["entry_id"], lemma, "canonical", evidence_id)
        else:
            entry = entry_map[key]
            entry["evidence_ids"].append(evidence_id)
        records["senses"].append(dict(common, sense_id=sense_id, entry_id=entry["entry_id"],
                                      concept_id=concept_id, gloss=definition, examples=[example], evidence_ids=[evidence_id]))
        for alias in aliases:
            form(entry["entry_id"], alias, "abbreviation", evidence_id)
        # A disambiguated concept label can be an independently searchable entry.
        if label in {"mạng máy tính", "mạng đánh cá", "đường đi", "đường ăn"}:
            extra = dict(common, entry_id=f"lex_{len(entry_map) + 1:06d}", lemma=label, lang="vi", pos=pos,
                         normalized_form=normalize(label), evidence_ids=[evidence_id])
            entry_map[(normalize(label), pos)] = extra
            records["entries"].append(extra)
            form(extra["entry_id"], label, "canonical", evidence_id)
            records["senses"].append(dict(common, sense_id=f"sen_{number + 100:06d}", entry_id=extra["entry_id"],
                                          concept_id=concept_id, gloss=definition, examples=[example], evidence_ids=[evidence_id]))
        catalog_rows.append(f"| {concept_id} | {label} | {lemma} | {pos} | candidate |")

    for number, (subject, predicate, target, rationale) in enumerate(RELATIONS, 1):
        evidence_id = f"evd_{len(SAMPLES) + number:06d}"
        rel_id = f"rel_{number:06d}"
        records["evidence"].append(dict(common, evidence_id=evidence_id, source_id="src_g0_draft",
                                        locator=f"data/seeds/g0/relations.jsonl#{rel_id}", excerpt=None,
                                        method="ai_assisted_draft", rationale=rationale))
        records["relations"].append(dict(common, rel_id=rel_id, subject_id=f"con_{subject:06d}",
                                         predicate=predicate, object_id=f"con_{target:06d}", evidence_ids=[evidence_id]))

    DEST.mkdir(parents=True, exist_ok=True)
    for name in names:
        id_field = {"entries": "entry_id", "forms": "form_id", "senses": "sense_id", "concepts": "concept_id",
                    "relations": "rel_id", "evidence": "evidence_id", "emotions": "annotation_id", "reviews": "review_id"}[name]
        lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in sorted(records[name], key=lambda row: row[id_field])]
        (DEST / f"{name}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    manifest = dict(schema_version=1, data_version="0.0.0-g0", status="draft", generated_at=timestamp,
                    counts={name: len(rows) for name, rows in records.items()}, approved_concepts=0)
    (DEST / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog.write_text("# Danh mục 30 khái niệm mẫu G0\n\n"
                       "Tất cả là bản nháp có AI hỗ trợ, chưa được xác minh độc lập. "
                       "Đọc định nghĩa và ví dụ trong JSONL; không duyệt chỉ dựa vào tên.\n\n"
                       "| Concept ID | Tên khái niệm | Lemma chính | POS | Trạng thái ban đầu |\n"
                       "|---|---|---|---|---|\n" + "\n".join(catalog_rows) + "\n\n"
                       "`đường` và `mạng` có hai sense trên cùng entry; `đá` có hai entry khác POS. "
                       "Các tên rõ nghĩa như `đường ăn` có entry riêng cùng concept để không alias cả mục từ đa nghĩa.\n\n"
                       "`AI`, `ML`, `CS` là abbreviation mẫu. Từ cảm xúc chưa được gán EmotionAnnotation. "
                       "Các cạnh part_of diễn đạt cấu trúc điển hình, có phạm vi trong Evidence; cần người duyệt rà lại.\n",
                       encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
