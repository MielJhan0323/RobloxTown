"""Shared helpers for the In This Town pipeline.

All paths resolve against the repo root. Set ITT_ROOT to point the tools at a
different project folder (handy for tests without touching raw/ or audio/).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ITT_ROOT", TOOLS.parent)).resolve()

SCRIPTS = ROOT / "scripts"
EDITS = ROOT / "edits"
RAW = ROOT / "raw"
VOICE = ROOT / "audio" / "voice"
MUSIC = ROOT / "audio" / "music"
SFX = ROOT / "audio" / "sfx"
FONTS = ROOT / "assets" / "fonts"
FX = ROOT / "assets" / "fx"
OUTPUT = ROOT / "output"

FPS = 30
W, H = 1080, 1920
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".webm")
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac")


def config() -> dict:
    p = TOOLS / "config.json"
    return json.loads(p.read_text()) if p.exists() else {}


def cache_dir(slug: str) -> Path:
    d = OUTPUT / "cache" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def log(*a):
    print("[itt]", *a, file=sys.stderr, flush=True)


def run(cmd: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    if cmd[0] == "ffmpeg":
        cmd = ["ffmpeg", "-hide_banner", "-y", "-loglevel", "error" if quiet else "info"] + cmd[1:]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        raise SystemExit(f"command failed: {' '.join(cmd[:6])} ...")
    return r


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def find_media(folder: Path, stem: str, exts) -> Path | None:
    for e in exts:
        p = folder / f"{stem}{e}"
        if p.exists():
            return p
    return None


def voice_path(slug: str) -> Path | None:
    return find_media(VOICE, slug, AUDIO_EXTS)


def raw_shot(slug: str, n: int) -> Path | None:
    return find_media(RAW / slug, f"shot_{n:02d}", VIDEO_EXTS)


def load_json(p: Path, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def save_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- text utils
_norm_re = re.compile(r"[^a-z0-9']+")


def norm_token(w: str) -> str:
    w = w.lower().replace("’", "'").replace("‘", "'")
    w = _norm_re.sub("", w).strip("'")
    return w


def tokens(text: str) -> list[str]:
    """Display tokens (keep original spelling), splitting on whitespace and dashes."""
    text = text.replace("—", " ").replace("–", " ").replace("--", " ")
    return [t for t in text.split() if norm_token(t)]


# ---------------------------------------------------------------- script parse
SHOT_COLS = ["n", "text", "location", "characters", "pose", "camera", "props", "mood", "fx", "sfx", "sec"]


def parse_script(slug: str) -> dict:
    """Read scripts/<slug>.md -> {title, rule, narration, shots:[...]}.

    The shot list is the markdown table under '## Shot list' with columns
    # | Narration | Location | Characters | Pose / expression | Camera | Props | Mood | FX | SFX | Sec
    """
    path = SCRIPTS / f"{slug}.md"
    if not path.exists():
        raise SystemExit(f"missing script {path}")
    md = path.read_text()
    title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), slug)
    shots = []
    in_table = False
    for line in md.splitlines():
        if line.lower().startswith("## shot list"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or not cells[0].strip().isdigit():
            continue  # header / separator
        cells += [""] * (len(SHOT_COLS) - len(cells))
        row = dict(zip(SHOT_COLS, cells))
        row["n"] = int(row["n"])
        try:
            row["sec"] = float(re.sub(r"[^0-9.]", "", row["sec"]) or 0)
        except ValueError:
            row["sec"] = 0.0
        shots.append(row)
    if not shots:
        raise SystemExit(f"no shot table found in {path}")
    return {"title": title, "shots": shots, "path": str(path)}


def font_file() -> Path | None:
    for d in (FONTS, TOOLS / "fonts"):
        if d.exists():
            for p in sorted(d.glob("*.[ot]tf")):
                return p
    return None


def font_dir() -> Path:
    f = font_file()
    return f.parent if f else TOOLS / "fonts"


def which(x):
    return shutil.which(x)
