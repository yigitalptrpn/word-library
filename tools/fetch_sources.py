#!/usr/bin/env python3
"""Kaynak veri setlerini indirir (tek seferlik).

Tum kaynaklar raw.githubusercontent.com uzerinden gelir; calisma aninda
uygulama hicbir dis istek yapmaz. NLTK'nin kendi indiricisi proxy arkasinda
calismadigi icin korpus zip'leri dogrudan urllib ile cekilir.
"""
import io
import os
import sys
import urllib.request
import zipfile

CACHE = os.environ.get("WL_CACHE", os.path.join(os.path.dirname(__file__), ".cache"))

FILES = {
    "words.csv": "https://raw.githubusercontent.com/Maximax67/Words-CEFR-Dataset/main/csv/words.csv",
    "word_pos.csv": "https://raw.githubusercontent.com/Maximax67/Words-CEFR-Dataset/main/csv/word_pos.csv",
    "pos_tags.csv": "https://raw.githubusercontent.com/Maximax67/Words-CEFR-Dataset/main/csv/pos_tags.csv",
    "octanove-c1c2.csv": "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/octanove-vocabulary-profile-c1c2-1.0.csv",
    "eng-tur.tei": "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/eng-tur/eng-tur.tei",
    "dictionary-json.zip": "https://raw.githubusercontent.com/firatkaya1/dictionary/main/dictionary-json.zip",
}

NLTK_ZIPS = {
    "corpora/wordnet": "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip",
}


def get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"  cached  {os.path.basename(dest)}")
        return
    print(f"  fetch   {os.path.basename(dest)} <- {url}")
    with urllib.request.urlopen(url, timeout=180) as r, open(dest, "wb") as f:
        f.write(r.read())


def main():
    os.makedirs(CACHE, exist_ok=True)
    print(f"cache: {CACHE}")
    for name, url in FILES.items():
        get(url, os.path.join(CACHE, name))

    # dictionary.json zip icinden cikarilir
    dj = os.path.join(CACHE, "dictionary.json")
    if not os.path.exists(dj):
        print("  unzip   dictionary.json")
        with zipfile.ZipFile(os.path.join(CACHE, "dictionary-json.zip")) as z:
            z.extract("dictionary.json", CACHE)

    nltk_dir = os.path.join(CACHE, "nltk_data")
    for rel, url in NLTK_ZIPS.items():
        target = os.path.join(nltk_dir, rel)
        if os.path.isdir(target):
            print(f"  cached  {rel}")
            continue
        print(f"  fetch   {rel}")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with urllib.request.urlopen(url, timeout=300) as r:
            data = r.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(os.path.dirname(target))
    print("ok")


if __name__ == "__main__":
    sys.exit(main())
