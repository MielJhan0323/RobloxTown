# alpha-mark - scene setup for laptop Claude

Read with `scripts/alpha-mark.md` and `tools/laptop/RECORDING.md`. Helpers: `tools/laptop/StoryKit.lua`.

## Sets - only 2, both REUSED from workspace.Town.Sets (add small props only)

| Set | Reuse | Add | Shots |
|---|---|---|---|
| **A. Town street** | existing street | morning light, kids with backpacks | 1-4 |
| **B. School playground** | existing playground | a school wall with a faded **crown mural**, 2 long lunch tables + trays, 2 trash cans, a bench, a drinking fountain, a **rain** effect you can switch on/off (ParticleEmitter or Toolbox rain) | 5-37 |

Lighting presets: `warm` (1-13, 28-37 brightening as the crown appears), `night`/dusk (14-15), `sad` grey + rain (16-27). Shot 37: rain off, sun out.

## Cast - every character has real Roblox hair (catalog hair accessories, not block hair)

| Character | Look | Mark (left wrist, `K.setMeter`) |
|---|---|---|
| **Narrator** | kid, messy brown hair, hoodie | leaf under a black-marker claw (1-18); smeared streaks + leaf (19-26); crown (28+) |
| **Kai** | tallest kid, spiky hair, varsity jacket | red claw |
| **Cousin** | kid, cap or slick hair | red claw |
| 3 prey kids | small kids, different hair | green leaf |
| crowd kids (4-6) | mixed | mixed claws/leaves |

Marks: make one wrist plate per character with `K.setMeter(char, text)`: leaf = "🍃" (green text), claw = a red
claw/scratch symbol (e.g. "///" in red), crown = "👑" (gold). If emoji don't render, use a small decal on the plate.
Fake claw: black "///" drawn over the green leaf plate (two layers: leaf underneath, black claw on top that you hide in 19).

## Per-shot plan

| # | Set | Who / action | Face | Mark | Camera |
|---|---|---|---|---|---|
| 1 | A | kids walking to school | - | - | wide |
| 2 | A | a kid raises wrist | smile | leaf | close insert |
| 3 | A | shy kid shows leaf | smile | leaf | close insert |
| 4 | A | tough kid shows claw | smirk | claw | close insert |
| 5 | B | predators cut the line | smirk | claws | medium, pan |
| 6 | B | prey kids eat by trash cans | sad | leaves | medium |
| 7 | B | cousin flexes wrist | smirk | claw | medium |
| 8 | B | prey kid carries two backpacks behind cousin | prey kid tired, cousin smirk | - | medium, pan |
| 9 | B | crown mural on the wall | - | - | slow push |
| 10 | B | crown mural close | - | - | punch |
| 11 | B | Narrator shows "claw" | smirk | black claw | medium |
| 12 | B | Narrator hides marker behind back | smirk -> worried @0.8 | - | close |
| 13 | B (morning) | Narrator draws claw on wrist | neutral | drawing | close insert |
| 14 | B (dusk) | Narrator scrubs wrist at fountain | sad | - | medium |
| 15 | B (dusk) | Narrator looks at leaf | sad | leaf | close |
| 16 | B (rain on) | kids run for cover | shocked | - | wide |
| 17 | B rain | Kai arms crossed | smirk | claw | medium |
| 18 | B rain | Kai grabs Narrator's wrist | Narrator neutral -> shocked @0.4 | - | close |
| 19 | B rain | wrist: marker runs | - | streaks + leaf | close insert |
| 20 | B rain | Kai points | shocked -> smirk @0.6 | - | close |
| 21 | B rain | Kai talks to crowd | talk | - | medium |
| 22 | B rain | crowd surrounds Narrator | angry (crowd), worried (Narrator) | - | wide |
| 23 | B rain | 2-3 crowd kids point | angry | - | medium |
| 24 | B rain | one crowd kid shouts | angry -> talk @0.3 | - | close |
| 25 | B rain | Narrator holds wrist | worried | - | close |
| 26 | B rain | leaf glows brighter | - | leaf (brighter) | close insert |
| 27 | B rain | leaf splits with light (flash) | - | leaf -> crown @1.0 | close insert |
| 28 | B rain, warmer | crown glowing | - | crown | close insert |
| 29 | B | Kai lets go, steps back | shocked | claw | medium |
| 30 | B | crowd steps back | shocked | - | wide |
| 31 | B | small kid whispers | shocked -> talk @0.4 | - | close |
| 32 | B | Kai bows head | embarrassed | - | close |
| 33 | B | Kai looks up | worried -> talk @0.5 | - | close |
| 34 | B | prey kids by trash cans look up | sad -> smile @1.0 | leaves | medium |
| 35 | B | Narrator soft smile | smile | crown | close |
| 36 | B | Narrator determined | determined | crown | close, punch |
| 37 | B (sun out) | everyone eating together at one table | laugh | mixed | wide, pull-out |
