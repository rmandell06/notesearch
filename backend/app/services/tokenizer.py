import re
import json
from collections import defaultdict
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# Training (offline) — produces merges.json + vocab.json.
# Run with `python -m app.services.tokenizer` from the backend root.
# ─────────────────────────────────────────────────────────────


def load_corpus() -> list[str]:
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

def BPE() -> dict:
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

def count_pairs(words: dict) -> dict:
    pairs = defaultdict(int)
    for word in words:
          original = word
          word = word.split()
          for i in range(len(word) - 1):
              pair = (word[i], word[i+1])
              pairs[pair] += words[original]
    return pairs

def merge_pairs(pairs: tuple, word_count: dict) -> dict:
    old = ' '.join(pairs)
    new = ''.join(pairs)
    new_word_count = defaultdict(int)
    for word, freq in word_count.items():
        new_word = word.replace(old, new)
        new_word_count[new_word] = freq

    return new_word_count

def main():
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
        """
        raise NotImplementedError

    def encode(self, text: str) -> list[int]:
        """Normalize -> split on whitespace -> BPE each word -> map to ids.

        Tokens not in the vocab become `self.unk_id`. Normalization must
        match training (`_normalize`), otherwise the merges won't apply
        the way they did during BPE training.
        """
        raise NotImplementedError

    def decode(self, ids: list[int]) -> str:
        """Inverse of encode — lossy (original case and whitespace gone).

        Look each id up in `self.id2token`, drop the </w> end-of-word
        markers (they become spaces), and join. Used for debugging and
        for showing matched snippets in search results.
        """
        raise NotImplementedError

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
        raise NotImplementedError


if __name__ == "__main__":
    main()
