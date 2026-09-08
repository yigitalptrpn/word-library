#!/usr/bin/env python3
"""Kullanilan emojilerin animasyonlu GIF'lerini indirip kucultur.

Kaynak: Google Noto Animated Emoji (CC BY 4.0), 512px GIF (~600 KB).
Cikti : assets/emoji/<kod>.gif (96px, ~37 KB) + assets/emoji/index.json
"""
import argparse
import collections
import json
import os
import sys
import urllib.request

import shards as sh

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.environ.get("WL_CACHE", os.path.join(HERE, ".cache")), "emoji")
OUT_DIR = os.path.join(sh.ROOT, "assets", "emoji")
PALETTE = os.path.join(HERE, "emoji_palette.json")
GIF_URL = "https://fonts.gstatic.com/s/e/notoemoji/latest/{code}/512.gif"

MAX_PX = 96
FRAME_STEP = 3
MAX_FRAMES = 24
COLORS = 64


def download(code):
    path = os.path.join(CACHE, f"{code}.gif")
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return path
    os.makedirs(CACHE, exist_ok=True)
    with urllib.request.urlopen(GIF_URL.format(code=code), timeout=120) as r:
        blob = r.read()
    if not blob.startswith(b"GIF8"):
        raise ValueError(f"{code}: gecerli GIF degil")
    with open(path, "wb") as f:
        f.write(blob)
    return path


def shrink(src, dest):
    """512px GIF -> kucuk, seffaf, animasyonlu GIF.

    Seffaflik icin palet indeksi 255 ayrilir: kareler 255 renge kuantalanir,
    alfasi dusuk pikseller o indekse boyanir. `convert("P")` bunu yapmaz --
    index 0'i rastgele bir renge atar ve emoji siyah kutu icinde gorunur.
    """
    from PIL import Image, ImageSequence

    TRANSPARENT = 255
    im = Image.open(src)
    # ImageSequence.Iterator ayni nesneyi tekrar verir -> her kare kopyalanmali,
    # yoksa butun kareler ayni cikar.
    frames_in = [f.convert("RGBA").copy() for f in ImageSequence.Iterator(im)]
    base = im.info.get("duration") or 60

    out = []
    for frame in frames_in[::FRAME_STEP][:MAX_FRAMES]:
        frame = frame.copy()
        frame.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
        alpha = frame.getchannel("A")
        quant = frame.convert("RGB").quantize(colors=COLORS, method=Image.MEDIANCUT)
        # yari saydam kenarlari da seffaf say: GIF'te ara alfa yok
        quant.paste(TRANSPARENT, alpha.point(lambda a: 255 if a < 128 else 0))
        quant.info["transparency"] = TRANSPARENT
        out.append(quant)

    out[0].save(dest, save_all=True, append_images=out[1:], loop=0,
                duration=base * FRAME_STEP, disposal=2,
                transparency=TRANSPARENT, optimize=False)
    return len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prune", action="store_true",
                    help="artik kullanilmayan gif'leri sil")
    args = ap.parse_args()

    with open(PALETTE, encoding="utf-8") as f:
        palette = {it["emoji"]: it for it in json.load(f)}

    used = collections.Counter()
    for index, _ in sh.shards():
        for rec in sh.load_sentences(index).values():
            if rec.get("e"):
                used[rec["e"]] += 1

    if not used:
        print("kullanilan emoji yok")
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    index_map, total, errors = {}, 0, []
    for i, emoji in enumerate(sorted(used), 1):
        item = palette.get(emoji)
        if item is None:
            errors.append(f"{emoji}: palette yok")
            continue
        code = item["code"]
        dest = os.path.join(OUT_DIR, f"{code}.gif")
        try:
            if not os.path.exists(dest):
                shrink(download(code), dest)
            index_map[emoji] = code
            total += os.path.getsize(dest)
        except Exception as exc:                       # noqa: BLE001
            errors.append(f"{emoji} ({code}): {exc}")
        if i % 50 == 0:
            print(f"  {i}/{len(used)}")

    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index_map, f, ensure_ascii=False, indent=1, sort_keys=True)

    if args.prune:
        keep = {f"{c}.gif" for c in index_map.values()} | {"index.json"}
        for name in os.listdir(OUT_DIR):
            if name not in keep:
                os.remove(os.path.join(OUT_DIR, name))
                print(f"  silindi: {name}")

    print(f"\nemoji      : {len(index_map)} farkli")
    print(f"toplam     : {total / 1024 / 1024:.1f} MB")
    if index_map:
        print(f"ortalama   : {total / len(index_map) / 1024:.0f} KB")
    if errors:
        print(f"\n{len(errors)} HATA:")
        for e in errors[:20]:
            print("  " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
