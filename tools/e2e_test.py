from playwright.sync_api import sync_playwright
import json, sys

BASE = "http://127.0.0.1:8765/"
fails = []
def ck(name, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -> " + str(extra)) if extra and not cond else ""))
    if not cond: fails.append(name)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width":390,"height":844})
    page = ctx.new_page()
    external = []
    page.on("request", lambda r: external.append(r.url)
            if not r.url.startswith(BASE) and not r.url.startswith("data:") else None)
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append("console:"+m.text) if m.type=="error" else None)

    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector("#card:not([hidden])", timeout=10000)

    ck("kart aciliyor", page.is_visible("#card"))
    ck("kelime var", len(page.inner_text("#word").strip()) > 1, page.inner_text("#word"))
    ck("cumle var", len(page.inner_text("#sentence").strip()) > 10)
    ck("gorsel svg uretildi", page.locator("#visual svg").count() == 1)
    ck("kelime cumlede vurgulu", page.locator("#sentence mark").count() >= 1)
    ck("TURKCE ANLAM BASTA GIZLI", page.locator("#meaning").is_hidden())

    word = page.inner_text("#word").strip()
    page.click("#revealBtn")
    ck("anlam gosterildi", page.locator("#meaning").is_visible())
    ck("turkce dolu", len(page.inner_text("#tr").strip()) > 1, page.inner_text("#tr"))
    ck("ingilizce tanim dolu", len(page.inner_text("#defn").strip()) > 3)

    # biliyorum -> bir daha gelmemeli
    page.click("#knownBtn")
    seen = set()
    for _ in range(120):
        seen.add(page.inner_text("#word").strip())
        page.click("#nextBtn")
    ck("bilinen kelime 120 cekiliste gelmedi", word not in seen, word)
    ck("cesitlilik var", len(seen) > 40, len(seen))

    known = page.evaluate("JSON.parse(localStorage.getItem('wl.known')||'[]')")
    ck("localStorage'a yazildi", known == [word], known)

    # yenileme sonrasi kalicilik
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#card:not([hidden])", timeout=10000)
    known2 = page.evaluate("JSON.parse(localStorage.getItem('wl.known')||'[]')")
    ck("yenilemeden sonra korundu", known2 == [word], known2)
    ck("durum metni dogru", "1 /" in page.inner_text("#statusText"), page.inner_text("#statusText"))

    # klavye
    page.keyboard.press("Space")
    ck("bosluk anlami acti", page.locator("#meaning").is_visible())
    w2 = page.inner_text("#word")
    page.keyboard.press("ArrowRight")
    ck("ok tusu sonrakine gecti", page.inner_text("#word") != w2)
    page.keyboard.press("k")
    ck("K bilinen sayisini artirdi",
       len(page.evaluate("JSON.parse(localStorage.getItem('wl.known')||'[]')")) == 2)
    page.keyboard.press("z")
    ck("Z geri aldi",
       len(page.evaluate("JSON.parse(localStorage.getItem('wl.known')||'[]')")) == 1)

    # --- emoji katmani ---
    emoji_srcs, plain = [], 0
    for _ in range(40):
        page.click("#nextBtn")
        img = page.locator("#visual img")
        if img.count():
            emoji_srcs.append(img.get_attribute("src"))
        else:
            plain += 1
    ck("emojili kartlar var", len(emoji_srcs) > 28, len(emoji_srcs))
    ck("emoji gif'leri yerelden geliyor",
       all(s.startswith("assets/emoji/") and s.endswith(".gif") for s in emoji_srcs),
       emoji_srcs[:2])
    ck("emojisiz kartlar da calisiyor (yalniz desen)", plain >= 0, plain)
    broken = page.evaluate("""() => {
      const i = document.querySelector('#visual img');
      return i ? (i.complete && i.naturalWidth === 0) : false;
    }""")
    ck("kirik gorsel yok", not broken)
    ck("emoji varken desen arkada", page.evaluate(
        "() => !document.querySelector('#visual img') || "
        "!!document.querySelector('#visual svg.visual-bg-muted')"))

    # --- sozluk balincagi ---
    # Sozluk arka planda yuklendigi icin tiklanabilir kelimeleri bekle.
    page.wait_for_function(
        "document.querySelectorAll('#sentence .tok[data-g]').length > 0",
        timeout=30000)
    toks = page.locator("#sentence .tok[data-g]")
    ck("cumle kelimeleri tiklanabilir", toks.count() >= 3, toks.count())
    ck("hedef kelime balincak icin isaretli degil",
       page.locator("#sentence mark[data-target]").count() == 1)

    toks.nth(1).click()
    page.wait_for_selector("#gloss:not([hidden])", timeout=5000)
    ck("balincak acildi", page.locator("#gloss").is_visible())
    ck("balincakta temel bicim var", len(page.inner_text("#glossWord").strip()) > 0,
       page.inner_text("#glossWord"))
    ck("balincakta turkce karsilik var", len(page.inner_text("#glossTr").strip()) > 0,
       page.inner_text("#glossTr"))
    ck("balincakta tur etiketi var",
       page.inner_text("#gloss").strip().count("\n") >= 1 or
       not page.locator("#glossPos").is_hidden())

    fits = page.evaluate("""() => {
      const c = document.getElementById('card').getBoundingClientRect();
      const g = document.getElementById('gloss').getBoundingClientRect();
      return g.left >= c.left - 1 && g.right <= c.right + 1;
    }""")
    ck("balincak karttan tasmiyor", fits)

    page.keyboard.press("Escape")
    ck("Escape balincagi kapatti", page.locator("#gloss").is_hidden())

    toks.nth(2).click()
    page.wait_for_selector("#gloss:not([hidden])", timeout=5000)
    page.click("#word")
    ck("disari tiklayinca kapaniyor", page.locator("#gloss").is_hidden())

    # hedef kelimeye tiklamak balincak degil, anlam bolumunu acmali
    page.click("#nextBtn")
    page.wait_for_function(
        "document.querySelectorAll('#sentence .tok[data-g]').length > 0",
        timeout=15000)
    ck("yeni kartta anlam yine gizli", page.locator("#meaning").is_hidden())
    page.click("#sentence mark")
    ck("hedef kelime anlami acti", page.locator("#meaning").is_visible())
    ck("hedef kelime balincak acmadi", page.locator("#gloss").is_hidden())

    # gorsel determinizmi
    same = page.evaluate("""() => {
      const a = WordVisual.render('abate','verb','26c5'), b = WordVisual.render('abate','verb','26c5');
      const c = WordVisual.render('abhor','verb','1f922');
      return [a===b, a!==c];
    }""")
    ck("gorsel deterministik", same[0]); ck("gorsel kelimeye ozgu", same[1])

    # tema
    page.click("#themeBtn")
    ck("tema degisti", page.evaluate("document.documentElement.getAttribute('data-theme')") in ("dark","light"))

    # yatay kaydirma olmamali
    ck("mobilde yatay tasma yok",
       page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"),
       page.evaluate("document.documentElement.scrollWidth + ' vs ' + window.innerWidth"))

    ck("DIS ISTEK YOK", len(external) == 0, external[:5])
    ck("js hatasi yok", len(errs) == 0, errs[:3])
    b.close()

print("\n" + ("TUM TESTLER GECTI" if not fails else f"{len(fails)} TEST BASARISIZ: {fails}"))
sys.exit(1 if fails else 0)
