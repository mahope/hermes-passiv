/* color-names.js — det nærmeste CSS-navn til en hexfarve.
 *
 * Paletgeneratoren regner farver i hex. En ikke-designer kan ikke tale om
 * `#2563eb`, men kan sagtens tale om «den blå». Navnet er den sætning de
 * mangler, når de har fået en farve ud af et logo og skal forklare den til en
 * anden.
 *
 * Tabellen er de navngivne CSS-farver fra CSS Color Module Level 4. Spec'en
 * lister 148 navne, men ni af dem er dubletter (aqua/cyan, fuchsia/magenta og
 * de syv gray/grey-par), så der er 139 forskellige farver. Hver farve står kun
 * med én stavning, den amerikanske, så den ikke kan få to navne alt efter
 * rækkefølgen.
 *
 * `nearestName()` er ren og uden DOM, så `tests/color-names.test.mjs` kan kalde
 * den direkte og holde svaret op mod kendte farver.
 *
 *   COLOR_NAMES.nearestName('#dc143c')  // 'crimson'
 */
(function (global) {
  'use strict';

  var TABLE = [
    ['aliceblue', 'f0f8ff'], ['antiquewhite', 'faebd7'], ['aqua', '00ffff'],
    ['aquamarine', '7fffd4'], ['azure', 'f0ffff'], ['beige', 'f5f5dc'],
    ['bisque', 'ffe4c4'], ['black', '000000'], ['blanchedalmond', 'ffebcd'],
    ['blue', '0000ff'], ['blueviolet', '8a2be2'], ['brown', 'a52a2a'],
    ['burlywood', 'deb887'], ['cadetblue', '5f9ea0'], ['chartreuse', '7fff00'],
    ['chocolate', 'd2691e'], ['coral', 'ff7f50'], ['cornflowerblue', '6495ed'],
    ['cornsilk', 'fff8dc'], ['crimson', 'dc143c'], ['darkblue', '00008b'],
    ['darkcyan', '008b8b'], ['darkgoldenrod', 'b8860b'], ['darkgray', 'a9a9a9'],
    ['darkgreen', '006400'], ['darkkhaki', 'bdb76b'], ['darkmagenta', '8b008b'],
    ['darkolivegreen', '556b2f'], ['darkorange', 'ff8c00'], ['darkorchid', '9932cc'],
    ['darkred', '8b0000'], ['darksalmon', 'e9967a'], ['darkseagreen', '8fbc8f'],
    ['darkslateblue', '483d8b'], ['darkslategray', '2f4f4f'], ['darkturquoise', '00ced1'],
    ['darkviolet', '9400d3'], ['deeppink', 'ff1493'], ['deepskyblue', '00bfff'],
    ['dimgray', '696969'], ['dodgerblue', '1e90ff'], ['firebrick', 'b22222'],
    ['floralwhite', 'fffaf0'], ['forestgreen', '228b22'], ['fuchsia', 'ff00ff'],
    ['gainsboro', 'dcdcdc'], ['ghostwhite', 'f8f8ff'], ['gold', 'ffd700'],
    ['goldenrod', 'daa520'], ['gray', '808080'], ['green', '008000'],
    ['greenyellow', 'adff2f'], ['honeydew', 'f0fff0'], ['hotpink', 'ff69b4'],
    ['indianred', 'cd5c5c'], ['indigo', '4b0082'], ['ivory', 'fffff0'],
    ['khaki', 'f0e68c'], ['lavender', 'e6e6fa'], ['lavenderblush', 'fff0f5'],
    ['lawngreen', '7cfc00'], ['lemonchiffon', 'fffacd'], ['lightblue', 'add8e6'],
    ['lightcoral', 'f08080'], ['lightcyan', 'e0ffff'], ['lightgoldenrodyellow', 'fafad2'],
    ['lightgray', 'd3d3d3'], ['lightgreen', '90ee90'], ['lightpink', 'ffb6c1'],
    ['lightsalmon', 'ffa07a'], ['lightseagreen', '20b2aa'], ['lightskyblue', '87cefa'],
    ['lightslategray', '778899'], ['lightsteelblue', 'b0c4de'], ['lightyellow', 'ffffe0'],
    ['lime', '00ff00'], ['limegreen', '32cd32'], ['linen', 'faf0e6'],
    ['maroon', '800000'], ['mediumaquamarine', '66cdaa'], ['mediumblue', '0000cd'],
    ['mediumorchid', 'ba55d3'], ['mediumpurple', '9370db'], ['mediumseagreen', '3cb371'],
    ['mediumslateblue', '7b68ee'], ['mediumspringgreen', '00fa9a'], ['mediumturquoise', '48d1cc'],
    ['mediumvioletred', 'c71585'], ['midnightblue', '191970'], ['mintcream', 'f5fffa'],
    ['mistyrose', 'ffe4e1'], ['moccasin', 'ffe4b5'], ['navajowhite', 'ffdead'],
    ['navy', '000080'], ['oldlace', 'fdf5e6'], ['olive', '808000'],
    ['olivedrab', '6b8e23'], ['orange', 'ffa500'], ['orangered', 'ff4500'],
    ['orchid', 'da70d6'], ['palegoldenrod', 'eee8aa'], ['palegreen', '98fb98'],
    ['paleturquoise', 'afeeee'], ['palevioletred', 'db7093'], ['papayawhip', 'ffefd5'],
    ['peachpuff', 'ffdab9'], ['peru', 'cd853f'], ['pink', 'ffc0cb'],
    ['plum', 'dda0dd'], ['powderblue', 'b0e0e6'], ['purple', '800080'],
    ['rebeccapurple', '663399'], ['red', 'ff0000'], ['rosybrown', 'bc8f8f'],
    ['royalblue', '4169e1'], ['saddlebrown', '8b4513'], ['salmon', 'fa8072'],
    ['sandybrown', 'f4a460'], ['seagreen', '2e8b57'], ['seashell', 'fff5ee'],
    ['sienna', 'a0522d'], ['silver', 'c0c0c0'], ['skyblue', '87ceeb'],
    ['slateblue', '6a5acd'], ['slategray', '708090'], ['snow', 'fffafa'],
    ['springgreen', '00ff7f'], ['steelblue', '4682b4'], ['tan', 'd2b48c'],
    ['teal', '008080'], ['thistle', 'd8bfd8'], ['tomato', 'ff6347'],
    ['turquoise', '40e0d0'], ['violet', 'ee82ee'], ['wheat', 'f5deb3'],
    ['white', 'ffffff'], ['whitesmoke', 'f5f5f5'], ['yellow', 'ffff00'],
    ['yellowgreen', '9acd32']
  ];

  function parseHex(hex) {
    var h = String(hex == null ? '' : hex).trim().replace(/^#/, '').toLowerCase();
    if (/^[0-9a-f]{3}$/.test(h)) {
      h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    }
    if (!/^[0-9a-f]{6}$/.test(h)) return null;
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  // Afstanden er «redmean»: den vægter grøn tungest og lader rød/grå bestemme
  // rød-blå-vægten. Det er den billige tilnærmelse til en opfattet afstand, og
  // den dømmer et navn rigtigt uden at skulle regne i Lab.
  function distance(r1, g1, b1, r2, g2, b2) {
    var rmean = (r1 + r2) / 2;
    var dr = r1 - r2, dg = g1 - g2, db = b1 - b2;
    return (2 + rmean / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rmean) / 256) * db * db;
  }

  var NAMED = TABLE.map(function (row) {
    var rgb = parseHex(row[1]);
    return { name: row[0], hex: row[1], r: rgb[0], g: rgb[1], b: rgb[2] };
  });

  function nearestName(hex) {
    var rgb = parseHex(hex);
    if (!rgb) return '';
    var best = null, bestDist = Infinity;
    for (var i = 0; i < NAMED.length; i++) {
      var n = NAMED[i];
      var d = distance(rgb[0], rgb[1], rgb[2], n.r, n.g, n.b);
      if (d < bestDist) { bestDist = d; best = n; }
    }
    return best ? best.name : '';
  }

  global.COLOR_NAMES = global.COLOR_NAMES || {};
  global.COLOR_NAMES.nearestName = nearestName;
  global.COLOR_NAMES.table = TABLE;
})(typeof window !== 'undefined' ? window : globalThis);
