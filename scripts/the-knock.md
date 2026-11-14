# The Knock (Part 1)

Rule: In this town, when the streetlights go out, you never open the door.
Music: Numbers (low, slowed) - spooky
Voice: user supplies the narration (Titan, eleven_v4, prompt below). Do NOT generate voice unless the user says so.

Format: kid-safe horror cliffhanger. Part 1 ends on a choice (front door or back door); viewers vote in the comments.
Part 2 follows the winning pick: the right door saves him, the wrong door is "the end" (he is simply gone - the screen
goes dark, nothing gory). Clues are planted so the choice is fair: Knockers copy voices, but only words they heard today.

## Narration

In this town, when the streetlights go out, you never open the door.

That's when the Knockers come. They sound like people you love. Last year, one knocked on the Parkers' door using their grandma's voice. Their grandma lives in Florida.

The rules are simple. Lock everything. Don't answer. Knockers can copy any voice, but only words they heard today.

Tonight, Mom and Dad went out for dinner. "Back before the lights go out," Mom said. She kissed my head and called me "bug," like she does every night. We were on the front porch.

At nine, the streetlights went out. They weren't home.

At nine-oh-one, someone knocked on the front door.

"Bug? It's Mom. I lost my keys. Open up, it's freezing."

Then, a knock on the back door. Softer.

"Hey, kiddo. It's Dad. Mom's with me. Don't open the front. Something followed us."

Dad never calls me kiddo.

But Mom said "bug" on the porch, where anything could have heard it.

The front door rattled. The back door went quiet. Too quiet.

My phone has two percent battery. I can reach one door before it dies.

Front door, or back door?

## Shot list

Animated in Blender (tools/anim/stories/the_knock.py): street at night, front porch, dark hallway with the
front door (left) and back door (right). Knocker = tall shadow with glowing eyes, never shown up close.

| # | Narration | Sec |
|---|---|---|
| 1 | In this town, when the streetlights go out, | 1.8 |
| 2 | you never open the door. | 1.8 |
| 3 | That's when the Knockers come. | 1.8 |
| 4 | They sound like people you love. | 1.8 |
| 5 | Last year, one knocked on the Parkers' door using their grandma's voice. | 1.8 |
| 6 | Their grandma lives in Florida. | 1.8 |
| 7 | The rules are simple. Lock everything. | 1.8 |
| 8 | Don't answer. | 1.8 |
| 9 | Knockers can copy any voice, but only words they heard today. | 1.8 |
| 10 | Tonight, Mom and Dad went out for dinner. | 1.8 |
| 11 | "Back before the lights go out," Mom said. | 1.8 |
| 12 | She kissed my head and called me "bug," like she does every night. | 1.8 |
| 13 | We were on the front porch. | 1.8 |
| 14 | At nine, the streetlights went out. | 1.8 |
| 15 | They weren't home. | 1.8 |
| 16 | At nine-oh-one, someone knocked on the front door. | 1.8 |
| 17 | "Bug? It's Mom. I lost my keys. Open up, it's freezing." | 1.8 |
| 18 | Then, a knock on the back door. Softer. | 1.8 |
| 19 | "Hey, kiddo. It's Dad. Mom's with me. Don't open the front. Something followed us." | 1.8 |
| 20 | Dad never calls me kiddo. | 1.8 |
| 21 | But Mom said "bug" on the porch, where anything could have heard it. | 1.8 |
| 22 | The front door rattled. | 1.8 |
| 23 | The back door went quiet. Too quiet. | 1.8 |
| 24 | My phone has two percent battery. | 1.8 |
| 25 | I can reach one door before it dies. | 1.8 |
| 26 | Front door, or back door? | 1.8 |

## Delivery

| Line | Tone |
|---|---|
| In this town, when the streetlights go out, you never open the door. | whisper |
| That's when the Knockers come. ... lives in Florida. | dramatic -> funny |
| The rules are simple. ... only words they heard today. | soft |
| Tonight, Mom and Dad went out ... front porch. | warm |
| At nine, the streetlights went out. They weren't home. | dramatic |
| At nine-oh-one, someone knocked on the front door. | whisper |
| "Bug? It's Mom. ..." | warm (too sweet) |
| Then, a knock on the back door. Softer. | whisper |
| "Hey, kiddo. It's Dad. ..." | whisper (urgent) |
| Dad never calls me kiddo. | dramatic |
| But Mom said "bug" on the porch, where anything could have heard it. | whisper |
| The front door rattled. The back door went quiet. Too quiet. | dramatic |
| My phone has two percent battery. ... | soft |
| Front door, or back door? | whisper |

## ElevenLabs prompt

```
[whispering] In this town, when the streetlights go out, you never open the door.

[dramatically] That's when the Knockers come. They sound like people you love. Last year, one knocked on the Parkers' door using their grandma's voice. [laughs softly] Their grandma lives in Florida.

[softly] The rules are simple. Lock everything. Don't answer. Knockers can copy any voice, but only words they heard today.

[warmly] Tonight, Mom and Dad went out for dinner. "Back before the lights go out," Mom said. She kissed my head and called me "bug," like she does every night. We were on the front porch.

[dramatically] At nine, the streetlights went out. They weren't home.

[whispering] At nine-oh-one, someone knocked on the front door.

[warmly] "Bug? It's Mom. I lost my keys. Open up, it's freezing."

[whispering] Then, a knock on the back door. Softer.

[whispering] "Hey, kiddo. It's Dad. Mom's with me. Don't open the front. Something followed us."

[dramatically] Dad never calls me kiddo.

[whispering] But Mom said "bug" on the porch, where anything could have heard it.

[dramatically] The front door rattled. The back door went quiet. Too quiet.

[softly] My phone has two percent battery. I can reach one door before it dies.

[whispering] Front door, or back door?
```
