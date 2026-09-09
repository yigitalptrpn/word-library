# Kelime Kütüphanesi — C1

C1 seviyesinde İngilizce kelime kartları. Uygulama açılınca rastgele bir kart
gelir: kelimenin anlamını taşıyan animasyonlu bir görsel, kelimeyi içeren bir
İngilizce örnek cümle ve istendiğinde açılan Türkçe karşılık. "Biliyorum"
işaretlenen kelimeler bir daha karşınıza çıkmaz.

**Hiçbir API kullanılmaz.** Sayfa açıldıktan sonra tarayıcı yalnızca bu deponun
kendi dosyalarını okur; tek bir dış istek bile yapılmaz. Veri de görseller de
depoda yereldir.

## Özellikler

- Rastgele kelime kartı, her açılışta farklı
- Kelimeye özgü animasyonlu emoji + kelimeden türetilen soyut desen
- Kelimenin cümle içinde vurgulanması
- **Cümledeki herhangi bir kelimeye dokunup anlamını görme** — temel biçim, tür
  ve Türkçe karşılık; anlam kelimenin o cümledeki sözcük türüne göre seçilir
- Türkçe anlam ve İngilizce tanım, ancak istendiğinde açılır
- Bilinen kelimeler `localStorage`'da saklanır ve bir daha gösterilmez
- İlerlemeyi JSON olarak dışa/içe aktarma
- Açık/koyu tema, mobil düzen, kaydırma jestleri, klavye kısayolları
- `prefers-reduced-motion` desteği

### Klavye

| Tuş | İşlev |
|---|---|
| `boşluk` | anlamı göster |
| `→` / `enter` | sonraki kelime |
| `K` | biliyorum, bir daha gösterme |
| `Z` | son işareti geri al |
| `sekme` | cümledeki kelimeler arasında gez |

Odak cümledeki bir kelimedeyken `boşluk` o kelimenin anlamını açar; hedef
kelimede ise "Anlamı göster"i tetikler. `esc` balıncağı kapatır.

Dokunmatik ekranda kartı sola kaydırın (sonraki), sağa kaydırın (biliyorum).

## Yerelde çalıştırma

Dosyayı doğrudan açmak yerine küçük bir sunucu gerekir (`fetch` `file://`
üzerinden çalışmaz):

```bash
python3 -m http.server 8000
# http://localhost:8000
```

## GitHub Pages'te yayınlama

`.github/workflows/pages.yml` bu dala her push'ta siteyi yayınlar. Bir kereye
mahsus olmak üzere Pages'i açmanız gerekir:

1. Depoda **Settings → Pages**
2. **Build and deployment → Source** kısmında **GitHub Actions** seçin

Bundan sonra her push otomatik yayınlanır.

## Veriyi yeniden üretme

Veri dosyaları depoda hazır durumdadır; aşağıdakiler yalnızca sıfırdan üretmek
içindir. Ham kaynaklar `tools/.cache/` altına iner ve depoya girmez.

```bash
pip install nltk Pillow

python3 tools/fetch_sources.py         # ham veri kumelerini indir
python3 tools/build_wordlist.py        # 8.500 kelimelik listeyi uret
python3 tools/build_emoji_palette.py   # animasyonlu emoji paletini cikar
python3 tools/build_emoji_assets.py    # kullanilan emojileri indir + kucult
python3 tools/build_lexicon.py         # cumle sozlugunu uret (POS'a duyarli)
python3 tools/check_sentences.py       # cumleleri ve sozluk hizasini dogrula
python3 tools/build_shards.py          # data/ altindaki yayin dosyalarini uret
```

Uçtan uca tarayıcı testi (sunucu 8765 portunda çalışırken):

```bash
pip install playwright && python3 tools/e2e_test.py
```

## Yapı

```
index.html              kart arayuzu
assets/app.js           kart mantigi, bilinen kelime yonetimi
assets/visual.js        kelimeden turetilen desen + emoji katmani
assets/styles.css       tema ve duzen
assets/emoji/           kucultulmus animasyonlu emoji GIF'leri
data/manifest.json      shard listesi
data/words/NNN.json     250'serlik kelime shard'lari ('g' = token basina sozluk dizini)
data/lexicon.json       cumle sozlugu [[temel bicim, tur, turkce], ...]
tools/                  veri uretim ve dogrulama betikleri
tools/sentences/        elle yazilan ornek cumleler (kaynak)
tools/lexicon_overrides.json  elle yazilan Turkce karsiliklar
```

## Kaynaklar ve lisanslar

Kelime listesi, tanımlar, Türkçe karşılıklar ve emojiler açık veri
kümelerinden gelir. Ayrıntılar ve lisanslar için [NOTICE.md](NOTICE.md).

Örnek cümleler bu proje için elle yazılmıştır.
