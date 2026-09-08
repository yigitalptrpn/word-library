"""Kelime listesini sabit shard'lara boler. Tum araclar bunu paylasir."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORDLIST = os.path.join(HERE, "wordlist.json")
SENT_DIR = os.path.join(HERE, "sentences")
DATA_DIR = os.path.join(ROOT, "data", "words")
MANIFEST = os.path.join(ROOT, "data", "manifest.json")

SHARD_SIZE = 250


def load_wordlist():
    with open(WORDLIST, encoding="utf-8") as f:
        return json.load(f)


def shards(rows=None):
    """[(index, [row, ...]), ...] - alfabetik sirali, sabit bolunme."""
    rows = rows if rows is not None else load_wordlist()
    return [
        (i // SHARD_SIZE, rows[i:i + SHARD_SIZE])
        for i in range(0, len(rows), SHARD_SIZE)
    ]


def sentence_path(index):
    return os.path.join(SENT_DIR, f"{index:03d}.json")


def load_sentences(index):
    path = sentence_path(index)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_sentences():
    out = {}
    for index, _ in shards():
        out.update(load_sentences(index))
    return out
