# alpha-mark - scene setup for laptop Claude

Read with `scripts/alpha-mark.md` and `tools/laptop/RECORDING.md`. Helpers: `tools/laptop/StoryKit.lua`.

## Sets - 3 total: 2 REUSED from workspace.Town.Sets + 1 new (mountain trail, reusable for future trips)

| Set | Reuse | Add | Shots |
|---|---|---|---|
| **A. Town street** | existing street | morning light, kids with backpacks | 1-4 |
| **B. School playground** | existing playground | a school wall with a faded **crown mural**, 2 long lunch tables + trays, 2 trash cans, a bench, a drinking fountain, a **rain** effect you can switch on/off (ParticleEmitter or Toolbox rain) | 5-32 |
| **C. Mountain trail (NEW)** | build once, save to Town.Sets | dirt trail along a slope, a cliff edge with a hanging root, a parked school bus, loose boulders that can tumble (unanchor or tween them down for shot 35), dust particles | 33-45 |

Lighting presets: `warm` (1-13, 28-33), `night`/dusk (14-15), `sad` grey + rain (16-27), mountain `sad`/dusty (34-41), `warm` sunset (42-45).

## Cast - every character UNIQUE, with REAL hair (catalog hair accessories/meshes, never block hair)

No two characters may share the same hair style, hair color, skin tone AND outfit. Before exporting, line
them up side by side, take ONE screenshot and check they're all easy to tell apart.

| Character | Hair (real catalog hair) | Skin | Outfit | Build |
|---|---|---|---|---|
| **Narrator** | messy brown hair, swoopy fringe | light | grey hoodie, blue jeans | average kid |
| **Kai** (bully) | spiky black hair | medium-brown | red varsity jacket, black pants | tallest kid |
| **Cousin** | blond slicked-back hair | light-tan | green polo, khaki shorts, sunglasses on head | average |
| Prey kid 1 | curly red hair | light, freckles | yellow t-shirt, overalls | small |
| Prey kid 2 | long black braids | dark | purple dress / hoodie | small |
| Prey kid 3 | short white/silver bowl cut | medium | striped shirt, glasses | small |
| Crowd kid 1 | pink ponytail | light | white jacket | average |
| Crowd kid 2 | brown afro / curls | dark | orange hoodie | average |
| Crowd kid 3 | blue spiky hair | medium | sports jersey | average |
| Crowd kid 4 | ginger buzz cut + cap | light | camo jacket | average |
| Small kid | two blonde pigtails | tan | pink raincoat | smallest |

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
| 32 | B (sunny) | kids bow/cheer around Narrator | kids laugh, Narrator embarrassed | crown | medium |
| 33 | C | class hikes up the trail, bus parked | smile | - | wide |
| 34 | C | class stops, ground shakes (camera shake) | smile -> shocked @0.4 | - | medium |
| 35 | C | boulders tumble down the slope, dust | - | - | wide |
| 36 | C | kids run past, Kai frozen | crowd shocked, Kai worried | - | medium, pan |
| 37 | C | Kai slips off the edge | shocked | claw | medium, punch |
| 38 | C | Kai's hand grips a root | - | claw | close insert |
| 39 | C | Narrator raises blazing crown wrist | determined | crown (brightest) | close insert |
| 40 | C | Narrator flat on the ground, grabs Kai's wrist | Narrator determined, Kai crying | crown + claw both visible | close |
| 41 | C | Narrator pulls | determined | - | close, punch |
| 42 | C | Kai sits safe on the trail, shaking | crying | - | close |
| 43 | C | Kai looks up | sad -> talk @0.4 | - | close |
| 44 | C | Narrator offers a hand | smile | crown | close |
| 45 | C (sunset) | Narrator helps Kai up, class gathers | smile / laugh | - | wide, pull-out |
