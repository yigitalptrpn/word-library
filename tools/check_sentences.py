#!/usr/bin/env python3
"""Elle yazilan ornek cumleleri dogrular.

Kontroller:
  - shard'daki her kelime tam olarak bir kez kapsanmis, fazladan anahtar yok
  - hedef kelime cumlede birebir veya duzenli cekimiyle geciyor
  - uzunluk 8-22 kelime, buyuk harfle basliyor, noktalama ile bitiyor
  - depo genelinde yinelenen cumle yok
"""
import argparse
import collections
import json
import os
import re
import sys

import shards as sh

MIN_WORDS, MAX_WORDS = 8, 22


def load_palette():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "emoji_palette.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return {it["emoji"] for it in json.load(f)}


def inflections(word):
    """Cumlede kabul edilen bicimler."""
    w = word
    forms = {w, w + "s", w + "es", w + "ed", w + "ing", w + "d", w + "ly",
             w + "'s", w + "n", w + "r", w + "st"}
    if w.endswith("e"):
        forms |= {w[:-1] + "ed", w[:-1] + "ing", w[:-1] + "es",
                  w[:-1] + "er", w[:-1] + "est", w[:-1] + "y"}
    if w.endswith("y") and len(w) > 2 and w[-2] not in "aeiou":
        forms |= {w[:-1] + "ies", w[:-1] + "ied", w[:-1] + "ier",
                  w[:-1] + "iest", w[:-1] + "ily"}
    if w.endswith("ic"):
        forms |= {w + "ally"}
    if len(w) > 3 and w[-1] not in "aeiouwxy" and w[-2] in "aeiou" and w[-3] not in "aeiou":
        forms |= {w + w[-1] + "ed", w + w[-1] + "ing", w + w[-1] + "er",
                  w + w[-1] + "est"}
    if w.endswith("us"):
        forms |= {w[:-2] + "i"}
    if w.endswith("is"):
        forms |= {w[:-2] + "es"}
    if w.endswith("f"):
        forms |= {w[:-1] + "ves"}
    if w.endswith("fe"):
        forms |= {w[:-2] + "ves"}
    return forms


def check_shard(index, rows, sentences, seen, errors, palette):
    expected = [r["word"] for r in rows]
    if not sentences:
        return 0
    missing = [w for w in expected if w not in sentences]
    extra = [w for w in sentences if w not in set(expected)]
    for w in missing:
        errors.append(f"{index:03d}  eksik kelime: {w}")
    for w in extra:
        errors.append(f"{index:03d}  fazladan anahtar: {w}")

    done = 0
    for row in rows:
        word = row["word"]
        rec = sentences.get(word)
        if rec is None:
            continue
        done += 1
        s = rec["s"]
        toks = re.findall(r"[a-z']+", s.lower())
        if not (inflections(word) & set(toks)):
            errors.append(f"{index:03d}  '{word}' cumlede gecmiyor: {s}")
        n = len(s.split())
        if not (MIN_WORDS <= n <= MAX_WORDS):
            errors.append(f"{index:03d}  '{word}' uzunluk {n} (beklenen {MIN_WORDS}-{MAX_WORDS}): {s}")
        if not s[:1].isupper():
            errors.append(f"{index:03d}  '{word}' buyuk harfle baslamiyor: {s}")
        if s[-1] not in ".!?":
            errors.append(f"{index:03d}  '{word}' noktalama ile bitmiyor: {s}")
        emoji = rec.get("e")
        if emoji is not None:
            if palette is not None and emoji not in palette:
                errors.append(f"{index:03d}  '{word}' emoji palette yok: {emoji}")
        if s in seen:
            errors.append(f"{index:03d}  '{word}' yinelenen cumle (ayrica '{seen[s]}'): {s}")
        else:
            seen[s] = word
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rows = sh.load_wordlist()
    all_shards = sh.shards(rows)
    palette = load_palette()
    errors = []
    seen = {}
    done = 0
    emoji_count = 0
    for index, shard_rows in all_shards:
        recs = sh.load_sentences(index)
        emoji_count += sum(1 for r in recs.values() if r.get("e"))
        done += check_shard(index, shard_rows, recs, seen, errors, palette)

    total = len(rows)
    pct = done / total * 100 if total else 0
    print(f"cumle kapsamasi : {done}/{total}  ({pct:.1f}%)")
    print(f"shard           : {sum(1 for i, _ in all_shards if sh.load_sentences(i))}/{len(all_shards)} baslatildi")
    if done:
        print(f"emoji           : {emoji_count}/{done}  ({emoji_count / done * 100:.0f}%)")
    if errors:
        print(f"\n{len(errors)} HATA:")
        for e in errors[:60]:
            print("  " + e)
        if len(errors) > 60:
            print(f"  ... ve {len(errors) - 60} tane daha")
        return 1
    print("hata yok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
