/* Kelimeden turetilen procedural SVG gorsel.
 * Ayni kelime her zaman ayni gorseli uretir; hicbir dis dosya kullanilmaz.  */
(function (global) {
  "use strict";

  function hash(str) {                       // FNV-1a 32 bit
    var h = 0x811c9dc5;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = (h + (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24)) >>> 0;
    }
    return h >>> 0;
  }

  function rng(seed) {                       // mulberry32
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* Soz turu renk ailesini belirler, boylece gorsel ayni zamanda bilgi tasir. */
  var HUES = { noun: 212, verb: 18, adjective: 286, adverb: 158 };

  var W = 400, H = 200, CX = 200, CY = 100;

  function el(name, attrs) {
    var s = "<" + name;
    for (var k in attrs) if (attrs[k] !== undefined) s += " " + k + '="' + attrs[k] + '"';
    return s + "/>";
  }

  var MOTIFS = [
    // yorunge: es merkezli elipsler + uzerlerinde donen noktalar
    function (r, c) {
      var out = "", n = 3 + Math.floor(r() * 3);
      for (var i = 0; i < n; i++) {
        var rx = 40 + i * (26 + r() * 18), ry = rx * (0.42 + r() * 0.3);
        var rot = Math.floor(r() * 180);
        out += '<g transform="rotate(' + rot + ' ' + CX + ' ' + CY + ')">' +
          el("ellipse", { cx: CX, cy: CY, rx: rx.toFixed(1), ry: ry.toFixed(1),
                          fill: "none", stroke: c.line, "stroke-width": 1.2,
                          opacity: (0.5 - i * 0.06).toFixed(2) }) +
          '<circle r="4.5" fill="' + c.dot + '" opacity="0.9">' +
          '<animateMotion dur="' + (9 + i * 4) + 's" repeatCount="indefinite" ' +
          'path="M ' + (CX - rx) + ' ' + CY + ' a ' + rx.toFixed(1) + ' ' + ry.toFixed(1) +
          ' 0 1 1 ' + (2 * rx).toFixed(1) + ' 0 a ' + rx.toFixed(1) + ' ' + ry.toFixed(1) +
          ' 0 1 1 ' + (-2 * rx).toFixed(1) + ' 0"/></circle></g>';
      }
      return out;
    },
    // yaylar: merkezden acilan halka dilimleri
    function (r, c) {
      var out = "", n = 5 + Math.floor(r() * 4);
      for (var i = 0; i < n; i++) {
        var rad = 22 + i * 13, a0 = r() * Math.PI * 2, a1 = a0 + 0.6 + r() * 2.2;
        var x0 = CX + rad * Math.cos(a0), y0 = CY + rad * Math.sin(a0);
        var x1 = CX + rad * Math.cos(a1), y1 = CY + rad * Math.sin(a1);
        out += '<path d="M ' + x0.toFixed(1) + ' ' + y0.toFixed(1) + ' A ' + rad +
          ' ' + rad + ' 0 ' + (a1 - a0 > Math.PI ? 1 : 0) + ' 1 ' +
          x1.toFixed(1) + ' ' + y1.toFixed(1) + '" fill="none" stroke="' + c.line +
          '" stroke-width="' + (2 + r() * 4).toFixed(1) + '" stroke-linecap="round" opacity="' +
          (0.65 - i * 0.05).toFixed(2) + '"/>';
      }
      return out;
    },
    // dalgalar
    function (r, c) {
      var out = "", n = 4 + Math.floor(r() * 4);
      for (var i = 0; i < n; i++) {
        var amp = 8 + r() * 26, y = 30 + i * (140 / n), ph = r() * 6;
        var d = "M -20 " + y.toFixed(1);
        for (var x = -20; x <= W + 20; x += 20) {
          d += " Q " + (x + 10) + " " + (y + Math.sin(x / 42 + ph) * amp).toFixed(1) +
               " " + (x + 20) + " " + (y + Math.sin((x + 20) / 42 + ph) * amp * 0.6).toFixed(1);
        }
        out += '<path d="' + d + '" fill="none" stroke="' + c.line +
          '" stroke-width="' + (1.5 + r() * 2).toFixed(1) + '" opacity="' +
          (0.55 - i * 0.05).toFixed(2) + '"/>';
      }
      return out;
    },
    // izgara
    function (r, c) {
      var out = "", step = 26 + Math.floor(r() * 14);
      for (var y = 12; y < H; y += step) {
        for (var x = 12; x < W; x += step) {
          var s = step * (0.25 + r() * 0.5);
          out += el("rect", { x: x.toFixed(1), y: y.toFixed(1),
                              width: s.toFixed(1), height: s.toFixed(1), rx: 2,
                              fill: r() > 0.55 ? c.dot : "none",
                              stroke: c.line, "stroke-width": 1,
                              opacity: (0.15 + r() * 0.5).toFixed(2) });
        }
      }
      return out;
    },
    // yumusak lekeler
    function (r, c) {
      var out = "", n = 3 + Math.floor(r() * 3);
      for (var i = 0; i < n; i++) {
        out += el("circle", { cx: (60 + r() * 280).toFixed(1),
                              cy: (30 + r() * 140).toFixed(1),
                              r: (40 + r() * 55).toFixed(1),
                              fill: i % 2 ? c.dot : c.line,
                              opacity: (0.18 + r() * 0.22).toFixed(2),
                              filter: "url(#vblur)" });
      }
      return out;
    },
    // isinsal
    function (r, c) {
      var out = "", n = 16 + Math.floor(r() * 22);
      for (var i = 0; i < n; i++) {
        var a = (i / n) * Math.PI * 2, r0 = 26 + r() * 16, r1 = r0 + 24 + r() * 62;
        out += '<line x1="' + (CX + r0 * Math.cos(a)).toFixed(1) +
          '" y1="' + (CY + r0 * Math.sin(a) * 0.62).toFixed(1) +
          '" x2="' + (CX + r1 * Math.cos(a)).toFixed(1) +
          '" y2="' + (CY + r1 * Math.sin(a) * 0.62).toFixed(1) +
          '" stroke="' + c.line + '" stroke-width="' + (1 + r() * 2.6).toFixed(1) +
          '" stroke-linecap="round" opacity="' + (0.3 + r() * 0.45).toFixed(2) + '"/>';
      }
      return out;
    },
    // spiral
    function (r, c) {
      var turns = 3 + r() * 3, pts = [], grow = 5 + r() * 4;
      for (var i = 0; i <= 240; i++) {
        var a = (i / 240) * turns * Math.PI * 2, rad = i / 240 * grow * 14;
        pts.push((CX + rad * Math.cos(a)).toFixed(1) + "," +
                 (CY + rad * Math.sin(a) * 0.6).toFixed(1));
      }
      return '<polyline points="' + pts.join(" ") + '" fill="none" stroke="' +
        c.line + '" stroke-width="2.2" stroke-linecap="round" opacity="0.6"/>' +
        el("circle", { cx: CX, cy: CY, r: 5, fill: c.dot, opacity: 0.9 });
    },
    // ucgen orgu
    function (r, c) {
      var out = "", step = 34 + Math.floor(r() * 16);
      for (var y = 0; y < H + step; y += step) {
        for (var x = 0; x < W + step; x += step) {
          var up = r() > 0.5, h = step * 0.86;
          var p = up
            ? [x, y + h, x + step / 2, y, x + step, y + h]
            : [x, y, x + step, y, x + step / 2, y + h];
          out += '<polygon points="' + p.map(function (v) { return v.toFixed(1); }).join(" ") +
            '" fill="' + (r() > 0.65 ? c.dot : "none") + '" stroke="' + c.line +
            '" stroke-width="0.9" opacity="' + (0.12 + r() * 0.4).toFixed(2) + '"/>';
        }
      }
      return out;
    }
  ];

  /** Kelime + soz turu icin SVG isaretlemesi dondurur. */
  function render(word, pos) {
    var seed = hash(word);
    var r = rng(seed);
    var base = (HUES[pos] === undefined ? 212 : HUES[pos]) + (r() * 46 - 23);
    var alt = base + 28 + r() * 54;
    var sat = 62 + r() * 22;

    var c = {
      bg0: "hsl(" + base.toFixed(0) + " " + sat.toFixed(0) + "% 92%)",
      bg1: "hsl(" + alt.toFixed(0) + " " + sat.toFixed(0) + "% 82%)",
      line: "hsl(" + base.toFixed(0) + " " + (sat * 0.9).toFixed(0) + "% 34%)",
      dot: "hsl(" + alt.toFixed(0) + " " + sat.toFixed(0) + "% 44%)"
    };

    var motif = MOTIFS[seed % MOTIFS.length];
    var spin = (seed % 2 ? 1 : -1) * (40 + (seed % 40));

    return '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="xMidYMid slice" ' +
      'xmlns="http://www.w3.org/2000/svg" role="presentation" focusable="false">' +
      "<defs>" +
      '<linearGradient id="vg" x1="0" y1="0" x2="1" y2="1">' +
      '<stop offset="0" stop-color="' + c.bg0 + '"/>' +
      '<stop offset="1" stop-color="' + c.bg1 + '"/></linearGradient>' +
      '<filter id="vblur"><feGaussianBlur stdDeviation="18"/></filter>' +
      "</defs>" +
      el("rect", { width: W, height: H, fill: "url(#vg)" }) +
      '<g class="visual-motif" style="--spin:' + spin + 's">' + motif(r, c) + "</g>" +
      "</svg>";
  }

  global.WordVisual = { render: render, hash: hash };
})(window);
