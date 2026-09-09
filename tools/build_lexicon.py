#!/usr/bin/env python3
"""Cumlelerdeki her kelime icin baglama uygun Turkce karsilik uretir.

  tools/sentences/*.json + tools/wordlist.json
      -> data/lexicon.json   [[temel_bicim, pos, "turkce"], ...]
      -> tools/lexicon_index.json  {kelime: [dizin, ...]}

Neden POS etiketleme: duz "kelime -> sozlugun ilk karsiligi" eslemesi yanlis
sonuc veriyordu (cancelled -> "cizilmis", graduate -> "diploma vermek").
Cumle NLTK ile etiketlenip karsilik, kelimenin O CUMLEDEKI turune gore
seciliyor: cancelled/VBD -> fiil -> "iptal etmek".

Karsilik kaynagi onceligi:
  1. elle duzeltme  (tools/lexicon_overrides.json)
  2. genis sozluk, tur eslesiyor + genel kategori
  3. genis sozluk, tur eslesiyor (kategori serbest)
  4. FreeDict  (tur bilgisi yok, sirayla ilk temiz karsilik)
  5. genis sozluk, tur eslesmiyor + genel kategori
"""
import argparse
import collections
import json
import os
import re
import sys

import shards as sh

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("WL_CACHE", os.path.join(HERE, ".cache"))
OVERRIDES = os.path.join(HERE, "lexicon_overrides.json")
LEXICON = os.path.join(sh.ROOT, "data", "lexicon.json")
INDEX = os.path.join(HERE, "lexicon_index.json")

# Penn Treebank -> gorunur POS. Buradaki etiketler sozlukteki tur alaniyla
# eslestirilir; listede olmayan etiketler (DT, IN, PRP, CC, ...) icin tur
# serbest birakilir.
PENN = {
    "NN": "noun", "NNS": "noun", "NNP": "noun", "NNPS": "noun",
    "JJ": "adjective", "JJR": "adjective", "JJS": "adjective",
    "VB": "verb", "VBD": "verb", "VBG": "verb", "VBN": "verb",
    "VBP": "verb", "VBZ": "verb",
    "RB": "adverb", "RBR": "adverb", "RBS": "adverb",
}
WN_TAG = {"noun": "n", "verb": "v", "adjective": "a", "adverb": "r"}
TYPE_TO_POS = {"n.": "noun", "v.": "verb", "adj.": "adjective", "adv.": "adverb"}

LEAD = "\"'“‘([{"
TRAIL = "\"'”’)]},.;:!?—–"


def split_token(tok):
    """'office,' -> ('', 'office', ',')  |  '\"Hello!' -> ('\"', 'Hello', '!')"""
    i, j = 0, len(tok)
    while i < j and tok[i] in LEAD:
        i += 1
    while j > i and tok[j - 1] in TRAIL:
        j -= 1
    return tok[:i], tok[i:j], tok[j:]


def tag_sentence(words, pos_tag):
    """words -> {kelime dizini: Penn etiketi}

    Noktalama isaretleri etiketleyiciye ayri token olarak verilir; boylece
    cumle sonu ve tirnaklar dogru degerlendirilir, ama etiket yalnizca gercek
    kelimelere geri baglanir.
    """
    toks, owner = [], []
    for i, w in enumerate(words):
        lead, core, trail = split_token(w)
        for ch in lead:
            toks.append(ch)
            owner.append(-1)
        if core:
            toks.append(core)
            owner.append(i)
        for ch in trail:
            toks.append(ch)
            owner.append(-1)
    out = {}
    if not toks:
        return out
    for (_, tag), o in zip(pos_tag(toks), owner):
        if o >= 0:
            out[o] = tag
    return out


class Glosser:
    def __init__(self, freedict, bigdict, overrides, clean_gloss, general_cats, wn):
        self.fd = freedict
        self.bd = bigdict
        self.ov = overrides
        self.clean = clean_gloss
        self.cats = general_cats
        self.wn = wn
        self.cache = {}
        self.source = collections.Counter()

    def known(self, word):
        return bool(self.bd.get(word) or self.fd.get(word))

    def lemma(self, word, pos, plural=False):
        """Sozluk hali. Once cumledeki ture gore, sonra genel."""
        if word.endswith("'s") and len(word) > 3:
            word = word[:-2]
        tags = [WN_TAG[pos]] if pos in WN_TAG else []
        tags += [t for t in ("n", "v", "a", "r") if t not in tags]
        got = None
        for t in tags:
            got = self.wn.morphy(word, t)
            if got:
                break
        got = got or word
        # WordNet 'years', 'days', 'minutes' gibi coguller icin kendi maddesini
        # tutuyor, bu yuzden morphy tekile inmiyor. Etiket cogulse elle dene.
        if plural and got == word:
            for cand in self._depluralize(word):
                if self.known(cand) or self.wn.synsets(cand):
                    return cand
        return got

    @staticmethod
    def _depluralize(word):
        if word.endswith("ies") and len(word) > 4:
            yield word[:-3] + "y"
        if word.endswith(("ses", "xes", "zes", "ches", "shes")):
            yield word[:-2]
        if word.endswith("ves"):
            yield word[:-3] + "f"
            yield word[:-3] + "fe"
        if word.endswith("s") and not word.endswith("ss"):
            yield word[:-1]

    def _from_bigdict(self, head, pos, cats_only):
        for e in self.bd.get(head, []):
            if cats_only and e.get("category") not in self.cats:
                continue
            if pos and TYPE_TO_POS.get(e.get("type")) != pos:
                continue
            got = self.clean(e["tr"], head, strict=False)
            if got:
                return got
        return None

    def _from_freedict(self, head):
        for raw in self.fd.get(head, []):
            got = self.clean(raw, head, strict=True)
            if got:
                return got
        for raw in self.fd.get(head, []):
            got = self.clean(raw, head, strict=False)
            if got:
                return got
        return None

    def lookup(self, head, pos):
        """(turkce, kaynak) - bulunamazsa (None, None)."""
        key = (head, pos)
        if key in self.cache:
            return self.cache[key]
        got = None
        src = None
        for name, fn in (
            ("elle", lambda: self.ov.get(f"{head}|{pos or ''}") or self.ov.get(head)),
            ("sozluk-tur-genel", lambda: self._from_bigdict(head, pos, True)),
            ("sozluk-tur", lambda: self._from_bigdict(head, pos, False)),
            ("freedict", lambda: self._from_freedict(head)),
            ("sozluk-genel", lambda: self._from_bigdict(head, None, True)),
        ):
            got = fn()
            if got:
                src = name
                break
        self.cache[key] = (got, src)
        return self.cache[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=int, default=0,
                    help="en sik N karsiligi elle denetim icin yazdirir")
    args = ap.parse_args()

    os.environ.setdefault("NLTK_DATA", os.path.join(CACHE, "nltk_data"))
    import nltk
    from nltk.corpus import wordnet as wn
    import build_wordlist as bw

    rows = sh.load_wordlist()
    sentences = sh.load_all_sentences()
    by_word = {r["word"]: r for r in rows}

    print("sozlukler yukleniyor...")
    freedict = bw.load_freedict(os.path.join(CACHE, "eng-tur.tei"))
    bigdict = bw.load_bigdict(os.path.join(CACHE, "dictionary.json"))
    overrides = {}
    if os.path.exists(OVERRIDES):
        with open(OVERRIDES, encoding="utf-8") as f:
            overrides = json.load(f)
    print(f"  FreeDict {len(freedict):,} | genis sozluk {len(bigdict):,} "
          f"| elle duzeltme {len(overrides):,}")

    g = Glosser(freedict, bigdict, overrides, bw.clean_gloss,
                bw.GENERAL_CATS, wn)

    table = []                       # [[temel_bicim, pos, turkce], ...]
    table_id = {}
    index = {}
    freq = collections.Counter()     # (temel, pos) -> kac token
    missing = collections.Counter()
    total = hit = 0

    for row in rows:
        word = row["word"]
        rec = sentences.get(word)
        if not rec:
            continue
        words = rec["s"].split()
        tags = tag_sentence(words, nltk.pos_tag)
        ids = []
        for i, tok in enumerate(words):
            _, core, _ = split_token(tok)
            core_l = core.lower()
            if not core_l or not re.search(r"[a-z]", core_l):
                ids.append(-1)
                continue
            total += 1
            penn = tags.get(i, "")
            pos = PENN.get(penn)
            head = g.lemma(core_l, pos, plural=penn in ("NNS", "NNPS"))
            # 8.500'luk listedeki bir kelime, hangi kartin cumlesinde
            # gecerse gecsin ayni kuratorlu karsiligi gosterir. Elle
            # duzeltme yine her seyin onunde gelir.
            listed = head if head in by_word else (
                core_l if core_l in by_word else None)
            manual = g.ov.get(f"{head}|{pos or ''}") or g.ov.get(head)
            if manual:
                tr, src = manual, "elle"
            elif listed:
                head = listed
                tr = " · ".join(by_word[listed]["tr"][:2])
                pos = pos or by_word[listed]["pos"]
                src = "kelime-listesi"
            else:
                tr, src = g.lookup(head, pos)
                if tr is None and head != core_l:
                    tr, src = g.lookup(core_l, pos)
                    if tr:
                        head = core_l
            if not tr:
                missing[core_l] += 1
                ids.append(-1)
                continue
            hit += 1
            g.source[src] += 1
            key = (head, pos or "", tr)
            if key not in table_id:
                table_id[key] = len(table)
                table.append([head, pos or "", tr])
            ids.append(table_id[key])
            freq[table_id[key]] += 1
        index[word] = ids

    os.makedirs(os.path.dirname(LEXICON), exist_ok=True)
    with open(LEXICON, "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, separators=(",", ":"))
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(LEXICON)
    print(f"\ntoken       : {hit:,}/{total:,}  ({100 * hit / total:.1f}%)")
    print(f"sozluk      : {len(table):,} farkli giris, {size / 1024:.0f} KB")
    print("kaynak      : " + " | ".join(f"{k} {v:,}" for k, v in g.source.most_common()))
    if missing:
        top = ", ".join(w for w, _ in missing.most_common(25))
        print(f"eksik       : {len(missing):,} farkli bicim -> {top}")

    if args.report:
        print(f"\n--- en sik {args.report} karsilik (elle denetim) ---")
        for tid, n in freq.most_common(args.report):
            head, pos, tr = table[tid]
            print(f"{n:>5}  {head}|{pos}\t{tr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
