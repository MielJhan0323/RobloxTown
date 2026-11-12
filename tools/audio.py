#!/usr/bin/env python3
"""Voice + ducked music + ambience + SFX -> output/cache/<slug>/mix.wav at -14 LUFS.

Music sits at ~-22 dB, is side-chain ducked under the voice, fades in, and
swells a little over the ending (last shot + tail).

usage: python tools/audio.py <slug>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EDITS, ROOT, cache_dir, config, load_json, log, run  # noqa: E402

AF = "aformat=sample_rates=48000:channel_layouts=stereo"


def mix(slug: str) -> Path:
    acfg = config().get("audio", {})
    data = load_json(EDITS / f"{slug}.json")
    if not data:
        raise SystemExit(f"run plan.py {slug} first")
    acfg = {**acfg, **(data.get("override") or {}).get("audio", {})}
    D = data["duration"]
    inputs, parts, mixins = [], [], []

    def add_input(args):
        inputs.extend(args)
        return sum(1 for a in inputs if a == "-i") - 1

    # voice (or silence for an animatic)
    if data.get("voice") and (ROOT / data["voice"]).exists():
        vi = add_input(["-i", ROOT / data["voice"]])
        parts.append(f"[{vi}:a]{AF},apad=whole_dur={D:.3f},atrim=0:{D:.3f},asplit=2[voice][key]")
    else:
        vi = add_input(["-f", "lavfi", "-t", f"{D:.3f}", "-i", "anullsrc=r=48000:cl=stereo"])
        parts.append(f"[{vi}:a]{AF},asplit=2[voice][key]")
    mixins.append("[voice]")

    music = (data.get("override") or {}).get("music", data.get("music"))
    if music and (ROOT / music["file"]).exists():
        mi = add_input(["-stream_loop", "-1", "-i", ROOT / music["file"]])
        db = music.get("db", acfg.get("music_db", -22))
        last = data["shots"][-1]
        t0 = max(0.0, last["start"] - 1.0)
        swell = 10 ** (acfg.get("ending_swell_db", 4) / 20)
        ramp = max(1.0, D - t0)
        parts.append(
            f"[{mi}:a]{AF},atrim=0:{D:.3f},asetpts=PTS-STARTPTS,volume={db}dB,"
            f"afade=t=in:d=1.2,afade=t=out:st={max(0, D - 1.6):.3f}:d=1.6[mus0]")
        parts.append(f"[mus0][key]sidechaincompress=threshold=0.025:ratio={acfg.get('duck_ratio', 6)}:"
                     f"attack=25:release=400:makeup=1[mus1]")
        parts.append(f"[mus1]volume='if(gt(t,{t0:.3f}),1+({swell:.3f}-1)*min(1,(t-{t0:.3f})/{ramp:.3f}),1)':eval=frame[mus]")
        mixins.append("[mus]")
    else:
        parts.append("[key]anullsink")

    for k, a in enumerate(data.get("ambience", [])):
        p = ROOT / a["file"]
        if not p.exists():
            continue
        ai = add_input(["-stream_loop", "-1", "-i", p])
        L = max(0.3, a["end"] - a["start"])
        parts.append(f"[{ai}:a]{AF},atrim=0:{L:.3f},asetpts=PTS-STARTPTS,volume={a.get('db', acfg.get('ambience_db', -30))}dB,"
                     f"afade=t=in:d=0.6,afade=t=out:st={max(0, L - 0.6):.3f}:d=0.6,adelay={int(a['start'] * 1000)}:all=1[amb{k}]")
        mixins.append(f"[amb{k}]")

    auto_sfx = [] if (data.get("override") or {}).get("sfx_auto") is False else data.get("sfx", [])
    for k, s in enumerate(auto_sfx):  # override.sfx_auto = false -> only the hand-placed sfx_extra play
        p = ROOT / s["file"]
        if not p.exists():
            continue
        si = add_input(["-i", p])
        parts.append(f"[{si}:a]{AF},volume={s.get('db', acfg.get('sfx_db', -14))}dB,adelay={int(max(0, s['t']) * 1000)}:all=1[sfx{k}]")
        mixins.append(f"[sfx{k}]")

    # extra hand-placed SFX: override.sfx_extra = [{"sfx": "boom", "shot": 6, "at": 0.55, "db": -9, "dur": 2.0}, ...]
    # "at" is seconds from the shot's start (negative = before it). "sfx" is a keyword matched in
    # audio/sfx then output/stock/sfx, or a path relative to the repo.
    from common import SFX as SFX_DIR, STOCK
    starts = {sh["n"]: sh["start"] for sh in data["shots"]}

    def find_sfx(key):
        p = ROOT / key
        if p.exists():
            return p
        for d in (SFX_DIR, STOCK / "sfx"):
            if d.exists():
                for f in sorted(d.iterdir()):
                    if key.lower() in f.stem.lower():
                        return f
        return None

    for k, e in enumerate((data.get("override") or {}).get("sfx_extra", [])):
        f = find_sfx(e["sfx"])
        if not f or e.get("shot") not in starts:
            log(f"sfx_extra: skipped {e}")
            continue
        t = max(0.0, starts[e["shot"]] + float(e.get("at", 0)))
        xi = add_input(["-i", f])
        # optional "dur": cut the sound after this many seconds (with a short fade), e.g. rain/wind beds
        cut = ""
        if e.get("dur"):
            L = float(e["dur"])
            cut = f"atrim=0:{L:.3f},afade=t=out:st={max(0, L - 0.4):.3f}:d=0.4,"
        parts.append(f"[{xi}:a]{AF},{cut}volume={e.get('db', acfg.get('sfx_db', -14))}dB,adelay={int(t * 1000)}:all=1[sx{k}]")
        mixins.append(f"[sx{k}]")

    parts.append(f"{''.join(mixins)}amix=inputs={len(mixins)}:normalize=0:duration=first,atrim=0:{D:.3f}[pre]")
    cd = cache_dir(slug)
    pre = cd / "premix.wav"
    graph = ";".join(parts)
    run(["ffmpeg", *inputs, "-filter_complex", graph, "-map", "[pre]", "-ar", "48000", "-c:a", "pcm_s16le", pre])

    # two-pass loudnorm
    target = acfg.get("lufs", -14)
    r = run(["ffmpeg", "-i", pre, "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], quiet=False)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    out = cd / "mix.wav"
    if m:
        st = json.loads(m.group(0))
        if float(st["input_i"]) < -70:  # silence (animatic without voice/music)
            run(["ffmpeg", "-i", pre, "-c:a", "pcm_s16le", out])
            return out
        ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
              f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    else:
        ln = f"loudnorm=I={target}:TP=-1.5:LRA=11"
    run(["ffmpeg", "-i", pre, "-af", ln + ",aresample=48000", "-c:a", "pcm_s16le", out])
    log(f"audio -> {out.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    mix(ap.parse_args().slug)
