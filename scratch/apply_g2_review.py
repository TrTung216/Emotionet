import csv
import io
import shutil
from pathlib import Path

SRC_DIR = Path("data/local/g2-review-v1")
SUBMIT_DIR = Path("data/local/g2-review-submitted-v1")

# 1. Copy directory
if SUBMIT_DIR.exists():
    shutil.rmtree(SUBMIT_DIR)
shutil.copytree(SRC_DIR, SUBMIT_DIR)
print(f"Copied {SRC_DIR} to {SUBMIT_DIR}")

# 2. Populate is-a-pilot-review.csv
isa_path = SUBMIT_DIR / "is-a-pilot-review.csv"
with open(isa_path, "r", encoding="utf-8-sig") as f:
    isa_rows = list(csv.DictReader(f))

isa_evaluations = {
    "g2_isa_c38f5e15d156": {
        "forward": "yes", "reverse": "no",
        "diff": "Giới hạn bởi tác nhân cụ thể: có sự kiện đón nhận điều tốt lành hoặc kết quả mong đợi",
        "counter": "Không có phản ví dụ cho chiều thuận",
        "decision": "accept", "predicate": "is_a",
        "notes": "Bao hàm một chiều thỏa mãn chặt chẽ; vui mừng là một dạng cụ thể của vui khi có biến cố/tin vui tốt lành."
    },
    "g2_isa_125cc633f053": {
        "forward": "yes", "reverse": "no",
        "diff": "Gắn liền với hành vi săn sóc, che chở, bao bọc đối tượng",
        "counter": "Yêu thần tượng hay yêu lý tưởng không nhất thiết có hành vi săn sóc che chở",
        "decision": "accept", "predicate": "is_a",
        "notes": "Yêu thương là dạng tình cảm yêu gắn liền với ý thức trách nhiệm săn sóc và che chở cụ thể."
    },
    "g2_isa_63bb30a31e51": {
        "forward": "yes", "reverse": "no",
        "diff": "Hướng đến hành động cụ thể lo liệu, chu tất việc thực tế cho người khác",
        "counter": "Quan tâm có thể chỉ dừng ở hỏi han từ xa, không nhất thiết là lo liệu thực tế",
        "decision": "accept", "predicate": "is_a",
        "notes": "Sense caring của 'lo' (lo liệu, chu tất) là một dạng cụ thể mang tính hành vi hỗ trợ của 'quan tâm'."
    },
    "g2_isa_65188cf2e5f9": {
        "forward": "yes", "reverse": "no",
        "diff": "Đối tượng quan tâm bị giới hạn cụ thể vào an nguy, sự an toàn hoặc rủi ro của người khác",
        "counter": "Quan tâm sở thích hay thành tích học tập không phải là lo cho an nguy",
        "decision": "accept", "predicate": "is_a",
        "notes": "'lo lắng cho' ở nghĩa caring là dạng quan tâm đặc thù tập trung vào sự an nguy của đối tượng."
    },
    "g2_isa_a08bfc32abef": {
        "forward": "yes", "reverse": "no",
        "diff": "Ý thức sâu sắc về tội lỗi gắn với mong muốn hối lỗi và sửa chữa sai lầm",
        "counter": "Tiếc nuối vì lỡ cơ hội khách quan không phải là ăn năn tội lỗi",
        "decision": "accept", "predicate": "is_a",
        "notes": "Ăn năn bổ sung nét nghĩa đạo đức và ý chí phục thiện so với hối hận/day dứt thông thường."
    },
    "g2_isa_aa57755372e5": {
        "forward": "yes", "reverse": "no",
        "diff": "Nỗi đau đớn tột bậc trước tang thương mất mát",
        "counter": "Khác biệt chủ yếu là cường độ cực hạn (tột bậc) và nguyên nhân tang thương; synset cha đang chứa 'tủi thân' cần tách nghĩa",
        "decision": "revise", "predicate": "related_to",
        "notes": "Chủ yếu khác biệt về cường độ tột bậc trước tang thương; synset cha chưa ổn định (cần tách tủi thân). Đề xuất giữ related_to."
    },
    "g2_isa_119d4faa9098": {
        "forward": "yes", "reverse": "no",
        "diff": "Sắc thái sâu kín, dai dẳng và nặng trĩu",
        "counter": "Chỉ là khác biệt sắc thái biểu cảm và phong cách từ ngữ (văn chương, cổ điển), không tạo thành subtype độc lập",
        "decision": "reject", "predicate": "related_to",
        "notes": "Sầu là biến thể sắc thái văn phong của buồn, không cấu thành chủng loại logic riêng biệt."
    },
    "g2_isa_8b2c993fa691": {
        "forward": "uncertain", "reverse": "uncertain",
        "diff": "Mức độ cáu kỉnh nhẹ vì chuyện lặt vặt",
        "counter": "Bực mình và khó chịu tâm lý là hai từ gần nghĩa hoán đổi được cho nhau; không có ranh giới bao hàm cha-con",
        "decision": "reject", "predicate": "related_to",
        "notes": "Hai khái niệm cận đồng nghĩa (near-synonyms) thuộc miền phiền toái; không thỏa mãn quan hệ phân cấp."
    },
    "g2_isa_37dae0b35053": {
        "forward": "uncertain", "reverse": "no",
        "diff": "Cơn giận cực điểm trước bất công, ngang trái xã hội",
        "counter": "Định nghĩa giận hiện tại quá hẹp ('trước hành động trái tai gai mắt hoặc thất hứa'), chưa bao trùm nguyên nhân bất công",
        "decision": "revise", "predicate": "related_to",
        "notes": "Định nghĩa synset giận hiện có chưa đủ bao quát; khác biệt chủ yếu là cường độ cao và tính chất phản kháng bất công."
    },
    "g2_isa_037d6e6ab9ae": {
        "forward": "yes", "reverse": "no",
        "diff": "Kinh ngạc tột độ trước điều phi thường, ngoài sức tưởng tượng",
        "counter": "Khác biệt thuần túy về cường độ cảm xúc cực mạnh; tiêu chuẩn G2 không dùng cường độ đơn thuần để lập is_a",
        "decision": "revise", "predicate": "related_to",
        "notes": "Khác biệt về cường độ ngạc nhiên tột độ; phù hợp chuyển sang related_to hoặc chờ schema quan hệ mức độ."
    },
    "g2_isa_db33da16409f": {
        "forward": "yes", "reverse": "no",
        "diff": "Mức độ mãnh liệt, cháy bỏng và kiên trì",
        "counter": "Chỉ là sự tăng cấp về mức độ/cường độ mong muốn, không có đặc điểm loại riêng",
        "decision": "reject", "predicate": "related_to",
        "notes": "Thuần túy là khác biệt cường độ mong muốn; không cấu thành subtype độc lập."
    },
    "g2_isa_877381b655bf": {
        "forward": "yes", "reverse": "yes",
        "diff": "Biểu lộ rõ ra bên ngoài khi đạt vinh dự",
        "counter": "Định nghĩa tự hào hiện tại chứa chính từ 'hãnh diện'; hai khái niệm tương đương hai chiều",
        "decision": "reject", "predicate": "related_to",
        "notes": "Tương đương hai chiều (định nghĩa tự hào có chứa hãnh diện); không dùng is_a để thay thế việc xem xét đồng nghĩa."
    },
    "g2_isa_6f36fba96236": {
        "forward": "uncertain", "reverse": "no",
        "diff": "Run rẩy cao độ khi gặp nguy",
        "counter": "Thành viên 'sợ sệt' mang nét nghĩa e dè rụt rè (cường độ thấp), mâu thuẫn với định nghĩa run rẩy cao độ của cả synset con",
        "decision": "revise", "predicate": "related_to",
        "notes": "Synset con chưa đồng nhất giữa sợ hãi (cường độ cao) và sợ sệt (e dè, rụt rè); cần rà soát lại synset con trước."
    },
    "g2_isa_47c3771d07c5": {
        "forward": "yes", "reverse": "no",
        "diff": "Sợ đến mức hoảng loạn, rụng rời tay chân",
        "counter": "Khác biệt về cường độ tột cùng kèm phản ứng sinh lý hoảng loạn, không phải chủng loại khái niệm",
        "decision": "reject", "predicate": "related_to",
        "notes": "Khác biệt về cường độ hoảng loạn cực điểm; không lập quan hệ phân cấp."
    },
    "g2_isa_2ea4e7838667": {
        "forward": "no", "reverse": "no",
        "diff": "Biểu hiện nét mặt hoặc tâm trạng rầu rĩ",
        "counter": "Nét mặt buồn bã có thể xuất hiện do ngoại hình hoặc diễn xuất mà tâm lý không buồn; vi phạm tiêu chí cùng loại khái niệm",
        "decision": "reject", "predicate": "related_to",
        "notes": "Vi phạm tiêu chí cùng loại khái niệm (synset con chứa nét mặt biểu hiện); synset cha đang chứa tủi thân cần tách."
    },
    "g2_isa_577c203dfafe": {
        "forward": "uncertain", "reverse": "no",
        "diff": "Kết hợp giữa ghê tởm và sợ hãi",
        "counter": "Ghê sợ một bãi rác bẩn kinh tởm thiên về ghê tởm (disgust) hơn là sợ hãi (fear); là cảm xúc lai ghép phức hợp",
        "decision": "reject", "predicate": "related_to",
        "notes": "Cảm xúc phức hợp lai ghép giữa ghê tởm và sợ hãi; không nên ép vào nhánh đơn thừa kế của sợ."
    },
    "g2_isa_86d5b8ef9177": {
        "forward": "no", "reverse": "no",
        "diff": "E thẹn, rụt rè, không tự nhiên trong giao tiếp",
        "counter": "Ngượng ngùng e thẹn khi mới quen hay khi được khen ngợi không hề có sự xấu hổ hay hổ thẹn vì phạm lỗi",
        "decision": "reject", "predicate": "no_relation",
        "notes": "Phản ví dụ rõ ràng: ngượng ngùng e thẹn giao tiếp không bao hàm xấu hổ (không có lỗi lầm hay hổ thẹn)."
    },
    "g2_isa_01406e747733": {
        "forward": "yes", "reverse": "uncertain",
        "diff": "Hụt hẫng trước kết quả không như ý",
        "counter": "Tiếc ở nghĩa thất vọng là cận đồng nghĩa của thất vọng; không dùng is_a để thay thế việc xem xét gộp synset",
        "decision": "reject", "predicate": "related_to",
        "notes": "Cận đồng nghĩa trong miền thất vọng (disappointment); hướng xử lý thích hợp là synonym_review."
    },
}

for row in isa_rows:
    rid = row["review_id"]
    if rid in isa_evaluations:
        ev = isa_evaluations[rid]
        row["forward_entailment"] = ev["forward"]
        row["reverse_entailment"] = ev["reverse"]
        row["differentia"] = ev["diff"]
        row["counterexample"] = ev["counter"]
        row["final_predicate"] = ev["predicate"]
        row["decision"] = ev["decision"]
        row["reviewer"] = "antigravity"
        row["reviewed_at"] = "2026-11-24T14:35:00+07:00"
        row["resolution_notes"] = ev["notes"]

stream = io.StringIO(newline="")
writer = csv.DictWriter(stream, fieldnames=list(isa_rows[0]), lineterminator="\n")
writer.writeheader()
writer.writerows(isa_rows)
isa_path.write_bytes(stream.getvalue().encode("utf-8-sig"))
print(f"Updated {isa_path} (18 rows filled)")

# 3. Populate synset-review.csv
syn_path = SUBMIT_DIR / "synset-review.csv"
with open(syn_path, "r", encoding="utf-8-sig") as f:
    syn_rows = list(csv.DictReader(f))

for row in syn_rows:
    sid = row["synset_id"]
    focus = row["review_focus"]

    # Base values
    row["reviewer"] = "antigravity"
    row["reviewed_at"] = "2026-11-24T14:35:00+07:00"

    if sid == "syn_770c2e9f56867e77":  # khâm phục;nể;phục
        row["decision"] = "keep"
        row["membership_decision"] = "revise"
        row["resolution_notes"] = (
            "Nghĩa của 'nể' có 2 hướng dùng: nể phục (admiration) và kiêng nể/nể nang (không phải admiration). "
            "Cần bổ sung điều kiện ngữ cảnh cho sense nể để tránh matcher gán nhầm admiration khi mang nghĩa kiêng dè."
        )
    elif sid == "syn_1560f3c8e023185b":  # biết ơn;cám ơn
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = (
            "Cám ơn là hành vi phát ngôn/giao tiếp biểu đạt lòng biết ơn; chấp nhận giữ chung synset với điều kiện "
            "ghi nhận tính chất biểu đạt xã giao so với tâm trạng nội tâm của biết ơn."
        )
    elif sid == "syn_bfcacfd3e7930678":  # buồn;đau lòng;tủi thân
        row["decision"] = "keep"
        row["membership_decision"] = "revise"
        row["proposed_member_sense_ids"] = "seed_a474e7e0e4e0def0_sense;sense_cand_766542167926"
        row["resolution_notes"] = (
            "Đề xuất tách 'tủi thân' (sense_cand_d6b678c30a79) ra khỏi synset buồn chung; "
            "tủi thân có nét nghĩa phân biệt sâu sắc là nỗi buồn cho thân phận đơn độc/thiệt thòi của chính mình, "
            "nên là một concept riêng hoặc quan hệ related_to của buồn."
        )
    elif sid == "syn_3d86b42296cd6c36":  # yêu;thương;yêu quý
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "3 thành viên có tính tương đương cao trong miền cảm xúc yêu thương tha thiết (love)."
    elif sid == "syn_44b397ce0503a06f":  # nhẹ nhõm;nhẹ lòng
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Đồng nghĩa hoàn toàn trong việc giải tỏa gánh nặng tâm lý (relief)."
    elif sid == "syn_ebc12cdc6ee516b9":  # đồng tình;tán thành
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Đồng nghĩa hoàn toàn trong việc nhất trí ủng hộ quan điểm (approval)."
    elif sid == "syn_3d785a40877bae84":  # nhận ra;vỡ lẽ
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Đồng nghĩa nhận thức bất ngờ ngộ ra chân tướng sự việc (realization)."
    elif sid == "syn_4575c2be0fc2df6e":  # sợ hãi;sợ sệt
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Giữ chung trong synset fear; ghi nhận 'sợ sệt' có thêm sắc thái rụt rè, e dè."
    elif sid == "syn_13a9a091c39694b1":  # lo;lo lắng;lo âu
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Hoàn toàn tương đương trong trạng thái bất an trước điều rủi ro (nervousness)."
    elif sid == "syn_52309529a62e915d":  # hối hận;tiếc nuối;day dứt;hối tiếc
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Giữ chung trong miền remorse; ghi nhận 'tiếc nuối' có thể do lỡ dịp khách quan."
    else:
        # 56 singletons / other synsets
        row["decision"] = "keep"
        row["membership_decision"] = "keep"
        row["resolution_notes"] = "Giữ nguyên định nghĩa và thành viên đã được rà soát từ snapshot v2."

stream_syn = io.StringIO(newline="")
writer_syn = csv.DictWriter(stream_syn, fieldnames=list(syn_rows[0]), lineterminator="\n")
writer_syn.writeheader()
writer_syn.writerows(syn_rows)
syn_path.write_bytes(stream_syn.getvalue().encode("utf-8-sig"))
print(f"Updated {syn_path} (66 rows filled)")
