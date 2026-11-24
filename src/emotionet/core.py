"""Transactional SQLite API for immutable, losslessly archived snapshots.

Only the Python standard library is required. Semantic review and rights are
never inferred from labels, embedding similarity or the act of importing.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Any

from .normalization import normalize_text


class SnapshotError(ValueError):
    """Invalid, inconsistent or modified input snapshot."""


class PublicationError(ValueError):
    """The snapshot does not meet the declared export policy."""


_SCHEMA_VERSION = 1
_PREDICATES = {"is_a", "part_of", "subfield_of", "related_to", "antonym_of", "same_as"}
_HIERARCHICAL = {"is_a", "part_of", "subfield_of"}
_SCHEMA = """
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE source_files(name TEXT PRIMARY KEY, content BLOB NOT NULL, sha256 TEXT NOT NULL);
CREATE TABLE records(id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE concepts(id TEXT PRIMARY KEY REFERENCES records(id));
CREATE TABLE entries(id TEXT PRIMARY KEY REFERENCES records(id), normalized_form TEXT NOT NULL);
CREATE INDEX entry_normalized ON entries(normalized_form);
CREATE TABLE senses(id TEXT PRIMARY KEY REFERENCES records(id),
 entry_id TEXT NOT NULL REFERENCES entries(id), concept_id TEXT NOT NULL REFERENCES concepts(id));
CREATE INDEX sense_entry ON senses(entry_id);
CREATE INDEX sense_concept ON senses(concept_id);
CREATE TABLE forms(id TEXT PRIMARY KEY REFERENCES records(id),
 entry_id TEXT NOT NULL REFERENCES entries(id), normalized_form TEXT NOT NULL);
CREATE INDEX form_normalized ON forms(normalized_form);
CREATE TABLE evidence(id TEXT PRIMARY KEY REFERENCES records(id));
CREATE TABLE record_evidence(owner_id TEXT NOT NULL REFERENCES records(id),
 evidence_id TEXT NOT NULL REFERENCES evidence(id), PRIMARY KEY(owner_id,evidence_id));
CREATE TABLE relations(id TEXT PRIMARY KEY REFERENCES records(id),
 subject_id TEXT NOT NULL REFERENCES concepts(id), object_id TEXT REFERENCES concepts(id),
 predicate TEXT NOT NULL);
CREATE INDEX relation_subject ON relations(subject_id,predicate);
CREATE INDEX relation_object ON relations(object_id,predicate);
"""


def _string(row: dict, key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError(f"{key} must be a nonempty string: {row!r}")
    return value


def _ids(value: Any, field: str) -> list[str]:
    if (not isinstance(value, list)
            or any(not isinstance(v, str) or not v.strip() for v in value)
            or len(set(value)) != len(value)):
        raise SnapshotError(f"{field} must be a list of distinct nonempty IDs")
    return value


def _json(content: bytes, location: str) -> Any:
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        return json.loads(content.decode("utf-8-sig"), object_pairs_hook=unique,
                          parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    except (ValueError, UnicodeError) as exc:
        raise SnapshotError(f"Invalid JSON in {location}: {exc}") from exc


class Emotionet:
    """One immutable snapshot per database. Use a new DB for a new version.

    ``mode='research'`` exposes candidates and unresolved relation proposals.
    The default ``approved`` mode requires explicit review and evidence.
    Neither mode performs word-sense disambiguation.
    """

    def __init__(self, connection: sqlite3.Connection, mode: str):
        self._db = connection
        self.mode = mode

    @classmethod
    def open(cls, path: str | Path = ":memory:", *, mode: str = "approved") -> Emotionet:
        if mode not in {"approved", "research"}:
            raise ValueError("mode must be 'approved' or 'research'")
        db = sqlite3.connect(str(path))
        try:
            db.execute("PRAGMA foreign_keys = ON")
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not tables:
                # DDL and version marker are committed together.
                db.executescript("BEGIN IMMEDIATE;\n" + _SCHEMA
                                 + f"PRAGMA user_version = {_SCHEMA_VERSION};\nCOMMIT;")
            elif db.execute("PRAGMA user_version").fetchone()[0] != _SCHEMA_VERSION:
                raise SnapshotError("Unsupported database schema; open a new Emotionet database")
            elif not {"metadata", "records", "source_files", "senses", "concepts",
                      "entries", "forms", "evidence", "record_evidence", "relations"} <= tables:
                raise SnapshotError("Not an Emotionet database")
            return cls(db, mode)
        except Exception:
            db.close()
            raise

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Emotionet:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @property
    def manifest(self) -> dict:
        row = self._db.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()
        return json.loads(row[0]) if row else {}

    def stats(self) -> dict[str, int]:
        """Physical snapshot counts, including records hidden by approved mode."""
        return {name: self._db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("entries", "forms", "senses", "concepts", "relations", "evidence")}

    def import_jsonl(self, directory: str | Path) -> dict[str, int]:
        """Validate and atomically import a flat JSONL snapshot with manifest.json.

        Supports the research synset profile and historical G0 concept profile.
        All files (including reviews and merge mappings) are archived verbatim.
        Checksums declared by the manifest are mandatory when present.
        """
        root = Path(directory)
        if not root.is_dir():
            raise SnapshotError(f"Snapshot directory does not exist: {root}")
        files = {}
        for path in sorted(root.iterdir()):
            if path.is_symlink() or not path.is_file():
                raise SnapshotError(f"Snapshot must contain only regular files: {path.name}")
            files[path.name] = path.read_bytes()
        if "manifest.json" not in files:
            raise SnapshotError("manifest.json is required")
        manifest = _json(files["manifest.json"], "manifest.json")
        if not isinstance(manifest, dict):
            raise SnapshotError("manifest.json must contain an object")
        checksums = manifest.get("output_sha256", {})
        if not isinstance(checksums, dict):
            raise SnapshotError("output_sha256 must be an object")
        for name, expected in checksums.items():
            if name not in files or hashlib.sha256(files[name]).hexdigest() != expected:
                raise SnapshotError(f"Snapshot checksum mismatch: {name}")
        concept_file = "synsets.jsonl" if "synsets.jsonl" in files else "concepts.jsonl"
        if "synsets.jsonl" in files and "concepts.jsonl" in files:
            raise SnapshotError("Choose either synsets.jsonl or concepts.jsonl, not both")
        if concept_file == "synsets.jsonl":
            if manifest.get("schema") not in {
                "emotionet_research_seed_synsets_v1",
                "emotionet_research_seed_synsets_v2",
                "emotionet_research_seed_synsets_v3",
            }:
                raise SnapshotError("Unsupported synset schema in manifest")
        elif manifest.get("schema_version") != 1:
            raise SnapshotError("Unsupported concept schema_version in manifest")
        for required in (concept_file, "entries.jsonl", "senses.jsonl", "evidence.jsonl"):
            if required not in files:
                raise SnapshotError(f"Missing required file: {required}")
        kinds = {concept_file: ("concept", "synset_id" if concept_file == "synsets.jsonl" else "concept_id"),
                 "entries.jsonl": ("entry", "entry_id"), "senses.jsonl": ("sense", "sense_id"),
                 "forms.jsonl": ("form", "form_id"), "evidence.jsonl": ("evidence", "evidence_id"),
                 "relations.jsonl": ("relation", "rel_id")}
        rows: dict[str, list[dict]] = {}
        # Parse even auxiliary JSON/JSONL, preserving bytes rather than silently
        # accepting broken provenance files. Auxiliary schemas remain opaque.
        for name, content in files.items():
            if name.endswith(".jsonl"):
                parsed = []
                for number, line in enumerate(content.splitlines(), 1):
                    if not line.strip():
                        continue
                    row = _json(line, f"{name}:{number}")
                    if not isinstance(row, dict):
                        raise SnapshotError(f"{name}:{number}: expected an object")
                    parsed.append(row)
                rows[name] = parsed
            elif name.endswith(".json"):
                _json(content, name)
        try:
            self._db.execute("BEGIN IMMEDIATE")
            if self._db.execute("SELECT 1 FROM source_files LIMIT 1").fetchone():
                raise SnapshotError("Database already contains a snapshot; use a new database")
            for name, (kind, id_key) in kinds.items():
                for row in rows.get(name, []):
                    self._db.execute("INSERT INTO records VALUES (?,?,?)",
                                     (_string(row, id_key), kind, json.dumps(row, ensure_ascii=False)))
            for row in rows[concept_file]:
                _string(row, "definition")
                _string(row, "preferred_lemma" if concept_file == "synsets.jsonl" else "preferred_label")
                self._db.execute("INSERT INTO concepts VALUES (?)", (row[kinds[concept_file][1]],))
            for row in rows["entries.jsonl"]:
                lemma = _string(row, "lemma")
                if row.get("lang") != "vi":
                    raise SnapshotError("Entry lang must be vi")
                if row.get("pos") is not None and not isinstance(row["pos"], str):
                    raise SnapshotError("Entry pos must be a string or null")
                if row.get("normalized_form") != normalize_text(lemma):
                    raise SnapshotError(f"Entry normalized_form mismatch: {row['entry_id']}")
                self._db.execute("INSERT INTO entries VALUES (?,?)", (row["entry_id"], normalize_text(lemma)))
            for row in rows["senses.jsonl"]:
                _string(row, "gloss")
                if "emotion_labels" in row:
                    _ids(row["emotion_labels"], "emotion_labels")
                target = _string(row, "synset_id" if concept_file == "synsets.jsonl" else "concept_id")
                self._db.execute("INSERT INTO senses VALUES (?,?,?)",
                                 (row["sense_id"], _string(row, "entry_id"), target))
            for row in rows.get("forms.jsonl", []):
                surface = _string(row, "surface")
                _string(row, "form_type")
                if row.get("normalized_form") != normalize_text(surface):
                    raise SnapshotError(f"Form normalized_form mismatch: {row['form_id']}")
                self._db.execute("INSERT INTO forms VALUES (?,?,?)",
                                 (row["form_id"], _string(row, "entry_id"), normalize_text(surface)))
            for row in rows["evidence.jsonl"]:
                self._db.execute("INSERT INTO evidence VALUES (?)", (row["evidence_id"],))
            for name, (_, id_key) in kinds.items():
                for row in rows.get(name, []):
                    for eid in _ids(row.get("evidence_ids", []), "evidence_ids"):
                        self._db.execute("INSERT INTO record_evidence VALUES (?,?)", (row[id_key], eid))
            graph = {p: {} for p in _HIERARCHICAL}
            for row in rows.get("relations.jsonl", []):
                subject = row.get("subject_synset_id", row.get("subject_id"))
                target = row.get("object_synset_id", row.get("object_id"))
                predicate = _string(row, "predicate")
                if predicate not in _PREDICATES:
                    raise SnapshotError(f"Unsupported predicate: {predicate}")
                if not isinstance(subject, str) or not subject:
                    raise SnapshotError("Relation requires a subject ID")
                if target is None:
                    _string(row, "object_term")
                elif not isinstance(target, str) or not target or target == subject:
                    raise SnapshotError("Relation requires a distinct object ID")
                self._db.execute("INSERT INTO relations VALUES (?,?,?,?)",
                                 (row["rel_id"], subject, target, predicate))
                if target is not None and predicate in graph:
                    graph[predicate].setdefault(subject, set()).add(target)
            self._validate_memberships(rows, concept_file)
            self._validate_cycles(graph)
            declared_counts = manifest.get("counts", {})
            if not isinstance(declared_counts, dict):
                raise SnapshotError("manifest counts must be an object")
            for name in set(rows) | set(kinds) | {key + ".jsonl" for key in declared_counts}:
                records = rows.get(name, [])
                key = name.removesuffix(".jsonl")
                expected = declared_counts.get(key, manifest.get(key))
                if expected is not None and (type(expected) is not int or expected != len(records)):
                    raise SnapshotError(f"Manifest count mismatch: {key}")
            for name, content in files.items():
                self._db.execute("INSERT INTO source_files VALUES (?,?,?)",
                                 (name, content, hashlib.sha256(content).hexdigest()))
            self._db.execute("INSERT INTO metadata VALUES ('manifest',?)", (json.dumps(manifest),))
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            if isinstance(exc, sqlite3.IntegrityError):
                raise SnapshotError(f"Snapshot integrity violation (duplicate ID or missing reference): {exc}") from exc
            raise
        return self.stats()

    def _validate_memberships(self, rows: dict, concept_file: str) -> None:
        for name, key, table, parent in (("entries.jsonl", "sense_ids", "senses", "entry_id"),
                                         (concept_file, "member_sense_ids", "senses", "concept_id")):
            for row in rows[name]:
                if key not in row:
                    continue
                identifier = row.get("entry_id", row.get("synset_id", row.get("concept_id")))
                declared = set(_ids(row[key], key))
                actual = {r[0] for r in self._db.execute(f"SELECT id FROM {table} WHERE {parent}=?", (identifier,))}
                if declared != actual:
                    raise SnapshotError(f"Inconsistent {key}: {identifier}")

    @staticmethod
    def _validate_cycles(graph: dict) -> None:
        # Iterative topological check also handles graphs deeper than Python's
        # recursion limit. Each hierarchical predicate has its own DAG.
        for predicate, edges in graph.items():
            indegree = {node: 0 for node in edges}
            for targets in edges.values():
                for node in targets:
                    indegree[node] = indegree.get(node, 0) + 1
            pending = [node for node, count in indegree.items() if count == 0]
            seen = 0
            while pending:
                node = pending.pop()
                seen += 1
                for target in edges.get(node, ()):
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        pending.append(target)
            if seen != len(indegree):
                raise SnapshotError(f"Cycle in hierarchical relation: {predicate}")

    def _record(self, identifier: str) -> dict:
        row = self._db.execute("SELECT payload FROM records WHERE id=?", (identifier,)).fetchone()
        return json.loads(row[0])

    def _evidence(self, identifier: str) -> list[dict]:
        return [self._record(r[0]) for r in self._db.execute(
            "SELECT evidence_id FROM record_evidence WHERE owner_id=? ORDER BY evidence_id", (identifier,))]

    @staticmethod
    def _reviewed(row: dict) -> bool:
        return (row.get("semantic_status", row.get("status")) == "approved"
                and isinstance(row.get("reviewer"), str) and bool(row["reviewer"].strip())
                and isinstance(row.get("reviewed_at"), str) and bool(row["reviewed_at"].strip()))

    def _approved(self, identifier: str) -> bool:
        evidence = self._evidence(identifier)
        return self._reviewed(self._record(identifier)) and bool(evidence) and all(map(self._reviewed, evidence))

    def _visible(self, identifier: str) -> bool:
        return self.mode == "research" or self._approved(identifier)

    def lookup(self, text: str) -> list[dict]:
        """Exact normalized lemma/alias lookup, returning every eligible sense.

        No accent stripping, substring matching or automatic sense selection.
        Results contain original records; generated canonical forms are marked.
        """
        key = normalize_text(text)
        hits = self._db.execute("SELECT id FROM entries WHERE normalized_form=? UNION "
                                "SELECT entry_id FROM forms WHERE normalized_form=? ORDER BY 1", (key, key))
        result = []
        for (identifier,) in hits.fetchall():
            if not self._visible(identifier):
                continue
            entry = self._record(identifier)
            forms = [self._record(r[0]) for r in self._db.execute(
                "SELECT id FROM forms WHERE entry_id=? ORDER BY id", (identifier,)) if self._visible(r[0])]
            if normalize_text(entry["lemma"]) != key and not any(f["normalized_form"] == key for f in forms):
                continue  # Do not expose an unapproved alias through an approved entry.
            senses = []
            for sid, cid in self._db.execute("SELECT id,concept_id FROM senses WHERE entry_id=? ORDER BY id", (identifier,)):
                if self._visible(sid) and self._visible(cid):
                    senses.append({"sense": self._record(sid), "concept": self._record(cid),
                                   "evidence": self._evidence(sid), "concept_evidence": self._evidence(cid)})
            if not senses:
                continue
            derived = [] if any(f.get("form_type") == "canonical" for f in forms) else [{
                "form_id": f"derived:canonical:{identifier}", "entry_id": identifier,
                "surface": entry["lemma"], "normalized_form": normalize_text(entry["lemma"]),
                "form_type": "canonical", "derived": True}]
            result.append({"entry": entry, "forms": forms, "derived_forms": derived,
                           "senses": senses, "evidence": self._evidence(identifier)})
        return result

    def get_concept(self, concept_id: str) -> dict | None:
        if not self._db.execute("SELECT 1 FROM concepts WHERE id=?", (concept_id,)).fetchone() or not self._visible(concept_id):
            return None
        senses = [self._record(sid) for sid, eid in self._db.execute(
            "SELECT id,entry_id FROM senses WHERE concept_id=? ORDER BY id", (concept_id,))
            if self._visible(sid) and self._visible(eid)]
        return {"concept": self._record(concept_id), "senses": senses, "evidence": self._evidence(concept_id)}

    def relations(self, concept_id: str, *, predicate: str | None = None, direction: str = "out") -> list[dict]:
        """Read declared edges/proposals; no inferred inverse or transitive edges."""
        clauses = {"out": "subject_id=?", "in": "object_id=?", "both": "(subject_id=? OR object_id=?)"}
        if direction not in clauses:
            raise ValueError("direction must be 'out', 'in' or 'both'")
        if predicate is not None and predicate not in _PREDICATES:
            raise ValueError(f"Unsupported predicate: {predicate}")
        args = [concept_id] * (2 if direction == "both" else 1)
        query = "SELECT id,subject_id,object_id FROM relations WHERE " + clauses[direction]
        if predicate is not None:
            query += " AND predicate=?"
            args.append(predicate)
        result = []
        for rid, subject, target in self._db.execute(query + " ORDER BY id", args):
            approved = target is not None and all(self._approved(v) for v in (rid, subject, target))
            if self.mode != "research" and not approved:
                continue
            row = self._record(rid)
            state = "needs_review" if target is None or not row.get("evidence_ids") else row.get("semantic_status", row.get("status", "needs_review"))
            if state == "approved" and not approved:
                state = "needs_review"
            result.append({"relation": row, "resolved": target is not None, "state": state,
                           "evidence": self._evidence(rid)})
        return result

    def export_jsonl(self, directory: str | Path, *, mode: str | None = None) -> Path:
        """Export the entire snapshot byte-for-byte, refusing existing targets.

        Research export preserves historical statuses/rights. Approved export
        fails closed instead of silently dropping unreviewed records.
        """
        mode = self.mode if mode is None else mode
        if mode not in {"research", "approved"}:
            raise ValueError("mode must be 'approved' or 'research'")
        if not self._db.execute("SELECT 1 FROM source_files LIMIT 1").fetchone():
            raise SnapshotError("No snapshot imported")
        if mode == "approved":
            issues = self.publication_issues()
            if issues:
                raise PublicationError("Export blocked: " + "; ".join(issues))
        target = Path(directory).absolute()
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Refusing to overwrite snapshot: {target}")
        # Prepare on the same filesystem; Windows rename publishes a complete directory.
        # The target parent must exist so an invalid path does not create trees.
        staging = Path(tempfile.mkdtemp(prefix=".emotionet-export-", dir=target.parent))
        try:
            for name, content, checksum in self._db.execute("SELECT name,content,sha256 FROM source_files ORDER BY name"):
                if Path(name).name != name or name in {".", ".."}:
                    raise SnapshotError("Unsafe archived filename")
                if hashlib.sha256(content).hexdigest() != checksum:
                    raise SnapshotError(f"Archived snapshot checksum mismatch: {name}")
                (staging / name).write_bytes(content)
            if target.exists() or target.is_symlink():
                raise FileExistsError(f"Refusing to overwrite snapshot: {target}")
            # Windows rename rejects an existing destination. On POSIX, reserve
            # via mkdir first so even an empty user directory is never replaced.
            if os.name == "nt":
                staging.rename(target)
            else:
                target.mkdir()
                for path in staging.iterdir():
                    path.rename(target / path.name)
            return target
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def publication_issues(self) -> list[str]:
        """Mechanical declared-policy checks, not a legal license determination."""
        issues = []
        if self.manifest.get("publication_status") != "cleared":
            issues.append("manifest publication_status is not cleared")
        incomplete = []
        for identifier, kind in self._db.execute("SELECT id,kind FROM records ORDER BY id"):
            if kind == "evidence":
                approved = self._reviewed(self._record(identifier))
            else:
                approved = self._approved(identifier)
            if not approved:
                incomplete.append(identifier)
        if incomplete:
            issues.append(f"{len(incomplete)} records lack explicit approval/reviewer/date/evidence (e.g. {incomplete[0]})")
        uncleared = [identifier for identifier, in self._db.execute("SELECT id FROM records ORDER BY id")
                     if self._record(identifier).get("publication_status", "cleared") != "cleared"]
        if uncleared:
            issues.append(f"{len(uncleared)} records declare publication restrictions (e.g. {uncleared[0]})")
        unresolved = self._db.execute("SELECT COUNT(*) FROM relations WHERE object_id IS NULL").fetchone()[0]
        if unresolved:
            issues.append(f"{unresolved} unresolved relation targets")
        core_files = {"entries.jsonl", "senses.jsonl", "synsets.jsonl", "concepts.jsonl", "forms.jsonl", "evidence.jsonl", "relations.jsonl"}
        for name, content in self._db.execute("SELECT name,content FROM source_files"):
            if name.endswith(".jsonl") and name not in core_files and content.strip():
                issues.append(f"approval validation is not implemented for auxiliary file {name}")
        return issues
