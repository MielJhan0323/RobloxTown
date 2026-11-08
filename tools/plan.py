#!/usr/bin/env python3
"""Script shot list + word timestamps -> edit plan  edits/<slug>.json

Each shot's start/end follows the voice. If there's no voice yet, timings are
estimated from the text (config speech_wps) so an animatic can still render.

Manual tweaks: put them in a shot's "override" object (or the top-level
"override") in edits/<slug>.json. Overrides survive re-planning. Examples:
  "override": {"transition": "fog", "transition_dur": 0.8}
  "override": {"motion": "punch", "src_in": 1.5, "focus_x": 0.3}
  "override": {"grade": "cool", "src": "raw/lost-hat/shot_07_take2.mp4"}

usage: python tools/plan.py <slug>
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (EDITS, MUSIC, ROOT, SCRIPTS, SFX, STOCK, AUDIO_EXTS, config, load_json, log,  # noqa: E402
                    norm_token, parse_script, probe_duration, raw_shot, save_json, tokens, voice_path)

TAIL = 1.4  # seconds held after the last word (ending breathes, music swells)


def classify_motion(camera: str, fx: str) -> str:
    c = f"{camera} {fx}".lower()
    if "punch" in c:
        return "punch"
    if "pull" in c or "zoom out" in c:
        return "pull_out"
    for k in ("left", "right", "up", "down"):
        if "pan" in c and k in c or ("tilt" in c and k in c):
            return f"pan_{k}"
    if "pan" in c:
        return "pan_right"
    if "static" in c or "hold" in c:
        return "drift"
    return "push_in"


def classify_transition(fx: str) -> str:
    f = fx.lower()
    if any(k in f for k in ("fog", "mist", "smoke", "dissolve", "dream")):
        return "fog"
    if any(k in f for k in ("sparkle", "magic", "shimmer")):
        return "sparkle"
    if "flash" in f:
        return "flash"
    return "cut"


def classify_grade(mood: str) -> str:
    m = mood.lower()
    if any(k in m for k in ("sad", "night", "dark", "blue", "rain", "cold", "lonely")):
        return "cool"
    if any(k in m for k in ("warm", "happy", "gold", "nostalg", "sunset", "summer", "joy")):
        return "warm"
    return "neutral"


def find_audio(folder: Path, keyword: str) -> Path | None:
    """First file in folder whose name contains keyword; falls back to output/stock/<kind>."""
    hit = _find(folder, keyword)
    return hit or _find(STOCK / folder.name, keyword)


def _find(folder: Path, keyword: str) -> Path | None:
    if not folder.exists():
        return None
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXTS)
    kw = keyword.lower().strip()
    for p in files:
        if kw and kw in p.stem.lower():
            return p
    return None


def script_meta(path: str) -> dict:
    meta = {}
    for line in Path(path).read_text().splitlines():
        m = re.match(r"^\*{0,2}(Music|Mood|Ambience)\*{0,2}\s*:\s*(.+)$", line.strip(), re.I)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip().strip("`")
    return meta


def align(script_words: list[dict], heard: list[dict]) -> None:
    """Give each script word start/end from the transcript (in place)."""
    a = [norm_token(w["w"]) for w in script_words]
    b = [norm_token(w["word"]) for w in heard]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            script_words[i + k]["s"] = heard[j + k]["start"]
            script_words[i + k]["e"] = heard[j + k]["end"]
    # Unmatched words: spread evenly between neighbouring matched words.
    n = len(script_words)
    i = 0
    while i < n:
        if "s" in script_words[i]:
            i += 1
            continue
        j = i
        while j < n and "s" not in script_words[j]:
            j += 1
        lo = script_words[i - 1]["e"] if i > 0 else 0.0
        hi = script_words[j]["s"] if j < n else (heard[-1]["end"] if heard else lo + 0.4 * (j - i))
        hi = max(hi, lo + 0.05 * (j - i))
        step = (hi - lo) / (j - i)
        for k in range(i, j):
            script_words[k]["s"] = round(lo + step * (k - i), 3)
            script_words[k]["e"] = round(lo + step * (k - i + 1), 3)
            script_words[k]["guess"] = True
        i = j


def estimate(script_words: list[dict], wps: float) -> None:
    t = 0.3
    for w in script_words:
        d = max(0.18, 1.0 / wps * (0.6 + 0.08 * len(norm_token(w["w"]))))
        w["s"], w["e"] = round(t, 3), round(t + d * 0.9, 3)
        t += d
        if w["w"][-1:] in ".!?":
            t += 0.25
        elif w["w"][-1:] in ",;:":
            t += 0.1


def plan(slug: str) -> dict:
    cfg = config()
    sc = parse_script(slug)
    meta = script_meta(sc["path"])
    out_path = EDITS / f"{slug}.json"
    old = load_json(out_path, {}) or {}
    old_over = {s["n"]: s.get("override", {}) for s in old.get("shots", [])}

    # words in script order, tagged with shot number
    words = []
    for s in sc["shots"]:
        for t in tokens(s["text"]):
            words.append({"w": t, "shot": s["n"]})

    vp = voice_path(slug)
    wj = load_json(EDITS / f"{slug}.words.json")
    if vp and wj and wj.get("words"):
        align(words, wj["words"])
        voice_dur = probe_duration(vp) or wj.get("duration", 0)
        matched = sum(1 for w in words if not w.get("guess"))
        log(f"aligned {matched}/{len(words)} script words to the voice")
        timing = "voice"
    else:
        estimate(words, cfg.get("speech_wps", 2.7))
        voice_dur = 0.0
        timing = "estimated"
        log("no voice/words yet -> estimated timings (animatic)")

    first = {}
    for w in words:
        first.setdefault(w["shot"], w["s"])
    last_end = max(w["e"] for w in words)
    total = max(voice_dur, last_end) + TAIL

    shots = []
    nums = [s["n"] for s in sc["shots"]]
    for idx, s in enumerate(sc["shots"]):
        n = s["n"]
        start = 0.0 if idx == 0 else first.get(n, None)
        if start is None:  # shot with no words (pure insert): split time with previous
            start = shots[-1]["start"] + (shots[-1]["end"] - shots[-1]["start"]) / 2 if shots else 0.0
        if shots:
            shots[-1]["end"] = round(start, 3)
        src = raw_shot(slug, n)
        shot = {
            "n": n,
            "text": s["text"],
            "start": round(start, 3),
            "end": None,
            "src": str(src.relative_to(ROOT)) if src else None,
            "src_dur": round(probe_duration(src), 3) if src else None,
            "motion": classify_motion(s["camera"], s["fx"]),
            "transition": "cut" if idx == 0 else classify_transition(s["fx"]),
            "grade": classify_grade(s["mood"]),
            "placeholder": None if src else " | ".join(x for x in (s["location"], s["characters"], s["pose"], s["camera"], s["props"]) if x and x.strip("- ")),
            "sfx": s["sfx"],
            "override": old_over.get(n, {}),
        }
        shots.append(shot)
    shots[-1]["end"] = round(total, 3)
    # pure-insert shots may have produced start>=end; clamp
    for i, s in enumerate(shots):
        s["dur"] = round(s["end"] - s["start"], 3)
        if s["dur"] > 3.2:
            log(f"note: shot {s['n']} holds {s['dur']:.1f}s (>3s) - consider splitting it in the script")
        if s["dur"] < 0.4:
            log(f"note: shot {s['n']} is only {s['dur']:.2f}s")

    # SFX / ambience from the SFX column: "door, shimmer" or "amb:waves"
    sfx, amb = [], []
    for s in shots:
        for item in [x.strip() for x in (s.pop("sfx") or "").split(",") if x.strip() and x.strip() != "-"]:
            off = 0.0
            if "@" in item:
                item, o = item.split("@", 1)
                off = float(o)
            if item.lower().startswith("amb:"):
                f = find_audio(SFX, item[4:])
                if f:
                    amb.append({"file": str(f.relative_to(ROOT)), "start": s["start"]})
                else:
                    log(f"no ambience file matching '{item[4:]}' in audio/sfx (shot {s['n']})")
            else:
                f = find_audio(SFX, item)
                if f:
                    sfx.append({"file": str(f.relative_to(ROOT)), "t": round(s["start"] + off, 3), "shot": s["n"]})
                else:
                    log(f"no sfx file matching '{item}' in audio/sfx (shot {s['n']})")
    for i, a in enumerate(amb):
        a["end"] = amb[i + 1]["start"] if i + 1 < len(amb) else total

    music = None
    mkw = meta.get("music", "")
    mf = find_audio(MUSIC, mkw) if mkw else None
    for folder in (MUSIC, STOCK / "music"):
        if mf or not folder.exists():
            continue
        cands = sorted(p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXTS)
        mf = cands[0] if cands else None
        if mf and mkw:
            log(f"no music matching '{mkw}', using {mf.name}")
    if mf:
        music = {"file": str(mf.relative_to(ROOT)), "db": cfg.get("audio", {}).get("music_db", -22)}
    else:
        log("no music in audio/music - rendering without music")

    data = {
        "slug": slug,
        "title": sc["title"],
        "timing": timing,
        "voice": str(vp.relative_to(ROOT)) if vp else None,
        "duration": round(total, 3),
        "shots": shots,
        "words": [{"w": w["w"], "s": w["s"], "e": w["e"], "shot": w["shot"]} for w in words],
        "music": music,
        "ambience": amb,
        "sfx": sfx,
        "override": old.get("override", {}),
    }
    save_json(out_path, data)
    missing = [s["n"] for s in shots if not s["src"]]
    log(f"plan -> edits/{slug}.json  ({len(shots)} shots, {total:.1f}s, timing={timing})")
    if missing:
        log(f"missing raw shots ({len(missing)}): " + ", ".join(f"shot_{n:02d}" for n in missing))
    return data


def effective(shot: dict) -> dict:
    """Shot with its override applied."""
    s = dict(shot)
    s.update(shot.get("override") or {})
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    a = ap.parse_args()
    plan(a.slug)
