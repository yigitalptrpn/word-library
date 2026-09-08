#!/usr/bin/env python3
"""wordlist.json + tools/sentences/*.json -> data/words/*.json + manifest

Yalnizca ornek cumlesi yazilmis kelimeler yayina girer; boylece cumleler
yazildikca kutuphane buyur ve uygulama her an calisir durumda kalir.
"""
import json
import os
import sys

import shards as sh


def main():
    rows = sh.load_wordlist()
    sentences = sh.load_all_sentences()
    os.makedirs(sh.DATA_DIR, exist_ok=True)

    for stale in os.listdir(sh.DATA_DIR):
        if stale.endswith(".json"):
            os.remove(os.path.join(sh.DATA_DIR, stale))

    ready = [r for r in rows if r["word"] in sentences]
    manifest_shards = []
    for index, chunk in sh.shards(ready):
        payload = [
            {
                "w": r["word"],
                "p": r["pos"],
                "c": r["cefr"],
                "s": sentences[r["word"]],
                "t": r["tr"],
                "d": r["defn_en"],
            }
            for r in chunk
        ]
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
