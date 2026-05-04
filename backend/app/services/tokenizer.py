import re
import json
from collections import defaultdict
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# Training (offline) — produces merges.json + vocab.json.
# Run with `python -m app.services.tokenizer` from the backend root.
# ─────────────────────────────────────────────────────────────


def load_corpus() -> list[str]:  # pragma: no cover
    # Lazy import: `datasets` is a heavy dependency only needed for training,
    # not for serving requests, so don't pay the import cost at app startup.
    from datasets import load_dataset

    texts = []

    print("Loading SNLI...")
    snli = load_dataset("snli", split="train")
    for row in snli:
        if row["label"] == 0:
            texts.append(row["premise"])
            texts.append(row["hypothesis"])

    print("Loading MultiNLI...")
    mnli = load_dataset("multi_nli", split="train")
    for row in mnli:
        if row["label"] == 0:
            texts.append(row["premise"])
            texts.append(row["hypothesis"])

    print("Loading SciTail...")
    scitail = load_dataset("scitail", "snli_format", split="train")
    for row in scitail:
        if row["gold_label"] == "entails":
            texts.append(row["sentence1"])
            texts.append(row["sentence2"])

    print("Loading QNLI...")
    qnli = load_dataset("glue", "qnli", split="train")
    for row in qnli:
        if row["label"] == 0:
            texts.append(row["question"])
            texts.append(row["sentence"])

    # Normalize
    texts = [re.sub(r"\s+", " ", t.lower().strip()) for t in texts]

    print(f"Total samples: {len(texts):,}")
    return texts

def BPE() -> dict:  # pragma: no cover
    corpus = load_corpus()
    word_count = {}
    for sentence in corpus:
        for word in sentence.split():
            if len(word) <= 1:
                continue
            word = ' '.join(word)
            word += ' </w>'
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1
    return word_count

def count_pairs(words: dict) -> dict:  # pragma: no cover
    pairs = defaultdict(int)
    for word in words:
          original = word
          word = word.split()
          for i in range(len(word) - 1):
              pair = (word[i], word[i+1])
              pairs[pair] += words[original]
    return pairs

def merge_pairs(pairs: tuple, word_count: dict) -> dict:  # pragma: no cover
    old = ' '.join(pairs)
    new = ''.join(pairs)
    new_word_count = defaultdict(int)
    for word, freq in word_count.items():
        new_word = word.replace(old, new)
        new_word_count[new_word] = freq

    return new_word_count

def main():  # pragma: no cover
    merges = []
    word_count = BPE()
    for i in range(0, 30000):
        pairs = count_pairs(word_count)
        best_pair = max(pairs, key=pairs.get)
        word_count = merge_pairs(best_pair, word_count)
        merges.append(best_pair)
        if i % 1000 == 0:
            print(f"Iteration {i}: {best_pair}")




# ─────────────────────────────────────────────────────────────
# Inference (runtime) — used by the backend at request time.
# ─────────────────────────────────────────────────────────────


class BPETokenizer:
    """BPE tokenizer that turns text into integer IDs for the encoder.

    Loaded once at app startup via `from_pretrained` and reused for every
    request — building the lookup tables is non-trivial and shouldn't run
    on the hot path.
    """

    PAD = "<pad>"
    UNK = "<unk>"

    def __init__(
        self,
        merge_ranks: dict[tuple[str, str], int],
        token2id: dict[str, int],
    ) -> None:
        # merge_ranks: (left, right) -> rank. Lower rank = applied earlier.
        # token2id must contain PAD and UNK so encode/decode can rely on them.
        self.merge_ranks = merge_ranks
        self.token2id = token2id
        self.id2token = {i: t for t, i in token2id.items()}
        self.pad_id = token2id[self.PAD]
        self.unk_id = token2id[self.UNK]

    @classmethod
    def from_pretrained(
        cls,
        directory: str | Path,
        vocab_size: int = 10000,
    ) -> "BPETokenizer":
        """Load merges.json + vocab.json from `directory` and build the tables.

        Steps:
        - merges.json (list of [a, b] pairs) -> merge_ranks dict.
        - vocab.json (post-merge word -> freq) -> sum frequencies per BPE
          token, then keep the top (vocab_size - 2) tokens.
        - Reserve id 0 = <pad>, id 1 = <unk>; assign the rest sequentially.
        - Safety net: ensure every symbol used in any merge pair has an id,
          so `_bpe`'s char-level fallback can always be looked up.
        """
        directory = Path(directory)
        merges_raw = json.loads((directory / "merges.json").read_text())

        merge_ranks: dict[tuple[str, str], int] = {
            (a, b): i for i, (a, b) in enumerate(merges_raw)
        }

        # Vocab construction strategy: rank order over raw frequency.
        #
        # vocab.json gives us per-token frequencies in the post-merge corpus,
        # but those numbers are dominated by single chars stuck in unmerged
        # rare words ("tchaikovsky" -> 't','c','h','a','i'...). Sorting by
        # that freq ranks single chars above genuinely useful merge products
        # like "ing</w>", which then get pushed past the vocab_size cap and
        # become UNK at inference time.
        #
        # Merge rank is a better signal: rank 0 is the most frequent adjacent
        # pair at training time, learned first; later ranks are progressively
        # rarer. So we fill the vocab with: PAD, UNK, every single-char + "</w>"
        # safety net (~80 entries), then merge products in rank order until
        # vocab_size is reached.
        safety: set[str] = {"</w>"}
        for (a, b) in merge_ranks:
            if len(a) == 1:
                safety.add(a)
            if len(b) == 1:
                safety.add(b)

        ordered: list[str] = [cls.PAD, cls.UNK]
        seen: set[str] = {cls.PAD, cls.UNK}

        for sym in sorted(safety):
            if sym not in seen and len(ordered) < vocab_size:
                ordered.append(sym)
                seen.add(sym)

        for (a, b) in merges_raw:
            if len(ordered) >= vocab_size:
                break
            merged = a + b
            if merged not in seen:
                ordered.append(merged)
                seen.add(merged)

        token2id = {tok: i for i, tok in enumerate(ordered)}
        assert len(token2id) <= vocab_size
        return cls(merge_ranks, token2id)

    def encode(self, text: str) -> list[int]:
        """Normalize -> split on whitespace -> BPE each word -> map to ids.

        Tokens not in the vocab become `self.unk_id`. Normalization must
        match training (`_normalize`), otherwise the merges won't apply
        the way they did during BPE training.
        """
        text = self._normalize(text)
        ids: list[int] = []
        for word in text.split():
            for tok in self._bpe(word):
                ids.append(self.token2id.get(tok, self.unk_id))
        return ids

    def decode(self, ids: list[int]) -> str:
        """Inverse of encode — lossy (original case and whitespace gone).

        Look each id up in `self.id2token`, drop the </w> end-of-word
        markers (they become spaces), and join. Used for debugging and
        for showing matched snippets in search results.
        """
        out: list[str] = []
        for i in ids:
            if i == self.pad_id:
                continue
            tok = self.id2token.get(i)
            if tok is None or tok == self.UNK:
                continue
            if tok.endswith("</w>"):
                out.append(tok[:-4] + " ")
            else:
                out.append(tok)
        return "".join(out).rstrip()

    def _normalize(self, text: str) -> str:
        # Mirror the preprocessing in `load_corpus`: lowercase and collapse
        # any run of whitespace to a single space. If these diverge, the
        # tokens produced here won't match what the model was trained on.
        return re.sub(r"\s+", " ", text.lower().strip())

    def _bpe(self, word: str) -> list[str]:
        """Apply merges greedily to one word; return its BPE token list.

        Algorithm: start with `list(word) + ["</w>"]`, then repeatedly find
        the adjacent pair whose merge rank is smallest, merge it in place,
        and continue until no remaining adjacent pair is in `merge_ranks`.
        Re-scan after every merge — a merge can create a new mergeable pair.
        """
        if word == "":
            return []
        # Training skipped len-1 words, so "a</w>" was never learned.
        # Return the bare char so it hits the safety-net id rather than UNK.
        if len(word) == 1:
            return [word]

        symbols: list[str] = list(word) + ["</w>"]
        while True:
            best_idx: int | None = None
            best_rank: int | None = None
            for i in range(len(symbols) - 1):
                rank = self.merge_ranks.get((symbols[i], symbols[i + 1]))
                if rank is None:
                    continue
                if best_rank is None or rank < best_rank:
                    best_rank = rank
                    best_idx = i
            if best_idx is None:
                break
            merged = symbols[best_idx] + symbols[best_idx + 1]
            symbols = symbols[:best_idx] + [merged] + symbols[best_idx + 2:]
        return symbols


if __name__ == "__main__":
    main()
