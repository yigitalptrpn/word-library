/* Kelime Kutuphanesi - kart mantigi.
 * Calisma aninda yalnizca kendi data/*.json dosyalarini okur; dis istek yok. */
(function () {
  "use strict";

  var KNOWN_KEY = "wl.known";
  var THEME_KEY = "wl.theme";

  var $ = function (id) { return document.getElementById(id); };

  var state = {
    words: [],          // yuklenmis tum kelimeler
    known: new Set(),   // "biliyorum" isaretlileri
    undo: [],           // geri alma yigini
    current: null,
    total: 0,           // manifest'teki toplam
    loading: true,
    revealed: false
  };

  /* ---------------------------------------------------------------- depolama */

  function loadKnown() {
    try {
      var raw = localStorage.getItem(KNOWN_KEY);
      if (!raw) return new Set();
      var arr = JSON.parse(raw);
      return new Set(Array.isArray(arr) ? arr : []);
    } catch (e) {
      return new Set();
    }
  }

  function saveKnown() {
    try {
      localStorage.setItem(KNOWN_KEY, JSON.stringify(Array.from(state.known)));
    } catch (e) {
      /* private mode / kota: ilerleme bu oturumla sinirli kalir */
    }
  }

  /* ------------------------------------------------------------------- tema */

  function applyTheme(theme) {
    if (theme) document.documentElement.setAttribute("data-theme", theme);
    else document.documentElement.removeAttribute("data-theme");
  }

  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) { /* yok say */ }
    applyTheme(saved);
    $("themeBtn").addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme");
      var isDark = cur
        ? cur === "dark"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      var next = isDark ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* yok say */ }
    });
  }

  /* ------------------------------------------------------ kelime vurgulama */

  /* check_sentences.py'deki cekim kurallarinin tarayici karsiligi. */
  function inflections(w) {
    var f = [w, w + "s", w + "es", w + "ed", w + "ing", w + "d", w + "ly",
             w + "n", w + "r", w + "st"];
    if (/e$/.test(w)) {
      var b = w.slice(0, -1);
      f.push(b + "ed", b + "ing", b + "es", b + "er", b + "est", b + "y");
    }
    if (/[^aeiou]y$/.test(w)) {
      var c = w.slice(0, -1);
      f.push(c + "ies", c + "ied", c + "ier", c + "iest", c + "ily");
    }
    if (/ic$/.test(w)) f.push(w + "ally");
    if (w.length > 3 && /[^aeiouwxy]$/.test(w) &&
        /[aeiou]/.test(w[w.length - 2]) && /[^aeiou]/.test(w[w.length - 3])) {
      var d = w + w[w.length - 1];
      f.push(d + "ed", d + "ing", d + "er", d + "est");
    }
    if (/us$/.test(w)) f.push(w.slice(0, -2) + "i");
    if (/is$/.test(w)) f.push(w.slice(0, -2) + "es");
    if (/fe$/.test(w)) f.push(w.slice(0, -2) + "ves");
    else if (/f$/.test(w)) f.push(w.slice(0, -1) + "ves");
    return new Set(f);
  }

  /* Cumleyi, hedef kelime <mark> ile sarilmis halde DOM'a yazar. */
  function renderSentence(node, sentence, word) {
    var forms = inflections(word.toLowerCase());
    var stem = word.toLowerCase().slice(0, Math.max(4, word.length - 3));
    node.textContent = "";
    var parts = sentence.split(/(\s+)/);
    var hit = false;
    parts.forEach(function (part) {
      var bare = part.toLowerCase().replace(/[^a-z']/g, "");
      var match = bare && (forms.has(bare) ||
                           (!hit && bare.length >= stem.length && bare.indexOf(stem) === 0));
      if (match) {
        hit = true;
        var m = document.createElement("mark");
        m.textContent = part;
        node.appendChild(m);
      } else {
        node.appendChild(document.createTextNode(part));
      }
    });
  }

  /* ------------------------------------------------------------------ kart */

  function pickNext() {
    var pool = state.words;
    var n = pool.length;
    if (!n) return null;
    // Bilinmeyenler arasindan tekduze secim; ayni karti ust uste gostermez.
    var unknown = [];
    for (var i = 0; i < n; i++) {
      var w = pool[i];
      if (!state.known.has(w.w) && (!state.current || w.w !== state.current.w)) {
        unknown.push(w);
      }
    }
    if (!unknown.length) {
      // Tek kalan kelime mevcut kart olabilir.
      for (var j = 0; j < n; j++) {
        if (!state.known.has(pool[j].w)) return pool[j];
      }
      return null;
    }
    return unknown[Math.floor(Math.random() * unknown.length)];
  }

  function showCard(entry) {
    state.current = entry;
    state.revealed = false;

    $("visual").innerHTML = window.WordVisual.render(entry.w, entry.p);
    $("word").textContent = entry.w;
    $("pos").textContent = posLabel(entry.p);
    $("cefr").textContent = entry.c;
    renderSentence($("sentence"), entry.s, entry.w);

    $("tr").textContent = entry.t.join(" · ");
    $("defn").textContent = entry.d;
    $("meaning").hidden = true;
    $("revealBtn").hidden = false;

    $("card").hidden = false;
    $("finished").hidden = true;
    $("loading").hidden = true;
    $("card").classList.remove("card-in");
    void $("card").offsetWidth;          // animasyonu yeniden tetikle
    $("card").classList.add("card-in");
  }

  var POS_TR = {
    noun: "isim", verb: "fiil", adjective: "sıfat", adverb: "zarf"
  };
  function posLabel(p) { return POS_TR[p] || p; }

  function reveal() {
    if (!state.current || state.revealed) return;
    state.revealed = true;
    $("meaning").hidden = false;
    $("revealBtn").hidden = true;
  }

  function next() {
    var entry = pickNext();
    if (entry) { showCard(entry); return; }
    if (state.loading) { showLoading(); return; }
    showFinished();
  }

  function markKnown() {
    if (!state.current) return;
    state.known.add(state.current.w);
    state.undo.push(state.current.w);
    saveKnown();
    updateStatus();
    next();
  }

  function undo() {
    var w = state.undo.pop();
    if (!w) return;
    state.known.delete(w);
    saveKnown();
    updateStatus();
    var entry = null;
    for (var i = 0; i < state.words.length; i++) {
      if (state.words[i].w === w) { entry = state.words[i]; break; }
    }
    if (entry) showCard(entry);
  }

  /* ---------------------------------------------------------------- durum */

  function updateStatus() {
    var total = state.total || state.words.length;
    var known = state.known.size;
    var pct = total ? Math.min(100, (known / total) * 100) : 0;
    $("progressFill").style.width = pct.toFixed(1) + "%";
    $("progressBar").setAttribute("aria-valuenow", pct.toFixed(0));

    var loaded = state.words.length;
    var text = known.toLocaleString("tr-TR") + " / " +
               total.toLocaleString("tr-TR") + " kelime biliniyor";
    if (state.loading && loaded < total) {
      text += " · " + loaded.toLocaleString("tr-TR") + " yüklendi…";
    }
    $("statusText").textContent = text;
    $("undoBtn").hidden = state.undo.length === 0;
    $("settingsStats").textContent =
      "Kütüphanede " + total.toLocaleString("tr-TR") + " kelime var; " +
      known.toLocaleString("tr-TR") + " tanesini biliyorum olarak işaretlediniz.";
  }

  function showLoading() {
    $("loading").hidden = false;
    $("card").hidden = true;
    $("finished").hidden = true;
  }

  function showFinished() {
    $("finished").hidden = false;
    $("card").hidden = true;
    $("loading").hidden = true;
    state.current = null;
  }

  function showError(msg) {
    $("errorMsg").textContent = msg;
    $("error").hidden = false;
    $("loading").hidden = true;
    $("card").hidden = true;
  }

  /* ------------------------------------------------------------- yukleme */

  function fetchJSON(url) {
    return fetch(url, { cache: "force-cache" }).then(function (r) {
      if (!r.ok) throw new Error(url + " → HTTP " + r.status);
      return r.json();
    });
  }

  function load() {
    return fetchJSON("data/manifest.json").then(function (manifest) {
      var files = manifest.shards || [];
      if (!files.length) throw new Error("Kütüphane henüz boş.");
      state.total = manifest.total || 0;

      // Ilk kart icin rastgele bir shard: acilis her seferinde farkli olsun.
      var first = Math.floor(Math.random() * files.length);
      var order = [first];
      for (var i = 0; i < files.length; i++) if (i !== first) order.push(i);

      return fetchJSON("data/words/" + files[first].file).then(function (rows) {
        state.words = state.words.concat(rows);
        updateStatus();
        next();
        // Kalan shard'lar arka planda, sirayla.
        var chain = Promise.resolve();
        order.slice(1).forEach(function (idx) {
          chain = chain.then(function () {
            return fetchJSON("data/words/" + files[idx].file)
              .then(function (more) {
                state.words = state.words.concat(more);
                updateStatus();
                // Kart yokken (hepsi bilinen) yeni kelimeler geldiyse goster.
                if (!state.current && !$("finished").hidden) next();
              })
              .catch(function () { /* tek shard hatasi uygulamayi durdurmasin */ });
          });
        });
        return chain;
      });
    }).then(function () {
      state.loading = false;
      updateStatus();
      if (!state.current) next();
    }).catch(function (err) {
      state.loading = false;
      var hint = location.protocol === "file:"
        ? "Dosyayı doğrudan açtınız. Yerel sunucu gerekir: python3 -m http.server"
        : String(err && err.message ? err.message : err);
      showError(hint);
    });
  }

  /* ------------------------------------------------- disa / ice aktarma */

  function exportProgress() {
    var blob = new Blob([JSON.stringify({
      app: "kelime-kutuphanesi",
      version: 1,
      exportedAt: new Date().toISOString(),
      known: Array.from(state.known)
    }, null, 1)], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "kelime-kutuphanesi-ilerleme.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function importProgress(file) {
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var data = JSON.parse(String(reader.result));
        var list = Array.isArray(data) ? data : data.known;
        if (!Array.isArray(list)) throw new Error("format");
        list.forEach(function (w) {
          if (typeof w === "string") state.known.add(w);
        });
        saveKnown();
        updateStatus();
        alert(list.length + " kelime içe aktarıldı.");
        next();
      } catch (e) {
        alert("Dosya okunamadı: beklenen biçimde bir ilerleme dosyası değil.");
      }
    };
    reader.readAsText(file);
  }

  function reset() {
    if (!confirm("Bütün ilerleme silinecek. Emin misiniz?")) return;
    state.known.clear();
    state.undo.length = 0;
    saveKnown();
    updateStatus();
    state.current = null;
    next();
  }

  /* --------------------------------------------------------------- olaylar */

  function openSettings(open) {
    $("settings").hidden = !open;
    $("settingsBtn").setAttribute("aria-expanded", String(open));
    if (open) $("closeSettings").focus();
  }

  function bind() {
    $("revealBtn").addEventListener("click", reveal);
    $("nextBtn").addEventListener("click", next);
    $("knownBtn").addEventListener("click", markKnown);
    $("undoBtn").addEventListener("click", undo);
    $("restartBtn").addEventListener("click", reset);
    $("resetBtn").addEventListener("click", function () { reset(); openSettings(false); });
    $("exportBtn").addEventListener("click", exportProgress);
    $("importBtn").addEventListener("click", function () { $("importFile").click(); });
    $("importFile").addEventListener("change", function (e) {
      if (e.target.files && e.target.files[0]) importProgress(e.target.files[0]);
      e.target.value = "";
    });
    $("settingsBtn").addEventListener("click", function () {
      openSettings($("settings").hidden);
    });
    $("closeSettings").addEventListener("click", function () { openSettings(false); });
    $("settings").addEventListener("click", function (e) {
      if (e.target === $("settings")) openSettings(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.target.matches("input, textarea")) return;
      if (e.key === "Escape") { openSettings(false); return; }
      if (!$("settings").hidden) return;
      if (e.key === " " || e.code === "Space") { e.preventDefault(); reveal(); }
      else if (e.key === "ArrowRight" || e.key === "Enter") { e.preventDefault(); next(); }
      else if (e.key === "k" || e.key === "K") { markKnown(); }
      else if (e.key === "z" || e.key === "Z") { undo(); }
    });

    // Dokunmatik: sola kaydir = sonraki, saga kaydir = biliyorum
    var x0 = null, y0 = null;
    var card = $("card");
    card.addEventListener("touchstart", function (e) {
      x0 = e.changedTouches[0].clientX;
      y0 = e.changedTouches[0].clientY;
    }, { passive: true });
    card.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      var dy = e.changedTouches[0].clientY - y0;
      x0 = null;
      if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        if (dx < 0) next(); else markKnown();
      }
    }, { passive: true });
  }

  /* ------------------------------------------------------------------ acilis */

  state.known = loadKnown();
  initTheme();
  bind();
  updateStatus();
  load();
})();
