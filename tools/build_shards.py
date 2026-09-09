#!/usr/bin/env python3
"""wordlist.json + tools/sentences/*.json -> data/words/*.json + manifest

Yalnizca ornek cumlesi yazilmis kelimeler yayina girer; boylece cumleler
yazildikca kutuphane buyur ve uygulama her an calisir durumda kalir.
"""
import json
import os
import re
import sys

import shards as sh


# WordNet tanimlari zaman zaman alinti kuyrugu ve bos anlam ayiraci tasir:
#   "unequivocally detestable; ; ; ; - Edmund Burke"
# Kelime listesi dondurulmus oldugu icin temizlik burada, yayina yazarken yapilir.
_ATTRIBUTION = re.compile(r"[;,]?\s*-\s*[A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*\s*$")
_EMPTY_SENSES = re.compile(r"(?:;\s*)+;")


def clean_definition(text):
    out = _EMPTY_SENSES.sub(";", text)
    out = _ATTRIBUTION.sub("", out)
    out = re.sub(r"\s+", " ", out).strip(" ;,-")
    return out or text.strip()


def load_emoji_index():
    path = os.path.join(sh.ROOT, "assets", "emoji", "index.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_lexicon_index():
    """kelime -> cumledeki her token icin data/lexicon.json dizini.

    build_lexicon.py uretir. Yoksa kartlar sozluk balincagi olmadan calisir.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "lexicon_index.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    rows = sh.load_wordlist()
    emoji_index = load_emoji_index()
    lexicon_index = load_lexicon_index()
    sentences = sh.load_all_sentences()
    os.makedirs(sh.DATA_DIR, exist_ok=True)

    for stale in os.listdir(sh.DATA_DIR):
        if stale.endswith(".json"):
            os.remove(os.path.join(sh.DATA_DIR, stale))

    ready = [r for r in rows if r["word"] in sentences]
    manifest_shards = []
    for index, chunk in sh.shards(ready):
        payload = []
        for r in chunk:
            rec = sentences[r["word"]]
            entry = {
                "w": r["word"],
                "p": rec.get("p", r["pos"]),
                "c": r["cefr"],
                "s": rec["s"],
                "t": rec.get("t", r["tr"]),
                "d": clean_definition(rec.get("d", r["defn_en"])),
            }
            code = emoji_index.get(rec.get("e", ""))
            if code:
                entry["e"] = code
            gloss = lexicon_index.get(r["word"])
            if gloss and len(gloss) == len(rec["s"].split()):
                entry["g"] = gloss
            payload.append(entry)
        name = f"{index:03d}.json"
        with open(os.path.join(sh.DATA_DIR, name), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        manifest_shards.append({"file": name, "count": len(payload)})

    manifest = {
        "total": len(ready),
        "shardSize": sh.SHARD_SIZE,
        "shards": manifest_shards,
    }
    with open(sh.MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    size = sum(
        os.path.getsize(os.path.join(sh.DATA_DIR, s["file"]))
        for s in manifest_shards
    )
    print(f"kelime  : {len(ready)}/{len(rows)}")
    print(f"shard   : {len(manifest_shards)}")
    print(f"boyut   : {size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
