# time-meter - scene setup for laptop Claude

Read with `scripts/time-meter.md` (shot list = what each shot must show) and `tools/laptop/RECORDING.md`.
Helpers: `tools/laptop/StoryKit.lua` (faces, wrist meter, counting meter, camera markers).

## Style (match the reference videos)
- **Classic flat face decals** (not Dynamic Heads), expressive, and they **change on the key word**:
  e.g. `neutral -> shocked` at 0.8 s. Faces sell the emotion more than poses - always set one.
- Warm, golden-hour lighting with soft haze for happy/memory scenes; cooler, dimmer light for
  sad/night scenes (`Lighting.ClockTime`, `Atmosphere`, `ColorCorrection` - set once per set).
- Characters held in clear poses; small movements only (head turn, arm raise, hand out).
- Camera: close (head + shoulders, face in the upper 40%), medium (waist up), wide (whole set).
  Place one marker Part per shot in `workspace.Cams` (`Shot01`, `Shot02`, ...) and use `K.lockCamera`.

## Build each set once (save the place after each) - then record its shots together

| Set | What to build | Shots |
|---|---|---|
| **A. Town street** | Main street at sunset, shops, lamps, people walking | 1, 3 |
| **B. Playground** | School yard, 3 kids | 4 |
| **C. Grandpa's kitchen** | Table, plate of broccoli | 5, 6 |
| **D. Uncle's living room** | Couch, lamp | 7 |
| **E. Park bench** | Bench, trees, sunset | 2, 8, 9, 10 (wrist inserts can use any arm here) |
| **F. Hospital** (the big one) | Two rooms facing each other across a short hallway: **Room 1** (Narrator) bed + IV stand + window + bedside table; **Room 2** (Lily) bed + window; doors open; hallway between | 11-31, 33-43, 47-61 |
| **G. Ambulance** | Simple ambulance interior, red/blue flashing light, blurry | 32 |
| **H. Treehouse** | Treehouse in a tree, rope ladder, golden sunset, two pudding cups | 44, 45, 46 |

Recording order suggestion: E, A, B, C, D (short), then F (most shots - Lily's stages in order),
then G, H. Lighting in F: day = warm (11-34), night = blue/dim (35-43), dawn = soft warm (47-61).

## Cast (same avatar every time)

| Character | Look | Notes |
|---|---|---|
| **Narrator** | teen boy, brown hair | hospital gown + **head bandage** in F; meter on left wrist |
| **Lily** | teen girl, long hair, **beaded bracelet on left wrist** | 4 stages (below); meter hidden under bracelet until shot 41 |
| young Narrator / young Lily | smaller copies with kid outfits | treehouse memory only (45, 46) |
| Grandpa, Uncle, 3 kids, Nurse, Doctor, passers-by | any fitting avatars | Doctor: white coat + clipboard |

**Lily's stages** (same avatar, change outfit/face/light only):
1 cheerful (15-21): bright clothes, `smile`/`grin`. 2 tired (22-23): `tired` face, leaning.
3 weak (24-50): hospital gown, blanket, **wheelchair** or bed, `tired`/`sad` faces, cooler light.
4 better (58-61): sitting up, `laugh`/`smile`, warm light.

## Per-shot plan

`Face` = start face, `->` = change to, `@` = seconds after recording starts.
`Meter` = text on that wrist meter (`K.setMeter(char, text)`); `hidden` = under the bracelet.

| # | Set | Who / action | Face | Meter | Camera |
|---|---|---|---|---|---|
| 1 | A | crowd walking | - | - | wide, slow push |
| 2 | E | passer-by raises wrist | - | `42 YEARS` | close on wrist |
| 3 | A | 3 people glance at wrists | neutral | various | medium |
| 4 | B | kids press wrists together | grin | `70 YEARS`, `68 YEARS` | medium |
| 5 | C | Grandpa shows wrist proudly | smirk | `20 YEARS` | close |
| 6 | C | Grandpa pushes plate away, arms crossed | smirk -> angry @0.6 (or `worried` if no angry face) | - | medium |
| 7 | D | Uncle: phone in one hand, staring at wrist | neutral -> shocked @0.8 | `35 YEARS` | medium |
| 8 | E | two people hold hands | smile | - | medium |
| 9 | E | wrists touch, `K.countMeter` on one wrist | smile | count 10 -> 25 YEARS | close on wrists |
| 10 | E | single wrist, meter dims | - | `1 TIME` -> hide @0.8 | close |
| 11 | F | Narrator in bed, eyes opening | sleeping -> neutral @1.0 | `61 YEARS` | medium |
| 12 | F | Narrator holds head | worried | - | close |
| 13 | F | Narrator at window, back half-turned | sad | - | medium |
| 14 | F | Narrator looks at wrist | neutral -> shocked @0.7 | `61 YEARS` | close on wrist |
| 15 | F | Lily (st.1) leans in Room 1 doorway | grin | hidden | medium |
| 16 | F | Lily waves | smile | hidden | close |
| 17 | F | Lily puts pudding cups on bedside table | smile | hidden | close insert |
| 18 | F | Lily laughs at own joke, Narrator groans | Lily laugh / Narrator embarrassed | - | medium |
| 19 | F | Lily pulls bracelet over wrist | neutral | hidden | close insert |
| 20 | F | cards on bed, Nurse points at door | Lily laugh, Nurse smirk | - | medium |
| 21 | F | Lily swaps a card secretly | smirk | - | close |
| 22 | F | Lily (st.2) leans on door frame, yawns | tired | hidden | medium |
| 23 | F | view across hallway: Lily in Room 2 bed waves weakly | tired | hidden | wide |
| 24 | F | Lily (st.3) in wheelchair at doorway, blanket | tired -> smile @1.0 | hidden | medium |
| 25 | F | Lily whispers a joke, Narrator leans in | Lily tired / Narrator worried | - | close |
| 26 | F | Lily holds out grape pudding | smile | hidden | medium |
| 27 | F | Narrator, hand half raised | neutral -> shocked @0.5 | - | close |
| 28 | F | Narrator tilts head, asking | talk | - | close |
| 29 | F | Lily looks away | smile | - | close |
| 30 | F | Lily shrugs | smirk | - | close |
| 31 | F | Doctor reads clipboard, morning light | neutral | - | medium |
| 32 | G | wrist meter flashing | - | `0` | close on wrist |
| 33 | F | Doctor lowers clipboard | sad | - | close |
| 34 | F | Doctor shakes head slightly | sad | - | close |
| 35 | F (night) | Narrator awake in bed | neutral -> worried @1.0 | - | medium |
| 36 | F (night) | stack of empty grape pudding cups | - | - | close insert |
| 37 | F | Lily's hand pulls bracelet down (memory) | - | hidden | close insert |
| 38 | F (night) | Lily asleep in wheelchair, Room 2 | sleeping | hidden | medium through doorway |
| 39 | F (night) | Narrator stands up by himself | determined | - | medium |
| 40 | F (night) | Narrator walks across the hallway | determined | - | medium, pan |
| 41 | F (night) | his hand slides her bracelet down | - | `1 DAY` (now visible) | close insert |
| 42 | F (night) | Lily's wrist | - | `1 DAY` | close, punch |
| 43 | F (night) | Narrator, hand on head | shocked | - | close, punch |
| 44 | H | treehouse, empty | - | - | wide |
| 45 | H | young Lily grins | grin | - | close |
| 46 | H | young pair share pudding | laugh | - | medium |
| 47 | F (dawn) | Narrator at Lily's bed | sad -> crying @0.8 | - | close |
| 48 | F | Lily looks down | sad | `1 DAY` | close |
| 49 | F | Lily small sad smile | sad -> smile @1.0 | - | close |
| 50 | F | Lily looks up | crying | - | close |
| 51 | F | Narrator sits on bed edge | sad | - | medium |
| 52 | F | Narrator small smile | determined | - | close, punch |
| 53 | F | wrists touch | - | his `61 YEARS`, hers `1 DAY` | close insert |
| 54 | F | meters flicker | - | `K.countMeter` both (quick random numbers) | close |
| 55 | F | hers counts up, his counts down | - | hers 0 -> 30, his 61 -> 30 (`" YEARS"`) | close, pan |
| 56 | F | meters freeze | - | `30 YEARS` both | close, punch |
| 57 | F | both meters side by side | - | `30 YEARS` both | close insert |
| 58 | F (warm) | Lily (st.4) laughing with tears | crying -> laugh @0.8 | `30 YEARS` | close |
| 59 | F | Lily whispers | smile -> talk @0.4 | - | close |
| 60 | F | Narrator splits the pudding | smile | - | medium |
| 61 | F (sunset window) | both side by side eating pudding | laugh | - | wide, pull-out |

## Recording a shot with a face change
1. Set the scene + `K.lockCamera(workspace.Cams.ShotXX)`, set the start face and meter.
2. Start the recording in the background: `screencapture -x -v -V <sec+1> -R x,y,w,h ~/RobloxTown/raw/time-meter/shot_XX.mov &`
3. Immediately run `K.faceSequence(char, {{0.8, "shocked"}})` (or `K.countMeter(...)`) via MCP.
4. Wait for the recording to finish; check the file isn't empty.
