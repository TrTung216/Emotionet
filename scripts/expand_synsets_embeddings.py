"""Train a small Vietnamese Word2Vec pilot and retrieve review-only candidates.

Only train text is used. Existing synsets and sense labels remain unchanged.
Static term vectors are guided by reviewed glosses, not learned sense vectors.
"""

import argparse
import csv
import hashlib
import html
import importlib.metadata
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from build_seed_synsets import private_output, read_jsonl, sha256, write_jsonl

ROOT = Path(__file__).resolve().parents[1]


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def stable_hash(value):
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "little")


def fuse_seed_phrases(tokens, seed_patterns):
    result, index = [], 0
    while index < len(tokens):
        for parts, merged in seed_patterns.get(tokens[index], []):
            if tuple(tokens[index:index + len(parts)]) == parts:
                result.append(merged)
                index += len(parts)
                break
        else:
            result.append(tokens[index])
            index += 1
    return result


def eligible_candidate(token, count, existing_tokens, config):
    parts = token.split("_")
    return (count >= config["min_candidate_count"] and token not in existing_tokens
            and token not in config["stop_tokens"] and 1 <= len(parts) <= 4
            and len(token) >= 2 and all(part.isalpha() for part in parts))


def read_train(path, allowed_ids_path=None):
    if path.name != "train.csv":
        raise ValueError("Expansion accepts train.csv only")
    allowed = None
    if allowed_ids_path:
        allowed = set(json.loads(allowed_ids_path.read_text(encoding="utf-8")))
        if not allowed or any(not isinstance(item, str) for item in allowed):
            raise ValueError("Train ID subset must be a nonempty JSON array of strings")
    rows, seen = [], set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"id", "text"} <= set(reader.fieldnames or []):
            raise ValueError("Expected train id and text")
        for row in reader:
            if not row["id"] or row["id"] in seen or row["text"] is None:
                raise ValueError("Missing/duplicate train ID or missing text")
            seen.add(row["id"])
            if allowed is None or row["id"] in allowed:
                # Do not retain or read the labels column for training/ranking.
                rows.append({"id": row["id"], "text": row["text"]})
    if allowed is not None and not allowed <= seen:
        raise ValueError("Subset includes IDs outside train")
    if not rows:
        raise ValueError("No training rows")
    return rows


def expand(synset_dir, train_path, config_path, output, train_ids=None):
    output = private_output(output)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["workers"] != 1 or not 0 <= config["gloss_weight"] <= 1:
        raise ValueError("Use one worker and a gloss weight in [0, 1]")
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise ValueError("Set PYTHONHASHSEED=0 before launching for reproducibility")
    synsets = read_jsonl(synset_dir / "synsets.jsonl")
    senses = {r["sense_id"]: r for r in read_jsonl(synset_dir / "senses.jsonl")}
    source_manifest = json.loads((synset_dir / "manifest.json").read_text(encoding="utf-8"))
    for filename, digest in source_manifest["output_sha256"].items():
        if sha256(synset_dir / filename) != digest:
            raise ValueError(f"Synset snapshot modified: {filename}")
    rows = read_train(train_path, train_ids)
    # Imports are deferred so validation tests need no model dependencies.
    import numpy as np
    from gensim.models import Word2Vec
    from pyvi import ViTokenizer

    def segmented(text):
        text = unicodedata.normalize("NFC", html.unescape(text))
        text = re.sub(r"<[^>]+>|https?://\S+", " ", text)
        return [normalize(token) for token in ViTokenizer.tokenize(text).split()]

    patterns = defaultdict(list)
    lemmas = sorted({r["lemma"] for r in senses.values()})
    for lemma in lemmas:
        parts = tuple(segmented(lemma))
        patterns[parts[0]].append((parts, normalize(lemma).replace(" ", "_")))
    for values in patterns.values():
        values.sort(key=lambda item: (-len(item[0]), item[0]))
    existing = {normalize(lemma).replace(" ", "_") for lemma in lemmas}

    def tokenize(text):
        # Fuse before removing punctuation, so phrases cannot cross punctuation.
        tokens = fuse_seed_phrases(segmented(text), patterns)
        return [token for token in tokens if all(part.isalpha() for part in token.split("_"))]

    sentences, counts, doc_counts, examples = [], Counter(), Counter(), defaultdict(list)
    for n, row in enumerate(rows, 1):
        tokens = tokenize(row["text"])
        sentences.append(tokens)
        counts.update(tokens)
        doc_counts.update(set(tokens))
        for token in sorted(set(tokens)):
            if len(examples[token]) < 2:
                examples[token].append(row)
        if n % 3000 == 0:
            print(f"Tokenized {n}/{len(rows)} train rows", flush=True)
    print(f"Training Skip-gram: {sum(counts.values())} tokens; {config['epochs']} epochs", flush=True)
    model = Word2Vec(vector_size=config["vector_size"], window=config["window"], min_count=config["min_count"],
                     sg=1, hs=0, negative=config["negative"], sample=config["sample"],
                     seed=config["seed"], workers=1, sorted_vocab=1, hashfxn=stable_hash)
    model.build_vocab(sentences)
    model.train(sentences, total_examples=model.corpus_count, epochs=config["epochs"])
    model.wv.fill_norms()
    candidates = [token for token in model.wv.index_to_key if eligible_candidate(token, counts[token], existing, config)]
    if not candidates:
        raise ValueError("No eligible candidate vocabulary")
    matrix = np.vstack([model.wv.get_vector(token, norm=True) for token in candidates])
    unit = lambda v: v / max(float(np.linalg.norm(v)), 1e-12)
    proposals, query_audit = [], []
    for synset in synsets:
        anchor_tokens = [normalize(term).replace(" ", "_") for term in synset["lemmas"]]
        usable = [token for token in anchor_tokens if token in model.wv and counts[token] >= config["min_anchor_count"]]
        if not usable:
            query_audit.append({"synset_id": synset["synset_id"], "lemmas": synset["lemmas"],
                                "status": "skipped_insufficient_observed_anchor", "anchor_counts": {t: counts[t] for t in anchor_tokens}})
            continue
        anchor = unit(np.mean([model.wv.get_vector(t, norm=True) for t in usable], axis=0))
        gloss_tokens = sorted({t for t in tokenize(synset["definition"]) if t in model.wv and t not in config["stop_tokens"] and t not in existing})
        if gloss_tokens:
            gloss = unit(np.mean([model.wv.get_vector(t, norm=True) for t in gloss_tokens], axis=0))
            query = unit((1 - config["gloss_weight"]) * anchor + config["gloss_weight"] * gloss)
        else:
            query = anchor
        # Cosine proximity proposes associations, never proves synonymy or emotion.
        query_scores, anchor_scores = matrix @ query, matrix @ anchor
        ranks = sorted(range(len(candidates)), key=lambda i: (-float(query_scores[i]), candidates[i]))
        count = 0
        for i in ranks:
            if query_scores[i] < config["min_query_cosine"]:
                break
            if anchor_scores[i] < config["min_anchor_cosine"]:
                continue
            token = candidates[i]
            candidate_id = "cand_" + hashlib.sha256((synset["synset_id"] + ":" + token).encode()).hexdigest()[:16]
            proposals.append({"candidate_id": candidate_id, "target_synset_id": synset["synset_id"],
                              "target_lemmas": synset["lemmas"], "target_definition": synset["definition"],
                              "target_emotion_labels": synset["emotion_labels"], "candidate_token": token,
                              "candidate_form": token.replace("_", " "), "cosine_query": float(query_scores[i]),
                              "cosine_anchor": float(anchor_scores[i]), "token_count": counts[token],
                              "document_count": doc_counts[token], "corpus_examples": examples[token],
                              "status": "needs_review", "relation": None, "candidate_emotion_labels": [],
                              "sense_resolved": False, "confidence": None,
                              "retrieval_method": "static_skipgram_anchor_plus_gloss_not_wsd"})
            count += 1
            if count >= config["top_k_per_synset"]:
                break
        query_audit.append({"synset_id": synset["synset_id"], "lemmas": synset["lemmas"],
                            "status": "queried", "usable_anchor_tokens": usable,
                            "anchor_counts": {t: counts[t] for t in anchor_tokens}, "gloss_tokens": gloss_tokens,
                            "candidate_count": count})
    output.mkdir(parents=True, exist_ok=False)
    # Portable inference artifact: no script-local initializer callback to unpickle.
    model.wv.save(str(output / "word-vectors.kv"))
    write_jsonl(output / "candidates.jsonl", proposals)
    write_jsonl(output / "query-audit.jsonl", query_audit)
    write_jsonl(output / "tokenized-train.jsonl", [{"id": row["id"], "tokens": tokens} for row, tokens in zip(rows, sentences)])
    fields = ["candidate_id", "target_synset_id", "target_lemmas", "target_definition", "target_emotions", "candidate_form",
              "cosine_query", "cosine_anchor", "token_count", "document_count", "example_id", "example_text",
              "decision", "relation", "reviewed_emotions", "candidate_gloss", "reviewer", "reviewed_at", "notes"]
    with (output / "candidate-review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for row in proposals:
            writer.writerow({"candidate_id": row["candidate_id"], "target_synset_id": row["target_synset_id"],
                             "target_lemmas": ";".join(row["target_lemmas"]), "target_definition": row["target_definition"],
                             "target_emotions": ";".join(row["target_emotion_labels"]), "candidate_form": row["candidate_form"],
                             "cosine_query": row["cosine_query"], "cosine_anchor": row["cosine_anchor"],
                             "token_count": row["token_count"], "document_count": row["document_count"],
                             "example_id": row["corpus_examples"][0]["id"], "example_text": row["corpus_examples"][0]["text"]})
    manifest = {"schema_version": 1, "config": config, "training_split": "train", "sentence_labels_used": False,
                "embedding_artifact": "word-vectors.kv", "initialization_hash": "sha256_first_8_bytes_little_endian",
                "rows": len(rows), "tokens": sum(counts.values()), "vocabulary_size": len(model.wv),
                "query_synsets": sum(r["status"] == "queried" for r in query_audit),
                "skipped_synsets": sum(r["status"] != "queried" for r in query_audit),
                "candidate_pairs": len(proposals), "unique_candidate_forms": len({r["candidate_form"] for r in proposals}),
                "accepted_new_members": 0, "sense_disambiguation_performed": False,
                "intended_use": "exploratory review; refit on inner-train for nested GA evaluation",
                "dependencies": {name: importlib.metadata.version(name) for name in ["gensim", "numpy", "scipy", "pyvi"]},
                "python_version": sys.version, "pythonhashseed": os.environ["PYTHONHASHSEED"],
                "inputs": {"train": {"path": str(train_path), "sha256": sha256(train_path)},
                           "config_sha256": sha256(config_path), "synset_manifest_sha256": sha256(synset_dir / "manifest.json"),
                           "train_ids_sha256": sha256(train_ids) if train_ids else None},
                "output_sha256": {path.name: sha256(path) for path in output.iterdir()}}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synsets", type=Path, default=ROOT / "data/local/seed-synsets-v1")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/embedding-expansion.json")
    parser.add_argument("--train-ids", type=Path, help="Optional JSON array of inner-train IDs; no IDs outside train accepted")
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/embedding-expansion-v1")
    args = parser.parse_args()
    result = expand(args.synsets, args.train, args.config, args.output, args.train_ids)
    print(json.dumps({k: result[k] for k in ["rows", "tokens", "vocabulary_size", "query_synsets", "skipped_synsets", "candidate_pairs", "unique_candidate_forms"]}), flush=True)
