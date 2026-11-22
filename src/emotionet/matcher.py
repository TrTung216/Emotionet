"""Phrase matcher and lexical context analyzer for Emotionet."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from emotionet.models import EmotionetLexicon, MatchSpan, Synset

# Negation particles in Vietnamese social and standard texts
DEFAULT_NEGATION_MARKERS = {
    "không", "chẳng", "chả", "chưa", "ko", "k", "khum", "đếch", "chớ", "đâu có",
    "không hề", "chả có", "chẳng có", "hổng", "hem", "chớ hề", "không thể",
}

# Intensity modifiers (amplifiers and downtoners)
DEFAULT_INTENSITY_MARKERS = {
    "rất": "high",
    "cực kỳ": "high",
    "cực kì": "high",
    "quá": "high",
    "vô cùng": "high",
    "quá đỗi": "high",
    "siêu": "high",
    "hết sức": "high",
    "thật sự": "high",
    "thực sự": "high",
    "lắm": "high",
    "ghê": "high",
    "kinh khủng": "high",
    "dữ dội": "high",
    "hơi": "low",
    "hơi hơi": "low",
    "một chút": "low",
    "chút xíu": "low",
    "sương sương": "low",
}

# Contrastive conjunctions indicating clause shift
DEFAULT_CONTRASTIVE_MARKERS = {
    "nhưng", "tuy nhiên", "dẫu vậy", "cơ mà", "thế nhưng", "nhưng mà", "mặc dù",
}

# Emoji & Emoticon mappings to ViGoEmotions
DEFAULT_EMOJI_MAPPINGS: Dict[str, str] = {
    # Joy / Amusement
    "😂": "amusement",
    "🤣": "amusement",
    "😆": "amusement",
    ":))": "amusement",
    "=))": "amusement",
    ":D": "amusement",
    "xD": "amusement",
    "😊": "joy",
    "🥰": "love",
    "😍": "love",
    "❤️": "love",
    "💖": "love",
    "<3": "love",
    # Sadness / Remorse
    "😭": "sadness",
    "😢": "sadness",
    "🥺": "sadness",
    ":'(": "sadness",
    "T_T": "sadness",
    "T.T": "sadness",
    # Anger / Annoyance
    "😡": "anger",
    "🤬": "anger",
    "😠": "annoyance",
    ">:(": "anger",
    # Fear / Nervousness
    "😨": "fear",
    "😱": "fear",
    "😰": "nervousness",
    # Surprise / Confusion
    "😮": "surprise",
    "😲": "surprise",
    "🤔": "curiosity",
    "😕": "confusion",
    # Disgust
    "🤢": "disgust",
    "🤮": "disgust",
}


@dataclass
class MatchResult:
    """Detailed matching results for a single text."""
    text: str
    spans: List[MatchSpan] = field(default_factory=list)
    negated_spans: List[MatchSpan] = field(default_factory=list)
    intensified_spans: List[MatchSpan] = field(default_factory=list)
    contrastive_count: int = 0
    repeated_punct_count: int = 0
    elongated_char_count: int = 0
    emoji_matches: List[Tuple[str, str]] = field(default_factory=list)  # (symbol, emotion_label)
    unmapped_emoji_count: int = 0


class PhraseMatcher:
    """Longest-phrase matcher and context analyzer over Vietnamese text."""

    def __init__(
        self,
        lexicon: EmotionetLexicon,
        negation_markers: Optional[Set[str]] = None,
        intensity_markers: Optional[Dict[str, str]] = None,
        contrastive_markers: Optional[Set[str]] = None,
        emoji_mappings: Optional[Dict[str, str]] = None,
        negation_window_words: int = 3,
    ) -> None:
        self.lexicon = lexicon
        self.negation_markers = negation_markers or DEFAULT_NEGATION_MARKERS
        self.intensity_markers = intensity_markers or DEFAULT_INTENSITY_MARKERS
        self.contrastive_markers = contrastive_markers or DEFAULT_CONTRASTIVE_MARKERS
        self.emoji_mappings = emoji_mappings or DEFAULT_EMOJI_MAPPINGS
        self.negation_window_words = negation_window_words

        # Compile phrase targets from synsets
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns from synset lemmas sorted by length descending."""
        # Map normalized phrase to (synset_id, preferred_lemma, emotion_labels)
        self.phrase_to_synsets: Dict[str, List[Synset]] = {}
        for synset in self.lexicon.synsets.values():
            for lem in synset.lemmas:
                norm = unicodedata.normalize("NFC", lem.strip().lower())
                if norm not in self.phrase_to_synsets:
                    self.phrase_to_synsets[norm] = []
                self.phrase_to_synsets[norm].append(synset)

        # Sort phrases by descending word count then character length (greedy longest-match)
        sorted_phrases = sorted(
            self.phrase_to_synsets.keys(),
            key=lambda p: (len(p.split()), len(p)),
            reverse=True,
        )

        # Regex for word-boundary matching in Vietnamese
        # Boundaries: start/end of string or non-word character (excluding combining accents)
        patterns = []
        for p in sorted_phrases:
            escaped = re.escape(p)
            patterns.append(rf"(?<![\wÀ-ỹ]){escaped}(?![\wÀ-ỹ])")

        if patterns:
            self.phrase_regex = re.compile("|".join(patterns), flags=re.IGNORECASE)
        else:
            self.phrase_regex = None

        # Punctuation & discourse regexes
        # Repeated characters (e.g., 'vuiiii', 'đẹppp', 'quaaaa' or 'quáaa' where base vowels or chars repeat >= 2 times)
        self.repeated_punct_regex = re.compile(r"([!?.,])\1{1,}")
        self.elongated_char_regex = re.compile(r"([a-zA-ZÀ-ỹ])\1{1,}")


        # Emoji / emoticon regex
        emoticon_patterns = [re.escape(k) for k in self.emoji_mappings.keys()]
        # Add generic unicode emoji block range
        emoji_unicode_range = r"[\U00010000-\U0010ffff]"
        if emoticon_patterns:
            combined_emoji = "|".join(emoticon_patterns) + "|" + emoji_unicode_range
            self.emoji_regex = re.compile(combined_emoji)
        else:
            self.emoji_regex = re.compile(emoji_unicode_range)

    def match(self, text: str) -> MatchResult:
        """Find phrase matches, context scopes, and discourse features in text."""
        norm_text = unicodedata.normalize("NFC", text)
        lower_text = norm_text.lower()

        spans: List[MatchSpan] = []
        negated_spans: List[MatchSpan] = []
        intensified_spans: List[MatchSpan] = []

        # 1. Match phrases
        if self.phrase_regex:
            # Keep track of matched character ranges to prevent overlapping inner matches
            matched_ranges: List[Tuple[int, int]] = []

            for m in self.phrase_regex.finditer(lower_text):
                start, end = m.span()
                # Check overlap with existing longer matches
                if any(start < r_end and end > r_start for r_start, r_end in matched_ranges):
                    continue

                matched_ranges.append((start, end))
                matched_str = lower_text[start:end]
                matching_synsets = self.phrase_to_synsets.get(matched_str, [])

                # Collect all labels across matching synsets
                all_labels: Set[str] = set()
                primary_synset_id = matching_synsets[0].synset_id if matching_synsets else ""
                primary_lemma = matching_synsets[0].preferred_lemma if matching_synsets else matched_str
                for s in matching_synsets:
                    all_labels.update(s.emotion_labels)

                is_multiword = " " in matched_str

                # Check negation scope (preceding window)
                in_negation = self._check_negation_scope(lower_text, start)

                # Check intensity modifier
                intensity_mod = self._check_intensity(lower_text, start, end)

                span = MatchSpan(
                    start_char=start,
                    end_char=end,
                    matched_text=norm_text[start:end],
                    synset_id=primary_synset_id,
                    lemma=primary_lemma,
                    emotion_labels=sorted(list(all_labels)),
                    is_multiword=is_multiword,
                    in_negation_scope=in_negation,
                    intensity_modifier=intensity_mod,
                )
                spans.append(span)
                if in_negation:
                    negated_spans.append(span)
                if intensity_mod:
                    intensified_spans.append(span)

        # 2. Match discourse markers
        contrastive_count = 0
        for marker in self.contrastive_markers:
            pattern = rf"(?<![\wÀ-ỹ]){re.escape(marker)}(?![\wÀ-ỹ])"
            contrastive_count += len(re.findall(pattern, lower_text))

        repeated_punct_count = len(self.repeated_punct_regex.findall(norm_text))
        elongated_char_count = len(self.elongated_char_regex.findall(norm_text))

        # 3. Match emojis and emoticons
        emoji_matches: List[Tuple[str, str]] = []
        unmapped_emoji_count = 0
        for m in self.emoji_regex.finditer(norm_text):
            symbol = m.group(0)
            if symbol in self.emoji_mappings:
                emoji_matches.append((symbol, self.emoji_mappings[symbol]))
            else:
                unmapped_emoji_count += 1

        return MatchResult(
            text=norm_text,
            spans=spans,
            negated_spans=negated_spans,
            intensified_spans=intensified_spans,
            contrastive_count=contrastive_count,
            repeated_punct_count=repeated_punct_count,
            elongated_char_count=elongated_char_count,
            emoji_matches=emoji_matches,
            unmapped_emoji_count=unmapped_emoji_count,
        )

    def _check_negation_scope(self, text: str, span_start: int) -> bool:
        """Check whether span_start is within the scope of a preceding negation."""
        prefix = text[:span_start]
        # Clause boundaries stop negation scope: . , ; ! ? \n or contrastive markers
        last_boundary = max(
            prefix.rfind("."),
            prefix.rfind(","),
            prefix.rfind(";"),
            prefix.rfind("!"),
            prefix.rfind("?"),
            prefix.rfind("\n"),
        )
        if last_boundary != -1:
            clause_prefix = prefix[last_boundary + 1:]
        else:
            clause_prefix = prefix

        words = clause_prefix.strip().split()
        preceding_words = words[-self.negation_window_words:] if words else []

        # Check multi-word negations first
        preceding_phrase = " ".join(preceding_words)
        for neg in self.negation_markers:
            if " " in neg and neg in preceding_phrase:
                return True
            if neg in preceding_words:
                return True

        return False

    def _check_intensity(self, text: str, span_start: int, span_end: int) -> Optional[str]:
        """Detect preceding or succeeding intensity modifier."""
        prefix = text[:span_start].strip().split()
        suffix = text[span_end:].strip().split()

        # Check 1-2 words before
        if prefix:
            last_word = prefix[-1]
            if last_word in self.intensity_markers:
                return self.intensity_markers[last_word]
            if len(prefix) >= 2:
                last_two = f"{prefix[-2]} {prefix[-1]}"
                if last_two in self.intensity_markers:
                    return self.intensity_markers[last_two]

        # Check 1 word after (e.g. "vui lắm", "buồn ghê")
        if suffix:
            first_word = suffix[0]
            if first_word in self.intensity_markers:
                return self.intensity_markers[first_word]

        return None
