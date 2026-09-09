# Kaynaklar ve lisanslar

Bu uygulama açık veri kümelerinden üretilmiştir. Çalışma anında hiçbir dış
servise istek yapılmaz; bütün veri ve görseller depoda yereldir.

## Kelime listesi ve tanımlar

| Kaynak | Kullanım | Lisans |
|---|---|---|
| [Maximax67/Words-CEFR-Dataset](https://github.com/Maximax67/Words-CEFR-Dataset) | CEFR seviyesi, sözcük türü, Google Ngram frekansı | MIT |
| [openlanguageprofiles/olp-en-cefrj](https://github.com/openlanguageprofiles/olp-en-cefrj) — Octanove C1/C2 profili | Küratörlü C1/C2 etiketleri | CC BY-SA 4.0 |
| [Princeton WordNet](https://wordnet.princeton.edu/) (NLTK üzerinden) | İngilizce tanımlar, sözcük türü doğrulaması, kök biçim | [WordNet License](https://wordnet.princeton.edu/license-and-commercial-use) |
| [NLTK averaged perceptron tagger](https://github.com/nltk/nltk_data) | Örnek cümlelerin sözcük türü etiketlemesi | Apache-2.0 |

## Türkçe karşılıklar

Türkçe karşılıklar iki yerde kullanılır: 8.500 kelimelik listenin kendisinde ve
cümledeki her kelimeye dokunulduğunda açılan sözlük balıncağında
(`data/lexicon.json`, cümlelerde geçen 14.361 farklı giriş).

| Kaynak | Kullanım | Lisans |
|---|---|---|
| [FreeDict eng-tur](https://github.com/freedict/fd-dictionaries) | Birincil Türkçe karşılıklar | GPL-2.0-or-later |
| [firatkaya1/dictionary](https://github.com/firatkaya1/dictionary) | FreeDict glossu kullanılamadığında yedek; ayrıca sözcük türü etiketi | Depoda lisans dosyası yok — aşağıdaki nota bakınız |
| `tools/lexicon_overrides.json` | Elle yazılmış 556 karşılık: işlev sözcükleri ve sözlüğün ilk anlamının cümledeki kullanıma uymadığı durumlar | Bu proje — CC0 |

> **Not:** `firatkaya1/dictionary` deposunda bir lisans dosyası bulunmuyor ve
> veri Tureng türevi görünüyor. Bu nedenle temiz lisanslı FreeDict birincil
> kaynak olarak kullanılır; söz konusu depo yalnızca FreeDict'in karşılığı
> okunamayacak durumda olduğunda devreye girer. Projeyi ticari olarak
> kullanacaksanız bu kaynağı kendi lisanslı sözlüğünüzle değiştirin:
> `tools/build_wordlist.py` ve `tools/build_lexicon.py` içindeki yedek kaynağı
> değiştirmek yeterlidir.

## Görseller

| Kaynak | Kullanım | Lisans |
|---|---|---|
| [Google Noto Animated Emoji](https://googlefonts.github.io/noto-emoji-animation/) | Kart görsellerindeki animasyonlu emojiler | CC BY 4.0 |

Emoji dosyaları `assets/emoji/` altında 96 piksele küçültülmüş olarak saklanır.
Emoji anahtar kelimeleri [emojilib](https://github.com/muan/emojilib) (MIT) ve
[unicode-emoji-json](https://github.com/muan/unicode-emoji-json) (MIT)
paketlerinden alınmıştır.

## Örnek cümleler

Uygulamadaki İngilizce örnek cümleler bu proje için elle yazılmıştır; herhangi
bir dış korpustan alınmamıştır.
