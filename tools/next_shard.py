#!/usr/bin/env python3
"""Cumlesi yazilacak siradaki shard'in kelimelerini listeler.

Kullanim:  python3 tools/next_shard.py [index]
Cikti:     word<TAB>pos<TAB>ingilizce tanim
"""
import sys

import shards as sh


def main():
    all_shards = sh.shards()
    if len(sys.argv) > 1:
        index = int(sys.argv[1])
    else:
        index = next(
            (i for i, _ in all_shards if not sh.load_sentences(i)), None
        )
        if index is None:
            print("tum shard'lar tamam", file=sys.stderr)
            return 1
    rows = dict(all_shards)[index]
    done = sh.load_sentences(index)
    print(f"# shard {index:03d}  ({len(rows)} kelime, {len(done)} yazilmis)",
          file=sys.stderr)
    for r in rows:
        if r["word"] in done:
            continue
        print(f"{r['word']}\t{r['pos']}\t{r['defn_en']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
