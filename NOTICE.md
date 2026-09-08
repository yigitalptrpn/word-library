# Kaynaklar ve lisanslar

Bu uygulama açık veri kümelerinden üretilmiştir. Çalışma anında hiçbir dış
servise istek yapılmaz; bütün veri ve görseller depoda yereldir.

## Kelime listesi ve tanımlar

| Kaynak | Kullanım | Lisans |
|---|---|---|
| [Maximax67/Words-CEFR-Dataset](https://github.com/Maximax67/Words-CEFR-Dataset) | CEFR seviyesi, sözcük türü, Google Ngram frekansı | MIT |
| [openlanguageprofiles/olp-en-cefrj](https://github.com/openlanguageprofiles/olp-en-cefrj) — Octanove C1/C2 profili | Küratörlü C1/C2 etiketleri | CC BY-SA 4.0 |
| [Princeton WordNet](https://wordnet.princeton.edu/) (NLTK üzerinden) | İngilizce tanımlar, sözcük türü doğrulaması, kök biçim | [WordNet License](https://wordnet.princeton.edu/license-and-commercial-use) |

## Türkçe karşılıklar

| Kaynak | Kullanım | Lisans |
|---|---|---|
| [FreeDict eng-tur](https://github.com/freedict/fd-dictionaries) | Birincil Türkçe karşılıklar | GPL-2.0-or-later |
| [firatkaya1/dictionary](https://github.com/firatkaya1/dictionary) | FreeDict glossu kullanılamadığında yedek | Depoda lisans dosyası yok — aşağıdaki nota bakınız |

> **Not:** `firatkaya1/dictionary` deposunda bir lisans dosyası bulunmuyor ve
> veri Tureng türevi görünüyor. Bu nedenle temiz lisanslı FreeDict birincil
> kaynak olarak kullanılır; söz konusu depo yalnızca FreeDict'in karşılığı
> okunamayacak durumda olduğunda devreye girer. Projeyi ticari olarak
> kullanacaksanız bu kaynağı kendi lisanslı sözlüğünüzle değiştirin:
> `tools/build_wordlist.py` içindeki yedek kaynağı değiştirmek yeterlidir.

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
