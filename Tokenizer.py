import re
import json
from collections import defaultdict
from datasets import load_dataset

def load_corpus() -> list[str]:
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


if __name__ == "__main__":
    main()
