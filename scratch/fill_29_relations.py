import csv
import io
from pathlib import Path

REL_CSV = Path("data/local/g2-review-reconciled-v1/relation-review.csv")

evaluations_29 = {
    "g2_rel_3c2babb98830": {
        "decision": "revise",
        "resolved_id": "syn_tui_than",
        "proposed_def": "Nỗi buồn tủi cho thân phận đơn độc, thiệt thòi của chính mình",
        "final_pred": "related_to",
        "notes": "Đối lập về cực tính cảm xúc (valence: amusement vs sadness) chứ không phải cặp trái nghĩa từ vựng nhị phân trực tiếp; trỏ nghĩa đích đến synset tủi thân đã tách."
    },
    "g2_rel_a1b35ccd3193": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Tính cách cởi mở, hay cười đùa và dễ mang lại niềm vui cho người khác",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan giữa phẩm chất tính cách (vui tính) và cảm xúc khôi hài (buồn cười)."
    },
    "g2_rel_3e60dcb8d94d": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Hành vi hoặc lời nói bông đùa nhằm gây cười, trêu vui",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan giữa tác nhân gây cười (trò đùa - danh từ) và tính chất cảm xúc (hài hước - tính từ)."
    },
    "g2_rel_da4e354c7e37": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Hoạt động hoặc sở thích đem lại sự thư giãn, hào hứng cho tinh thần",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan giữa hoạt động giải trí (thú vui) và cảm xúc vui tươi (hài hước/thích thú)."
    },
    "g2_rel_3c3a043d1b94": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Thanh thản, không bận tâm lo nghĩ hay vướng bận toan tính",
        "final_pred": "related_to",
        "notes": "Trạng thái tâm lý không vướng bận (vô tư) là nền tảng tạo nên niềm vui (vui)."
    },
    "g2_rel_90ac7fd56adc": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Thái độ hòa nhã, sẵn lòng chia sẻ và đón nhận người khác",
        "final_pred": "related_to",
        "notes": "Thái độ tâm lý tích cực, chan hòa (cởi mở) thường đi kèm và thúc đẩy tâm trạng vui vẻ."
    },
    "g2_rel_984f1f6df244": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Yên ổn, thanh thản, không gặp điều trắc trở hay mối lo sợ",
        "final_pred": "related_to",
        "notes": "Sự yên bình trong tâm hồn (bình an) là một thành tố cốt lõi của cảm giác hạnh phúc."
    },
    "g2_rel_24bb01e7425a": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Cảm giác dễ chịu, chan chứa tình yêu thương và sự sẻ chia",
        "final_pred": "related_to",
        "notes": "Sắc thái cảm xúc ấm cúng, che chở (ấm áp) gắn liền với trải nghiệm hạnh phúc."
    },
    "g2_rel_7e6b6ca2fa47": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Chỉ biết vì lợi ích cá nhân của mình mà không màng đến người khác",
        "final_pred": "antonym_of",
        "notes": "Đối lập về định hướng thái độ: yêu thương (vị tha, chăm lo cho người khác) đối nghịch với ích kỷ (vị kỷ, chỉ vì mình)."
    },
    "g2_rel_b52ad8b5d288": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Cảm giác đau đớn, xót xa sâu sắc trước nỗi đau của người khác",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan thuộc miền caring/sadness: khi yêu thương ai thì dễ đau xót khi thấy họ hoạn nạn."
    },
    "g2_rel_bbc7b6e36c74": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Xót thương, đau lòng một cách thấm thía trước cảnh ngộ éo le",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan thuộc miền caring/sadness: xót xa là biểu hiện tình cảm nảy sinh từ lòng yêu thương."
    },
    "g2_rel_0b7cc1161a8f": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Có dã tâm hiểm ác, tàn nhẫn và sẵn sàng gây đau khổ cho người khác",
        "final_pred": "antonym_of",
        "notes": "Tính chất đối lập sâu sắc: lòng yêu thương đùm bọc trái ngược với tâm địa ác độc, tàn nhẫn."
    },
    "g2_rel_d67b2d7ac3a2": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Gợi cảm giác thương hại, xót xa vì chịu nhiều thiệt thòi, bất hạnh",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan thuộc miền caring: đối tượng tội nghiệp là đối tượng khơi gợi tình cảm yêu thương che chở."
    },
    "g2_rel_d74dde98d8a0": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Cảm giác đau đớn, xót xa sâu sắc trước nỗi đau của người khác",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan giữa động từ tình cảm thương và trạng thái cảm xúc đau xót."
    },
    "g2_rel_9d327117f2c6": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Có dã tâm hiểm ác, tàn nhẫn và sẵn sàng gây đau khổ cho người khác",
        "final_pred": "antonym_of",
        "notes": "Tính chất đối lập giữa lòng thương xót nâng đỡ và tính chất tàn nhẫn ác độc."
    },
    "g2_rel_bc8f37dbc4dd": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Xót thương, đau lòng một cách thấm thía trước cảnh ngộ éo le",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan trực tiếp giữa thương và xót xa."
    },
    "g2_rel_6acd1c9ec41d": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Gợi cảm giác thương hại, xót xa vì chịu nhiều thiệt thòi, bất hạnh",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan giữa hành vi thương xót và tính chất tội nghiệp của đối tượng."
    },
    "g2_rel_74e576f6ebd7": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Có thiện cảm và lòng quý trọng, muốn gần gũi với ai đó",
        "final_pred": "related_to",
        "notes": "Quan hệ liên quan gần nghĩa trong miền cảm xúc yêu quý/thiện cảm (love/caring)."
    },
    "g2_rel_ebb4558baa2d": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Hiểu thấu và cùng chia sẻ cảm xúc, rung động với người khác",
        "final_pred": "related_to",
        "notes": "Sự đồng cảm tinh thần thường song hành và thúc đẩy sự ngưỡng mộ đối với người khác."
    },
    "g2_rel_252d726c52be": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Nhạy cảm, khéo léo và sâu sắc trong nhận thức hoặc ứng xử",
        "final_pred": "related_to",
        "notes": "Phẩm chất tinh tế là đối tượng khơi gợi lòng ngưỡng mộ."
    },
    "g2_rel_c5182ff2223d": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Có tình cảm thương yêu, bao dung và sẵn lòng giúp đỡ đồng loại",
        "final_pred": "related_to",
        "notes": "Đức tính nhân ái là đối tượng cao đẹp khơi dậy niềm khâm phục."
    },
    "g2_rel_aabcd8e17c29": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Dám đối đầu với hiểm nguy, khó khăn mà không hề sợ hãi",
        "final_pred": "related_to",
        "notes": "Phẩm chất dũng cảm là nguyên nhân điển hình làm nảy sinh lòng khâm phục, nể phục."
    },
    "g2_rel_97662ea5a444": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Bất ngờ, đột ngột xảy đến trong khoảnh khắc ngắn ngủi",
        "final_pred": "related_to",
        "notes": "Phó từ bổ ngữ thời gian/khoảnh khắc (chợt) kết hợp chặt chẽ với động từ nhận thức (nhận ra, vỡ lẽ)."
    },
    "g2_rel_57778d4e09d1": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Mơ hồ, mờ mịt và không có điểm tựa xác định",
        "final_pred": "related_to",
        "notes": "Trạng thái nhận thức mơ hồ (mông lung) liên quan trực tiếp đến cảm xúc hoang mang (confusion)."
    },
    "g2_rel_802c1ae09c80": {
        "decision": "revise",
        "resolved_id": "",
        "proposed_def": "Phù hợp với chuẩn mực, sự thật và lẽ phải, không phạm sai lầm",
        "final_pred": "related_to",
        "notes": "Lệch phạm trù từ loại và cảm xúc: hối hận là tâm trạng tự trách, đúng đắn là tính chất nhận thức/đánh giá; đề xuất chuyển thành related_to thay vì antonym_of."
    },
    "g2_rel_d280b57a1b21": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Rơi vào cảnh bị từ chối hoặc tan vỡ trong tình cảm lứa đôi",
        "final_pred": "related_to",
        "notes": "Thất tình là nguyên nhân/hoàn cảnh điển hình gây nên nỗi buồn u sầu, đau lòng (sadness)."
    },
    "g2_rel_b7dfde146644": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Coi thường, đánh giá thấp và không tôn trọng đối tượng",
        "final_pred": "related_to",
        "notes": "Thái độ khinh bỉ/coi thường liên quan chặt chẽ với cảm xúc khinh ghét, ghê tởm (disgust)."
    },
    "g2_rel_a5c88362a580": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Coi thường, đánh giá thấp và không tôn trọng đối tượng",
        "final_pred": "related_to",
        "notes": "Khinh miệt là sắc thái thái độ gắn liền với sự căm ghét (disgust/anger)."
    },
    "g2_rel_bab4d75a6bdf": {
        "decision": "accept",
        "resolved_id": "",
        "proposed_def": "Tỏ thái độ giận hờn, làm mình làm mẩy để biểu lộ sự không bằng lòng nhẹ",
        "final_pred": "related_to",
        "notes": "Hờn dỗi là hành vi biểu cảm mức độ nhẹ trong quan hệ tình cảm của cảm xúc giận (anger)."
    },
}

with open(REL_CSV, "r", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    rid = r["review_id"]
    if rid in evaluations_29:
        ev = evaluations_29[rid]
        r["decision"] = ev["decision"]
        r["resolved_object_synset_id"] = ev["resolved_id"]
        r["proposed_object_definition"] = ev["proposed_def"]
        r["final_predicate"] = ev["final_pred"]
        r["reviewer"] = "antigravity"
        r["reviewed_at"] = "2026-11-24T15:00:00+07:00"
        r["resolution_notes"] = ev["notes"]

stream = io.StringIO(newline="")
writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
writer.writeheader()
writer.writerows(rows)
REL_CSV.write_bytes(stream.getvalue().encode("utf-8-sig"))
print(f"Updated {REL_CSV} with 29 reviewed relations.")

# Also update submitted directory copy
submit_rel = Path("data/local/g2-review-submitted-v1/relation-review.csv")
if submit_rel.exists():
    submit_rel.write_bytes(stream.getvalue().encode("utf-8-sig"))
    print(f"Updated {submit_rel}")
