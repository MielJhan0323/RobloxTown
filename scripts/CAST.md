# Mindless Animations – Recurring Cast

One cast that shows up across all our stories, like a troupe of actors. Each story keeps its own
"In this town…" rule, but the same faces come back with the same personalities, so viewers recognise them.
Code name = the character model in `output/models/alpha-mark/` (use it in `S.char(...)`), mapped in `tools/anim/cast.py`.
Lineup picture: `python tools/animate.py cast-lineup 1 --stills` (or see the cast sheet sent in chat).

| # | Name | Model (code) | Look | Age | Personality | Signature line / habit |
|---|------|--------------|------|-----|-------------|------------------------|
| 1 | **Milo** | `Narrator` | messy brown hair, grey hoodie, blue jeans | 12 | Our narrator. Curious, overthinks everything, dry jokes in his head, brave only when someone he loves is in trouble. | Mom calls him "bug". Counts things when he's nervous. |
| 2 | **Rio** | `Crowd3` | blue hair, teal + orange tee | 12 | Milo's best friend. Fearless, laughs at danger, loyal to the end, terrible at plans. | "Okay but what if we just… did it?" |
| 3 | **Kai** | `Kai` (spiky black hair override) | spiky black hair, red tee, black pants | 13 | The rival. Competitive show-off, has to win everything, secretly soft and lonely. | Flexes before every challenge. |
| 4 | **Pip** | `Smallkid` | tiny, white hair, pink hoodie | 7 | Milo's little sister. Chaotic, brutally honest, always holding something weird (a snail, a spoon). Says the creepy thing out loud. | "I already knew that." |
| 5 | **Juno** | `Prey1` | long dark hair, yellow tee | 12 | The smart one. Notebook full of theories, skeptic, the one who explains the town's rules. | Draws diagrams of everything. |
| 6 | **Dev** | `Prey2` | purple hoodie, braids | 11 | The scaredy-cat comic relief. Always hungry, quotes rules, first to run, last to leave a friend. | "I'm not scared, I'm *strategically* leaving." |
| 7 | **Wren** | `Prey3` | white hair, white hoodie | 13 | The mystery kid. Quiet, knows things she shouldn't, never explains. **Easter egg: she appears in the background of EVERY episode** - viewers hunt for her in the comments. Her secret pays off in a later series. | Just… watches. Waves once. |
| 8 | **Ms. Odessa** | `Crowd2` | long black hair, orange jacket | adult | Teacher + town librarian. Knows the town's history and old rules; warm but cryptic. | "That rule is older than this town." |
| 9 | **Mom** | `Crowd1` | pink hair, white jacket | adult | Milo + Pip's mom. Works double shifts, huge hugs, worries quietly. | Calls Milo "bug". |
| 10 | **Dad** | `Cousin` (scale 1.18, hide "Sunglass" for close-ups) | blond hair, green tee | adult | Goofy dad jokes, always fixing something that isn't broken. | Calls Milo "champ" – never "kiddo" (The Knock twist). |
| 11 | **Mrs. Parker** | `Crowd4` (scale 1.18) | red hair, olive coat | adult | Neighbour across the street. Nosy, kind, gets her newspaper at 6:00 every morning and sees everything. | Appears with a newspaper. |

## Relationships
- Milo + Rio: best friends since kindergarten (bench, bikes, the hill).
- Milo vs Kai: rivals who respect each other; Kai becomes an ally when it counts.
- Milo + Pip: annoyed big brother / tiny sister who is always right.
- Juno + Dev: Juno plans, Dev panics; they're cousins.
- Wren: connected to everyone, explained to no one (series-long mystery).
- Mom, Dad, Mrs. Parker, Ms. Odessa: the adults who never quite believe the kids.

## Rules for using the cast
- Every story uses 2-4 of them; Milo narrates unless a story is told from someone else's POV (special episodes).
- Keep personalities consistent across stories - a "different town" is a different world, but the same people.
- Hide Wren somewhere in every episode (a background window, across the street, in a crowd).
- Past stories fit in: Rio (The Last Pickle, The Seat, Night Riders), Kai (The Last Pickle), Mom/Dad/Mrs. Parker (The Knock).
