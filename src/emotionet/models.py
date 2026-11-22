"""Core data models for Emotionet Vietnamese lexical-semantic network."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class EmotionAnnotation:
    """Emotion annotation for a sense or synset."""
    label: str
    taxonomy: str = "vigoemotions"
    confidence: Optional[float] = None
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Sense:
    """Individual sense of an entry."""
    sense_id: str
    entry_id: str
    gloss: str
    emotion_labels: List[str] = field(default_factory=list)
    pos: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class Entry:
    """Lexical entry (lemma) containing one or more senses."""
    entry_id: str
    lemma: str
    pos: Optional[str] = None
    senses: List[Sense] = field(default_factory=list)


@dataclass
class Synset:
    """Synset grouping synonymous senses expressing shared emotional concepts."""
    synset_id: str
    preferred_lemma: str
    definition: str
    lemmas: List[str] = field(default_factory=list)
    member_sense_ids: List[str] = field(default_factory=list)
    emotion_labels: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    construction: str = "singleton"
    membership_status: str = "singleton"
    semantic_status: str = "inherited_from_reviewed_member"
    publication_status: str = "not_cleared"


@dataclass
class Relation:
    """Semantic relation between a synset and an external term or another synset."""
    rel_id: str
    subject_synset_id: str
    predicate: str  # e.g., 'related_to', 'antonym_of'
    object_term: str
    object_emotions: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class MatchSpan:
    """Information about a matched phrase span in a text."""
    start_char: int
    end_char: int
    matched_text: str
    synset_id: str
    lemma: str
    emotion_labels: List[str] = field(default_factory=list)
    is_multiword: bool = False
    in_negation_scope: bool = False
    intensity_modifier: Optional[str] = None


@dataclass
class EmotionetLexicon:
    """In-memory loaded representation of an Emotionet snapshot."""
    entries: Dict[str, Entry] = field(default_factory=dict)
    senses: Dict[str, Sense] = field(default_factory=dict)
    synsets: Dict[str, Synset] = field(default_factory=dict)
    relations: List[Relation] = field(default_factory=list)
    manifest: Dict[str, Any] = field(default_factory=dict)

    # Secondary indexes
    lemma_to_synsets: Dict[str, List[Synset]] = field(default_factory=dict, init=False)
    emotion_to_synsets: Dict[str, List[Synset]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.rebuild_indexes()

    def rebuild_indexes(self) -> None:
        """Build fast lookup indexes for lemmas and emotions."""
        self.lemma_to_synsets = {}
        self.emotion_to_synsets = {}

        for synset in self.synsets.values():
            for lem in synset.lemmas:
                norm_lem = lem.strip().lower()
                if norm_lem not in self.lemma_to_synsets:
                    self.lemma_to_synsets[norm_lem] = []
                self.lemma_to_synsets[norm_lem].append(synset)

            for emo in synset.emotion_labels:
                if emo not in self.emotion_to_synsets:
                    self.emotion_to_synsets[emo] = []
                self.emotion_to_synsets[emo].append(synset)

    @classmethod
    def from_snapshot(cls, snapshot_dir: Path | str) -> EmotionetLexicon:
        """Load an EmotionetLexicon instance from a snapshot directory."""
        snap_path = Path(snapshot_dir)
        if not snap_path.exists():
            raise FileNotFoundError(f"Snapshot directory does not exist: {snap_path}")

        manifest = {}
        manifest_file = snap_path / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        # Load entries
        entries: Dict[str, Entry] = {}
        entries_file = snap_path / "entries.jsonl"
        if entries_file.exists():
            with open(entries_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        entry = Entry(
                            entry_id=data["entry_id"],
                            lemma=data["lemma"],
                            pos=data.get("pos"),
                        )
                        entries[entry.entry_id] = entry

        # Load senses
        senses: Dict[str, Sense] = {}
        senses_file = snap_path / "senses.jsonl"
        if senses_file.exists():
            with open(senses_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        sense = Sense(
                            sense_id=data["sense_id"],
                            entry_id=data["entry_id"],
                            gloss=data.get("gloss", ""),
                            emotion_labels=data.get("emotion_labels", []),
                            pos=data.get("pos"),
                            examples=data.get("examples", []),
                            evidence_ids=data.get("evidence_ids", []),
                        )
                        senses[sense.sense_id] = sense
                        if sense.entry_id in entries:
                            entries[sense.entry_id].senses.append(sense)

        # Load synsets
        synsets: Dict[str, Synset] = {}
        synsets_file = snap_path / "synsets.jsonl"
        if synsets_file.exists():
            with open(synsets_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        synset = Synset(
                            synset_id=data["synset_id"],
                            preferred_lemma=data["preferred_lemma"],
                            definition=data.get("definition", ""),
                            lemmas=data.get("lemmas", []),
                            member_sense_ids=data.get("member_sense_ids", []),
                            emotion_labels=data.get("emotion_labels", []),
                            evidence_ids=data.get("evidence_ids", []),
                            construction=data.get("construction", "singleton"),
                            membership_status=data.get("membership_status", "singleton"),
                            semantic_status=data.get("semantic_status", "inherited_from_reviewed_member"),
                            publication_status=data.get("publication_status", "not_cleared"),
                        )
                        synsets[synset.synset_id] = synset

        # Load relations
        relations: List[Relation] = []
        relations_file = snap_path / "relations.jsonl"
        if relations_file.exists():
            with open(relations_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        rel = Relation(
                            rel_id=data["rel_id"],
                            subject_synset_id=data["subject_synset_id"],
                            predicate=data["predicate"],
                            object_term=data["object_term"],
                            object_emotions=data.get("object_emotions", []),
                            notes=data.get("notes", ""),
                        )
                        relations.append(rel)

        return cls(
            entries=entries,
            senses=senses,
            synsets=synsets,
            relations=relations,
            manifest=manifest,
        )
