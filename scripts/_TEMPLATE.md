# <Story Title>

Rule: In this town, <one magical rule>.
Music: <mood keyword matching a file in audio/music, e.g. sad_piano>
Voice: <ElevenLabs voice name / id>

## Narration

In this town, <rule>. <3-5 quick funny examples> ... Then, <new character/event>...
(250-400 words, first-person kid/teen narrator, short sentences, quiet payoff ending.)

## Shot list

One row per sentence or half-sentence (~1.5-2 s each). `Narration` must be the
exact words spoken - plan.py matches it to the voice. Record each row as
`raw/<slug>/shot_XX.mp4`.

- Camera: `wide/medium/close` + `push-in` (default) | `pull-out` | `pan left/right/up/down` | `punch-in` (reveals) | `static`
- Mood: `warm` (happy/nostalgic, golden) | `sad`/`night` (cool, darker) | blank = neutral
- FX (transition INTO this shot): blank = hard cut | `fog` (time skip / dream / location change) | `sparkle` (magic) | `flash`
- SFX: comma list of keywords matching files in audio/sfx (`door, shimmer`, `click@0.5` = 0.5 s into the shot); `amb:waves` starts an ambience bed

| # | Narration | Location | Characters | Pose / expression | Camera | Props | Mood | FX | SFX | Sec |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | In this town, ... | Main Street at sunset, wide | - | - | wide, slow push-in | - | warm | - | amb:town | 2.5 |
| 2 | ... | | | | | | | | | |
