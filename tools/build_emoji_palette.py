#!/usr/bin/env python3
"""Animasyonlu Noto emoji paletini uretir -> tools/emoji_palette.json

Noto Animated Emoji (CC BY 4.0) tum emojileri kapsamaz: bayraklar ve ZWJ
kisi/aile dizileri animasyonsuzdur. Bu betik her emojiyi fonts.gstatic.com
uzerinde yoklar ve yalnizca gercekten animasyonu olanlari kaydeder.
"""
import concurrent.futures as cf
import io
import json
import os
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("WL_CACHE", os.path.join(HERE, ".cache"))
OUT = os.path.join(HERE, "emoji_palette.json")

NPM = {
    "emojilib": "https://registry.npmjs.org/emojilib/-/emojilib-4.0.3.tgz",
    "unicode-emoji-json":
        "https://registry.npmjs.org/unicode-emoji-json/-/unicode-emoji-json-0.9.0.tgz",
}
GIF_URL = "https://fonts.gstatic.com/s/e/notoemoji/latest/{code}/512.gif"


def codepoints(emoji):
    """Noto URL'lerinin kullandigi kod noktasi dizgesi (FE0F atilir)."""
    return "_".join(f"{ord(c):x}" for c in emoji if ord(c) != 0xFE0F)


def npm_json(pkg, url, member):
    """npm paketinden tek bir JSON dosyasi cikarir (onbellekli)."""
    cached = os.path.join(CACHE, f"{pkg}-{os.path.basename(member)}")
    if os.path.exists(cached):
        with open(cached, encoding="utf-8") as f:
            return json.load(f)
    print(f"  indiriliyor: {pkg}")
    with urllib.request.urlopen(url, timeout=120) as r:
        blob = r.read()
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        data = json.load(tar.extractfile(member))
    os.makedirs(CACHE, exist_ok=True)
    with open(cached, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def has_animation(code):
    """404 govdesi de 200 gibi gelebilir; icerik tipi de dogrulanir."""
    req = urllib.request.Request(GIF_URL.format(code=code), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                return False
            ctype = r.headers.get("Content-Type", "")
            head = r.read(6)
            return ctype.startswith("image/gif") and head.startswith(b"GIF8")
    except Exception:
        return False


def main():
    os.makedirs(CACHE, exist_ok=True)
    print("emoji verisi yukleniyor...")
    keywords = npm_json("emojilib", NPM["emojilib"], "package/dist/emoji-en-US.json")
    meta = npm_json("unicode-emoji-json", NPM["unicode-emoji-json"],
                    "package/data-by-emoji.json")
    print(f"  {len(meta)} emoji")

    items = []
    for emoji, info in meta.items():
        code = codepoints(emoji)
        if not code:
            continue
        items.append({
            "emoji": emoji,
            "code": code,
            "name": info.get("name", ""),
            "group": info.get("group", ""),
            "keywords": [k.replace("_", " ") for k in keywords.get(emoji, [])],
        })

    print(f"animasyon yoklaniyor ({len(items)} istek, 12 paralel)...")
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        flags = list(pool.map(lambda it: has_animation(it["code"]), items))

    animated = [it for it, ok in zip(items, flags) if ok]
    animated.sort(key=lambda it: (it["group"], it["name"]))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(animated, f, ensure_ascii=False, indent=1)

    groups = {}
    for it in animated:
        groups[it["group"]] = groups.get(it["group"], 0) + 1
    print(f"\nanimasyonlu: {len(animated)}/{len(items)} "
          f"({len(animated) / len(items) * 100:.0f}%)")
    for g, n in sorted(groups.items(), key=lambda kv: -kv[1]):
        print(f"  {g:34s} {n}")
    print(f"\nyazildi: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
