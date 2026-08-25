#!/usr/bin/env python3
"""Tests for the 6 v1.2.0 rules in the Python core (parity with test_rules_v112.js)."""
import sys

from eaa_scanner.core import scan_html


def rules(html):
    rep = scan_html(html)
    assert rep["ok"], rep.get("error")
    return {f["rule_id"]: f for f in rep["findings"]}


def check(name, html, rid, count=None, severity=None):
    r = rules(html)
    f = r.get(rid)
    if count == 0:
        assert f is None, f"{name}: expected no {rid}, got {f}"
        print(f"ok  {name} (absent)")
        return
    assert f is not None, f"{name}: expected {rid}, got none"
    assert f["count"] == count, f"{name}: count {f['count']} != {count}"
    if severity:
        assert f["severity"] == severity, f"{name}: sev {f['severity']} != {severity}"
    print(f"ok  {name}")


# INPUT_TYPE_IMAGE_ALT (1.1.1)
check("input-image no alt", '<form><input type="image" src="go.png"></form>',
      "INPUT_TYPE_IMAGE_ALT", 1, "error")
check("input-image with alt", '<form><input type="image" src="go.png" alt="Go"></form>',
      "INPUT_TYPE_IMAGE_ALT", 0)

# VIDEO_TRACKS (1.2.2)
check("video no track", '<video src="a.mp4"></video>', "VIDEO_TRACKS", 1, "error")
check("video with captions", '<video src="a.mp4"><track kind="captions" src="c.vtt"></video>',
      "VIDEO_TRACKS", 0)
check("video with subtitles", '<video src="a.mp4"><track kind="subtitles" srclang="da"></video>',
      "VIDEO_TRACKS", 0)

# AUDIO_TRANSCRIPT (1.2.1)
check("audio bare", '<audio src="x.mp3"></audio>', "AUDIO_TRANSCRIPT", 1, "warning")
check("audio labelled transcript",
      '<audio src="x.mp3" aria-label="Interview transcript below"></audio>',
      "AUDIO_TRANSCRIPT", 0)

# AUTOPLAY_MEDIA (1.4.2)
check("video autoplay no mute", '<video src="a.mp4" autoplay></video>',
      "AUTOPLAY_MEDIA", 1, "error")
check("video autoplay muted", '<video src="a.mp4" autoplay muted></video>',
      "AUTOPLAY_MEDIA", 0)
check("audio autoplay no controls", '<audio src="x.mp3" autoplay></audio>',
      "AUTOPLAY_MEDIA", 1, "error")
check("audio autoplay controls", '<audio src="x.mp3" autoplay controls></audio>',
      "AUTOPLAY_MEDIA", 0)

# MARQUEE_BLINK (2.2.2)
check("marquee element", "<marquee>news</marquee>", "MARQUEE_BLINK", 1, "error")
check("blink element", "<blink>hi</blink>", "MARQUEE_BLINK", 1)
check("text-decoration blink style",
      '<span style="text-decoration: blink">hi</span>', "MARQUEE_BLINK", 1)
check("normal span", '<span>hi</span>', "MARQUEE_BLINK", 0)

# POSITIVE_TABINDEX (2.4.3)
check("positive tabindex", '<div tabindex="3">x</div>', "POSITIVE_TABINDEX", 1, "warning")
check("zero tabindex", '<div tabindex="0">x</div>', "POSITIVE_TABINDEX", 0)
check("minus-one tabindex", '<div tabindex="-1">x</div>', "POSITIVE_TABINDEX", 0)

print("\nAll v1.2.0 rule tests passed.")
sys.exit(0)
