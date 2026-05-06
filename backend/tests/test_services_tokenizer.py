from pathlib import Path

import pytest

from app.services.tokenizer import BPETokenizer


ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
VOCAB_SIZE = 10_000


@pytest.fixture(scope="module")
def tok() -> BPETokenizer:
    return BPETokenizer.from_pretrained(ARTIFACTS, vocab_size=VOCAB_SIZE)


def test_tables_built(tok: BPETokenizer) -> None:
    assert tok.pad_id == 0
    assert tok.unk_id == 1
    assert tok.token2id[BPETokenizer.PAD] == 0
    assert tok.token2id[BPETokenizer.UNK] == 1
    assert len(tok.token2id) == len(tok.id2token)
    assert len(tok.token2id) <= VOCAB_SIZE
    for token, idx in tok.token2id.items():
        assert tok.id2token[idx] == token


def test_merge_ranks_loaded(tok: BPETokenizer) -> None:
    assert tok.merge_ranks[("e", "</w>")] == 0
    assert tok.merge_ranks[("t", "h")] == 1
    assert len(tok.merge_ranks) == 30_000


def test_encode_basic(tok: BPETokenizer) -> None:
    ids = tok.encode("hello world")
    assert isinstance(ids, list)
    assert len(ids) > 0
    assert all(isinstance(i, int) and 0 <= i < len(tok.token2id) for i in ids)


def test_encode_empty(tok: BPETokenizer) -> None:
    assert tok.encode("") == []
    assert tok.encode("   ") == []


def test_unk_rate_low_on_common_english(tok: BPETokenizer) -> None:
    text = "the quick brown fox jumps over the lazy dog the cat sat on the mat"
    ids = tok.encode(text)
    assert ids
    unk_rate = sum(1 for i in ids if i == tok.unk_id) / len(ids)
    assert unk_rate < 0.05


def test_high_freq_word_round_trips(tok: BPETokenizer) -> None:
    ids = tok.encode("the")
    assert tok.unk_id not in ids
    assert tok.decode(ids).strip() == "the"


def test_round_trip_approximate(tok: BPETokenizer) -> None:
    decoded = tok.decode(tok.encode("Hello, World!  This is a TEST."))
    for word in ("hello", "world", "this", "is", "test"):
        assert word in decoded


def test_normalize_is_applied(tok: BPETokenizer) -> None:
    assert tok.encode("HELLO") == tok.encode("hello")
    assert tok.encode("  hello  ") == tok.encode("hello")


def test_bpe_handles_short_words(tok: BPETokenizer) -> None:
    ids = tok.encode("a i o")
    assert isinstance(ids, list)
    assert len(ids) == 3
