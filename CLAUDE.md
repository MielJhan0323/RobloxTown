# In This Town — Roblox Story Studio

Claude is writer, voice director and video editor for "In This Town" Roblox story Shorts
(narrated, staged Roblox Studio scenes; one magical rule per town) and long 16:9 compilations.
Style reference: `reference/` — when unsure, pull frames with ffmpeg and look.

## Story format
- First line always: `In this town, <one magical rule>.`
- One first-person kid/teen narrator, casual + warm, short sentences. 250–400 words (~1.5–2.5 min).
- Beats: rule (0–5 s) → 3–5 quick funny worldbuilding examples (5–25 s) → inciting "Then, ..." →
  personal stakes (family / loss / secret; time skips OK) → turn (discovery / trick / reveal, short quoted exchange)
  → quiet emotional or clever payoff (often one final word or image). No "subscribe" inside the story.
- Wholesome, kid-safe, original (never copy other creators' stories, characters, channel names).
- Save to `scripts/<slug>.md` using `scripts/_TEMPLATE.md` (narration + shot table, ~1.5–2 s per row).

## Voice (locked in - the user approved this sound)
- ElevenLabs **Titan - ConvoAI + ContentAI** (`dtSEyYGNJqjrtBArPCVZ`), model `eleven_v4`, with an inline
  emotion tag on most lines: [curious] [dramatically] [excited] [playfully] [laughs softly] [sadly]
  [softly] [warmly] [whispering] [emotional]. Write the tags from the script's `## Delivery` table.
- Save the chosen take to `audio/voice/<slug>.mp3`; extra takes go to `output/voice_takes/`.
- `voice_fx` (tools/config.json) pitches it up **5.5 semitones** with the clean resample method
  (no rubberband / no WORLD - those sounded scuffed/glitchy). Matches the reference narrator's
  sound and pace (~4.5 words/s, short natural pauses).
- If ElevenLabs refuses (free tier is often blocked): fallback is Kokoro `am_adam:0.5,am_liam:0.5`
  via `python tools/tts_local.py <slug>` with `voice.prefer = "stock"`; tell the user it's the fallback.
- Music: user's `TEMPOREX - Numbers` instrumental loop (`output/music/`), set via the top-level
  `override.music` in `edits/<slug>.json`, ~-7.5 dB under the voice.

## Shots (user records in Roblox Studio)
Shot list gives: #, location, characters, pose/expression, camera (close/medium/wide, push-in/pan), props, seconds.
Each shot shows exactly what its sentence says; props get insert close-ups. Files: `raw/<slug>/shot_XX.mp4`.

## Pipeline (`tools/`)
```
python tools/render.py <slug> --preview --stills 8   # 540x960 ultrafast + check frames
python tools/render.py <slug>                        # final 1080x1920 30fps H.264 CRF18, AAC 192k, -14 LUFS
python tools/compile.py <slug1> <slug2> ... [--channel "Name"]   # 1920x1080 blurred-sides compilation + chapters
```
Steps: `transcribe.py` (faster-whisper words → `edits/<slug>.words.json`) → `plan.py` (script ↔ word alignment →
`edits/<slug>.json`) → `captions.py` (one-word ASS) → `audio.py` (voice + ducked music −22 dB + ambience + SFX,
ending swell, two-pass loudnorm) → `video.py` (cover-crop 9:16, push-in/pan/punch, grade, cuts/fog/sparkle/flash,
vignette, captions, mux).
- Manual tweaks go in `"override"` objects in `edits/<slug>.json` (per shot or top level) — they survive re-planning.
  Per shot: `transition` (cut|fog|sparkle|flash), `transition_dur`, `motion` (push_in|pull_out|pan_left|pan_right|pan_up|pan_down|punch|drift),
  `grade` (warm|cool|neutral|none), `src`, `src_in`, `speed`, `focus_x`, `focus_y`.
  Top level: `captions` (size, y_pct, …), `audio` (music_db, …), `music` ({file, db}).
- Defaults live in `tools/config.json`. Missing shots render as blurred placeholder cards with the shot description.
- Set `ITT_ROOT=/some/dir` to run the tools against another project folder (tests).
- Caption font: first font in `assets/fonts/`, else `tools/fonts/Montserrat-ExtraBold.otf` (OFL).
- Animated 3D stand-in shots (until real Roblox Studio recordings exist): `python tools/animate.py <slug> [shots] [--stills]`
  renders Blender clips to `output/anim/<slug>/shot_XX.mp4` from `tools/anim/stories/<slug>.py` (one function per shot,
  built with `tools/anim/kit.py`: blocky posable characters with blink/talk/expressions, sets, lighting, beams).
  `raw/<slug>/shot_XX.mp4` always wins over these. Needs `apt-get install -y blender xvfb`. ~1 s/rendered frame
  (540x960, animated on twos); check `--stills` contact sheets before a full render.
- Stand-ins (never committed, live in `output/stock/`, real `audio/` files always win):
  `python tools/stock_audio.py` synthesizes original piano music + waves/wind/town ambience + shimmer/knock/click;
  `python tools/tts_local.py <slug>` makes a Piper narration (`pip install piper-tts`) when ElevenLabs isn't available.
- Setup if missing: `apt-get install -y ffmpeg fonts-montserrat`, `pip install -r tools/requirements.txt`.

## Workflow per request
1. New story: pitch 2–3 rule ideas, user picks, then write script + shot list.
2. Voice: generate (ElevenLabs) or wait for recording.
3. List exactly which `raw/<slug>/shot_XX.mp4` are missing (placeholders keep the edit previewable).
4. Preview render, look at 6–10 frames yourself (caption readable, on chest not face, shots match words); fix first.
5. Final render; report output path, length, shot table with timestamps.

## Rules
- Never modify/delete `reference/`, `raw/`, `audio/`, `assets/`. Write only to `scripts/`, `edits/`, `tools/`, `output/`.
- Only music/SFX in the repo or clearly royalty-free. Kid-friendly always.
- Commit scripts, edits, tools. Never commit video/audio (`.gitignore` covers raw/, output/, reference/, audio/).
