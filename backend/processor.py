import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessedContent:
    raw: str
    cleaned: str
    chunks: list["TextChunk"]
    word_count: int
    char_count: int
    summary: Optional[str]


@dataclass
class TextChunk:
    index: int
    content: str
    char_start: int
    char_end: int
    token_estimate: int  # ~4 chars per token


class ContentProcessor:
    """
    Processes raw text through a cleaning and chunking pipeline.

    Design notes:
    - Chunking uses a sentence-aware sliding window so semantic units
      aren't split mid-sentence.
    - Overlap between chunks ensures context isn't lost at boundaries.
    - All chunking is deterministic (no randomness) for reproducibility.
    """

    CHUNK_SIZE_CHARS: int = 1000        # target chunk size
    CHUNK_OVERLAP_CHARS: int = 150      # overlap between consecutive chunks
    MIN_CHUNK_CHARS: int = 100          # don't emit tiny trailing chunks
    MAX_SUMMARY_CHARS: int = 300

    def process(self, raw_content: str, source_type: str = "manual") -> ProcessedContent:
        cleaned = self._clean(raw_content)
        chunks = self._chunk(cleaned)
        summary = self._extract_summary(cleaned)
        word_count = len(cleaned.split())
        char_count = len(cleaned)

        return ProcessedContent(
            raw=raw_content,
            cleaned=cleaned,
            chunks=chunks,
            word_count=word_count,
            char_count=char_count,
            summary=summary,
        )

    # ── Cleaning ──────────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        # Normalize unicode (NFC composition)
        text = unicodedata.normalize("NFC", text)

        # Collapse null bytes and control characters (except \n and \t)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip leading/trailing whitespace per line
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Collapse runs of blank lines (3+ → 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Collapse inline whitespace (multiple spaces/tabs → single space)
        text = re.sub(r"[ \t]+", " ", text)

        # Strip HTML tags if present, decode entities regardless
        if re.search(r"<[a-zA-Z][^>]*>", text):
            text = self._strip_html(text)
        else:
            text = self._decode_entities(text)

        return text.strip()

    def _strip_html(self, text: str) -> str:
        # Replace block-level tags with newlines
        text = re.sub(r"<(?:p|div|br|h[1-6]|li|tr|blockquote)[^>]*>", "\n", text, flags=re.I)
        # Remove remaining tags
        text = re.sub(r"<[^>]+>", "", text)
        return self._decode_entities(text)

    def _decode_entities(self, text: str) -> str:
        entities = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&nbsp;": " "}
        for entity, char in entities.items():
            text = text.replace(entity, char)
        return text

    # ── Chunking ──────────────────────────────────────────────────────────────

    def _chunk(self, text: str) -> list[TextChunk]:
        if not text:
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: list[TextChunk] = []
        current_parts: list[str] = []
        current_start: int = 0
        current_len: int = 0
        chunk_index: int = 0
        cursor: int = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # If adding this sentence would overflow, flush current chunk
            if current_len + sentence_len > self.CHUNK_SIZE_CHARS and current_parts:
                chunk_text = " ".join(current_parts)
                char_start = current_start
                char_end = char_start + len(chunk_text)

                chunks.append(TextChunk(
                    index=chunk_index,
                    content=chunk_text,
                    char_start=char_start,
                    char_end=char_end,
                    token_estimate=len(chunk_text) // 4,
                ))
                chunk_index += 1

                # Keep overlap: walk back sentences that fit within OVERLAP window
                overlap_parts: list[str] = []
                overlap_len = 0
                for part in reversed(current_parts):
                    if overlap_len + len(part) <= self.CHUNK_OVERLAP_CHARS:
                        overlap_parts.insert(0, part)
                        overlap_len += len(part) + 1
                    else:
                        break

                current_parts = overlap_parts
                current_len = overlap_len
                current_start = cursor - overlap_len

            current_parts.append(sentence)
            current_len += sentence_len + 1  # +1 for space
            cursor += sentence_len + 1

        # Flush the last chunk
        if current_parts:
            chunk_text = " ".join(current_parts)
            if len(chunk_text) >= self.MIN_CHUNK_CHARS or not chunks:
                chunks.append(TextChunk(
                    index=chunk_index,
                    content=chunk_text,
                    char_start=current_start,
                    char_end=current_start + len(chunk_text),
                    token_estimate=len(chunk_text) // 4,
                ))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """
        Sentence-aware split. Handles abbreviations and decimal numbers
        by requiring uppercase after period + space.
        """
        pattern = re.compile(
            r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+(?=[A-Z\"])|\n"
        )
        raw = pattern.split(text)
        return [s.strip() for s in raw if s.strip()]

    # ── Summary ───────────────────────────────────────────────────────────────

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract first N chars, ending on a sentence boundary."""
        if not text:
            return None

        if len(text) <= self.MAX_SUMMARY_CHARS:
            return text

        candidate = text[: self.MAX_SUMMARY_CHARS]
        # Try to end on sentence boundary
        for marker in (".", "!", "?"):
            idx = candidate.rfind(marker)
            if idx > self.MAX_SUMMARY_CHARS // 2:
                return candidate[: idx + 1]

        # Fall back to word boundary
        idx = candidate.rfind(" ")
        return (candidate[:idx] + "…") if idx > 0 else (candidate + "…")


content_processor = ContentProcessor()
