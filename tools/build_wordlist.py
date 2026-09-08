#!/usr/bin/env python3
"""C1+ kelime listesini uretir -> tools/wordlist.json

Zincir:
  1. Words-CEFR-Dataset'ten level >= 5.0 (C1/C2) satirlari
  2. POS / lemma / bicim filtreleri
  3. WordNet kapisi (gercek sozluk kelimesi + Ingilizce tanim)
  4. Genel kelime kapisi (teknik jargon elenir)
  5. Turkce karsilik: once FreeDict (temiz lisans), temizlikten gecemezse
     genis sozluk
  6. Google Ngram frekansina gore siralanip ilk N kelime alinir
"""
import argparse
import collections
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("WL_CACHE", os.path.join(HERE, ".cache"))
OUT = os.path.join(HERE, "wordlist.json")

TEI_NS = {"t": "http://www.tei-c.org/ns/1.0"}

# Penn Treebank -> gorunur POS. Burada olmayan etiketler (NNP/NNPS ozel isim,
# CD sayi, FW yabanci kelime, ...) tamamen elenir.
POSMAP = {
    "NN": "noun", "NNS": "noun",
    "JJ": "adjective", "JJR": "adjective", "JJS": "adjective",
    "VB": "verb", "VBD": "verb", "VBG": "verb", "VBN": "verb",
    "VBP": "verb", "VBZ": "verb",
    "RB": "adverb", "RBR": "adverb", "RBS": "adverb",
}

# Genis sozlugun kategori etiketleri
NUMERIC_WORDS = re.compile(
    r"^(\w*(teenth|teen|tieth|fold)|(twen|thir|for|fif|six|seven|eigh|nine)ty"
    r"|\w*hundredth|\w*thousandth|\w*illionth)$"
)
GENERAL_CATS = {
    "Common Usage", "General", "Idioms", "Colloquial", "Slang",
    "Phrasals", "Literature", "Speaking", "Proverb",
}

TYPE_TO_POS = {"n.": "noun", "v.": "verb", "adj.": "adjective", "adv.": "adverb"}

csv.field_size_limit(10 ** 7)


# --------------------------------------------------------------------------
# Turkce karsilik temizligi
# --------------------------------------------------------------------------

PARENS = re.compile(r"\([^)]*\)")
GLUED = re.compile(r"\)\w")          # "(bakt.)eriler" -> bozuk madde
MULTISENT = re.compile(r"\.\s")


def clean_gloss(raw, headword, strict):
    """Ham Turkce karsiligi temizler; kullanilamazsa None doner."""
    g = raw.strip()
    if strict and GLUED.search(g):
        return None
    g = PARENS.sub(" ", g)
    g = MULTISENT.split(g)[0]                  # ilk cumle/anlam
    g = g.strip(" .,;:!-–—'\"")
    g = re.sub(r"\s+", " ", g)
    if not g:
        return None
    if len(g) > (45 if strict else 60):
        return None
    toks = g.split()
    if len(toks) > (5 if strict else 7):
        return None
    if any(ch.isdigit() for ch in g):
        return None
    if re.search(r"[.,;:/()]", g):
        return None
    if strict and any(ch.isupper() for ch in g):
        return None                            # "Acipenser sturio" gibi latince
    # turev sizintisi: "polymer'ic ...", "bacterial ..."
    pre = headword[:5].lower()
    if len(pre) >= 4 and any(t.lower().startswith(pre) for t in toks):
        return None
    return g


def dedupe(seq, limit):
    out = []
    for x in seq:
        if x and x not in out:
            out.append(x)
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------
# Kaynak yukleyiciler
# --------------------------------------------------------------------------

def load_freedict(path):
    """headword -> [ham turkce karsilik]"""
    out = collections.defaultdict(list)
    for entry in ET.parse(path).getroot().iter(f"{{{TEI_NS['t']}}}entry"):
        orth = entry.find(".//t:form/t:orth", TEI_NS)
        if orth is None or not orth.text:
            continue
        hw = orth.text.strip().lower()
        for q in entry.findall(".//t:cit[@type='trans']/t:quote", TEI_NS):
            if q.text:
                out[hw].append(q.text.strip())
    return out


def load_bigdict(path):
    """headword -> [{tr, type, category}]"""
    out = collections.defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for e in json.load(f):
            out[e["word"].strip().lower()].append(e)
    return out


def load_octanove(path):
    """headword -> 'C1' | 'C2' (kuratorlu CEFR etiketi)"""
    out = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hw = (r.get("headword") or "").strip().lower()
            lvl = (r.get("CEFR") or "").strip().upper()
            if hw and lvl in ("C1", "C2"):
                out.setdefault(hw, lvl)
    return out


def load_cefr_candidates():
    """Ham aday havuzu: word -> (level, pos, freq)"""
    with open(os.path.join(CACHE, "words.csv"), encoding="utf-8") as f:
        words = {r["word_id"]: r["word"] for r in csv.DictReader(f)}
    with open(os.path.join(CACHE, "pos_tags.csv"), encoding="utf-8") as f:
        tags = {r["tag_id"]: r["tag"] for r in csv.DictReader(f)}

    best = {}
    with open(os.path.join(CACHE, "word_pos.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                level = float(r["level"])
            except (TypeError, ValueError):
                continue
            if level < 5.0:
                continue
            pos = POSMAP.get(tags.get(r["pos_tag_id"], ""))
            if pos is None:
                continue
            if r["lemma_word_id"]:              # cekimli bicim, sozluk formu degil
                continue
            w = words.get(r["word_id"], "")
            if not re.fullmatch(r"[a-z]{4,}", w):
                continue
            if NUMERIC_WORDS.match(w):
                continue
            freq = int(r["frequency_count"])
            if w not in best or freq > best[w][2]:
                best[w] = (level, pos, freq)
    return best


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=8500)
    ap.add_argument("--min-general-ratio", type=float, default=0.30)
    args = ap.parse_args()

    os.environ.setdefault("NLTK_DATA", os.path.join(CACHE, "nltk_data"))
    from nltk.corpus import wordnet as wn

    print("kaynaklar yukleniyor...")
    cands = load_cefr_candidates()
    print(f"  CEFR adaylari       : {len(cands)}")
    freedict = load_freedict(os.path.join(CACHE, "eng-tur.tei"))
    print(f"  FreeDict basliklari : {len(freedict)}")
    bigdict = load_bigdict(os.path.join(CACHE, "dictionary.json"))
    print(f"  Genis sozluk        : {len(bigdict)}")
    octanove = load_octanove(os.path.join(CACHE, "octanove-c1c2.csv"))
    print(f"  Octanove C1/C2      : {len(octanove)}")

    WNPOS = {"noun": wn.NOUN, "verb": wn.VERB,
             "adjective": wn.ADJ, "adverb": wn.ADV}
    WN_TO_POS = {wn.NOUN: "noun", wn.VERB: "verb",
                 wn.ADJ: "adjective", "s": "adjective", wn.ADV: "adverb"}

    rows = []
    stats = collections.Counter()
    for word, (level, pos, freq) in cands.items():
        # --- WordNet kapisi ---------------------------------------------
        all_syns = wn.synsets(word)
        if not all_syns:
            stats["wordnet_yok"] += 1
            continue
        wn_pos = {WN_TO_POS[s.pos()] for s in all_syns if s.pos() in WN_TO_POS}
        entries = bigdict.get(word) or []
        # POS secimi: frekans turevi veri seti etiketi taban alinir. WordNet o
        # POS'u hic tanimiyorsa ya da sozlugun genel maddelerindeki cogunluk
        # baska bir POS'u gosteriyorsa duzeltilir (tagger hatalarini toplar).
        if pos not in wn_pos:
            pos = next((p for p in ("noun", "verb", "adjective", "adverb")
                        if p in wn_pos), pos)
        dict_types = collections.Counter(
            TYPE_TO_POS[e["type"]] for e in entries
            if e.get("type") in TYPE_TO_POS and e.get("category") in GENERAL_CATS
        )
        if dict_types:
            top, n = dict_types.most_common(1)[0]
            if top != pos and top in wn_pos and n > dict_types.get(pos, 0) * 2:
                pos = top
        syns = wn.synsets(word, WNPOS[pos]) or all_syns
        if all(s.instance_hypernyms() for s in syns):
            stats["ozel_isim"] += 1          # Aberdeen, Accra, ...
            continue
        definition = syns[0].definition()
        if not definition:
            stats["tanim_yok"] += 1
            continue

        # --- genel kelime kapisi ----------------------------------------
        if not entries:
            stats["kategori_yok"] += 1
            continue
        general = sum(1 for e in entries if e.get("category") in GENERAL_CATS)
        if not general:
            stats["sadece_teknik"] += 1
            continue
        if general / len(entries) < args.min_general_ratio:
            stats["teknik_agirlikli"] += 1
            continue

        # --- Turkce karsilik: once FreeDict ------------------------------
        tr = dedupe(
            (clean_gloss(g, word, strict=True) for g in freedict.get(word, [])), 4
        )
        source = "freedict"
        if not tr:
            # POS'u eslesen ve genel kategorideki maddeler oncelikli
            want = [e for e in entries
                    if TYPE_TO_POS.get(e.get("type")) == pos
                    and e.get("category") in GENERAL_CATS]
            want += [e for e in entries if e.get("category") in GENERAL_CATS]
            want += entries
            tr = dedupe(
                (clean_gloss(e["tr"], word, strict=False) for e in want), 4
            )
            source = "bigdict"
        if not tr:
            stats["turkce_yok"] += 1
            continue

        rows.append({
            "word": word,
            "pos": pos,
            "cefr": octanove.get(word, "C1+"),
            "freq": freq,
            "defn_en": definition,
            "tr": tr,
            "tr_source": source,
        })

    rows.sort(key=lambda r: -r["freq"])
    selected = rows[:args.limit]
    selected.sort(key=lambda r: r["word"])

    print("\nelenenler:")
    for k, v in stats.most_common():
        print(f"  {k:20s} {v}")
    print(f"\nuygun aday havuzu : {len(rows)}")
    print(f"secilen           : {len(selected)}")
    print("  CEFR :", dict(collections.Counter(r["cefr"] for r in selected)))
    print("  POS  :", dict(collections.Counter(r["pos"] for r in selected)))
    print("  TR   :", dict(collections.Counter(r["tr_source"] for r in selected)))

    if len(selected) < args.limit:
        print(f"\nUYARI: hedef {args.limit}, uretilen {len(selected)}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=0)
    print(f"\nyazildi: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
