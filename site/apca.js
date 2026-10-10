/* apca.js — APCA (WCAG 3-udkast) som en Lc-værdi oveni WCAG 2-forholdet.
 *
 * `/contrast-checker` svarede med WCAG 2.1-forholdet (4.5:1 osv.). Det tal er
 * let at regne og let at sammenligne, men det er blindt for hvilken vej
 * farverne vender: 4.5:1 mørk-tekst-på-lys læses anderledes end 4.5:1
 * lys-tekst-på-mørk. APCA — Advanced Perceptual Contrast Algorithm — er den
 * kandidat, WCAG 3 bygger på, og den tager højde for polariteten. De førende
 * kontrasttjekkere viser begge tal; vi viste kun det ene.
 *
 * Modellen er **APCA 0.1.9 (W3, G-4g)**, ord for ord efter reference-
 * implementeringen i `Myndex/apca-w3` (W3-licens). Den er citeret her og ikke
 * genopfundet: konstanterne og de to formler er hele algoritmen, og en
 * afvigelse i ét eksponent- eller skaleringsled giver et andet tal.
 *
 *   APCA.contrast([r,g,b], [r,g,b])  ->  signeret Lc (fx 63.06 eller -68.54)
 *   APCA.label(lc)                   ->  kort råd på sidens sprog
 *
 * Lc er signeret med vilje: positivt betyder mørk tekst på lys baggrund,
 * negativt lys tekst på mørk. Vi kaster aldrig fortegnet væk — det er
 * netop den information WCAG 2-forholdet smider ud.
 *
 * Dommen ligger i `tests/apca.test.mjs`, der holder tallene op mod
 * referenceværdierne fra `apca-w3`'s egen testsuite.
 */
(function (global) {
  'use strict';

  // APCA 0.1.9, SAPC-8 G-4g — W3-kompatible konstanter.
  var mainTRC = 2.4;
  var sRco = 0.2126729, sGco = 0.7151522, sBco = 0.0721750;
  var normBG = 0.56, normTXT = 0.57, revTXT = 0.62, revBG = 0.65;
  var blkThrs = 0.022, blkClmp = 1.414;
  var scaleBoW = 1.14, scaleWoB = 1.14;
  var loBoWoffset = 0.027, loWoBoffset = 0.027;
  var deltaYmin = 0.0005, loClip = 0.1;

  // sRGB (0-255) -> Y, den lineære luminans APCA arbejder i. Bemærk at den
  // ikke bruger WCAG's stykvise 0.03928-kurve, men den rene 2.4-eksponent.
  function sRGBtoY(rgb) {
    return sRco * Math.pow(rgb[0] / 255, mainTRC) +
           sGco * Math.pow(rgb[1] / 255, mainTRC) +
           sBco * Math.pow(rgb[2] / 255, mainTRC);
  }

  // De to Y-værdier ind, et signeret Lc ud. Tekst først, baggrund bagefter —
  // rækkefølgen er ikke ligegyldig, fortegnet skifter med den.
  function contrast(fgRgb, bgRgb) {
    var txtY = sRGBtoY(fgRgb), bgY = sRGBtoY(bgRgb);
    if (isNaN(txtY) || isNaN(bgY)) return 0;

    // Blød klamp af nær-sort, som i referencen.
    txtY = txtY > blkThrs ? txtY : txtY + Math.pow(blkThrs - txtY, blkClmp);
    bgY = bgY > blkThrs ? bgY : bgY + Math.pow(blkThrs - bgY, blkClmp);
    if (Math.abs(bgY - txtY) < deltaYmin) return 0;

    var SAPC, output;
    if (bgY > txtY) {
      // Normal polaritet: mørk tekst på lys baggrund.
      SAPC = (Math.pow(bgY, normBG) - Math.pow(txtY, normTXT)) * scaleBoW;
      output = SAPC < loClip ? 0 : SAPC - loBoWoffset;
    } else {
      // Omvendt polaritet: lys tekst på mørk baggrund. Negativt Lc.
      SAPC = (Math.pow(bgY, revBG) - Math.pow(txtY, revTXT)) * scaleWoB;
      output = SAPC > -loClip ? 0 : SAPC + loWoBoffset;
    }
    return output * 100;
  }

  // Rådene er tærsklerne fra APCA's egen vejledning (beta 0.1.7/0.1.9), ikke
  // opfundet her. Lc 90 = foretrukket brødtekst, 75 = mindste brødtekst,
  // 60 = store overskrifter, 45 = store/fede tekster, 30 = absolut minimum,
  // 15 = ikke-tekst, derunder ikke brugbart til tekst.
  function label(lc, lang) {
    var a = Math.abs(lc);
    if (lang === 'da') {
      if (a >= 90) return 'Lc ' + lc.toFixed(0) + ' — foretrukket til brødtekst';
      if (a >= 75) return 'Lc ' + lc.toFixed(0) + ' — fint til brødtekst';
      if (a >= 60) return 'Lc ' + lc.toFixed(0) + ' — store overskrifter og fed tekst';
      if (a >= 45) return 'Lc ' + lc.toFixed(0) + ' — kun store eller fede tekster';
      if (a >= 30) return 'Lc ' + lc.toFixed(0) + ' — absolut minimum for tekst';
      if (a >= 15) return 'Lc ' + lc.toFixed(0) + ' — kun ikke-tekst (ikoner, rammer)';
      return 'Lc ' + lc.toFixed(0) + ' — ikke brugbart til tekst';
    }
    if (a >= 90) return 'Lc ' + lc.toFixed(0) + ' — preferred for body text';
    if (a >= 75) return 'Lc ' + lc.toFixed(0) + ' — fine for body text';
    if (a >= 60) return 'Lc ' + lc.toFixed(0) + ' — large headings and bold text';
    if (a >= 45) return 'Lc ' + lc.toFixed(0) + ' — large or bold text only';
    if (a >= 30) return 'Lc ' + lc.toFixed(0) + ' — absolute minimum for text';
    if (a >= 15) return 'Lc ' + lc.toFixed(0) + ' — non-text only (icons, borders)';
    return 'Lc ' + lc.toFixed(0) + ' — not usable for text';
  }

  global.APCA = { contrast: contrast, sRGBtoY: sRGBtoY, label: label };
})(typeof window !== 'undefined' ? window : this);
