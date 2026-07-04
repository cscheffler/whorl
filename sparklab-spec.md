# SparkLab — design spec

**SparkLab** (`sparklab.html`) is a self-contained, static HTML maths game for a
7½-year-old who has just completed **P2 in the Scottish Curriculum for
Excellence** (working within *First Level*). The goal: practice the mental
calculation skills of P2 to real fluency, and stretch into P3 — while making
learning feel *good*.

**Frame:** the player is an apprentice inventor in Professor Gizmo's wonderfully
chaotic invention workshop. Every correct answer generates **sparks** (energy).
Sparks power the lab's machines, and completed missions earn **blueprint
pieces** that build ridiculous inventions (a Bubble-Powered Jetpack, a
Sock-Finding Radar…). Maths *is* the power source of the lab.

- No server, no build step, no external assets. Open the file, play.
- All state in `localStorage`. Hostable on GitHub Pages as-is.
- Touch-first (tablet), fully usable with mouse + keyboard on desktop.

---

## 1. Curriculum map (what it teaches)

CfE First Level spans P2–P4. A child finishing P2 is typically secure on early
First Level; P3 consolidates and extends. Each **machine** in the lab trains one
skill strand, with levels running from "P2 secure" to "P3 stretch". Mental
calculation only — time-telling and shape are out of scope (see §9).

| Machine | Skill strand | Levels (→ = stretch toward P3) |
|---|---|---|
| **Power Cells** | Number bonds | 1: make 5 & 10 (ten-frame) · 2: make 10 fast · 3: make 20 · 4: make the next ten (47+□=50) → 5: make 100 with tens |
| **Rocket Fuel** | Addition | 1: within 10 · 2: within 20 · 3: bridging ten (8+7) · 4: 2-digit + 1-digit → 5: 2-digit + tens → 6: 2-digit + 2-digit |
| **Shrink Ray** | Subtraction | 1: within 10 · 2: within 20 · 3: bridging back (15−7) · 4: 2-digit − 1-digit → 5: 2-digit − tens → 6: find the difference (counting on) |
| **Cloning Chamber** | Doubles & halves | 1: doubles to 12 · 2: doubles to 20 & halves · 3: near-doubles (7+8 = 7+7+1) → 4: doubles/halves of tens (40+40, ½ of 60) |
| **Gear Works** | Skip counting & tables | 1: count in 2s/5s/10s · 2: backwards & odd starts · 3: 2× table · 4: 10× table · 5: 5× table → 6: sharing (÷ by 2, 5, 10 as "share among robots") |
| **Circuit Fixer** | Missing numbers | 1: □+a=b within 10 · 2: all forms within 20 · 3: fact families (3,7,10) → 4: balance both sides (3+□ = 6+2) → 5: missing numbers in tables |
| **Number Scanner** | Place value & number sense | 1: tens & ones · 2: +10/−10 from any number · 3: which is bigger · 4: order three numbers → 5: odd/even rapid sorter |

Question generators produce plausible **distractors** (off-by-one, off-by-ten,
operation confusion), never duplicated, never negative.

**Mix Lab — the Daily Experiment.** A 12-question mission interleaving *all*
unlocked levels across machines, weighted toward the player's weak facts.
Playing on consecutive days grows a "lab log" streak. This is the spaced,
interleaved practice that turns skills into fluency.

---

## 2. Fluency model (how it adapts)

- **Per-fact stats.** Every atomic fact (e.g. `add:7+8`) tracks attempts,
  correct count, an EWMA of response time, and last-seen time.
- **Weakness-weighted selection.** ~60% of questions are drawn with weight
  toward weak (low accuracy), slow (high EWMA), or stale (not seen recently)
  facts; ~40% uniformly from the level pool. Deliberate practice targets the
  edge of competence, not comfort.
- **Missed questions re-queue** 2–3 questions later in the same mission —
  retrieval shortly after corrective feedback.
- **Levels unlock** at ≥2 stars on the previous level. Stars per mission:
  ⭐ ≥60% first-try correct · ⭐⭐ ≥80% · ⭐⭐⭐ ≥90% **and** median response
  under the level's target time. Speed is rewarded, never punished: fast
  answers earn a "Quick spark!" bonus; slow answers are simply correct.
  (Mental-maths anxiety is real; there is no countdown-doom bar. The timer UI
  is a *charging capacitor* that fills toward bonus.)
- **Scaffolding fades.** Early levels always show the visual model
  (ten-frame etc.) and use multiple choice; higher levels hide the model
  behind a **Hint** button (it also appears after a wrong answer) and switch
  to **keypad entry** (the generation effect: recalling beats recognising).

---

## 3. Reward loop

- **Sparks:** +10 per correct, +5 quick bonus, streak multiplier at 3+ and 5+
  in a row (with escalating chime pitch and flame meter).
- **Blueprints:** each mission awards blueprint pieces toward the invention
  currently "on the workbench" (4–6 pieces each). Completed inventions join
  the **Hall of Inventions** — an animated gallery of silly gadgets with
  flavour text. Ten inventions form the long-term goal arc.
- **Titles:** total sparks promote the player: Trainee → Junior Inventor →
  Inventor → Senior Inventor → Chief Inventor → Mad Genius.
- **Praise targets effort and strategy,** never innate ability ("Your brain
  got stronger!", "You used doubles — clever!"), per growth-mindset findings.
- A wrong answer always shows the correct answer **with the visual model**
  (see it, not just read it), costs nothing but the star count, and re-queues.

### 3b. Invention mini-games (the arcade layer)

Every **built invention unlocks a mini-game** played from its Hall card — a
real arcade reward whose mechanics come from the invention itself. Numeracy is
woven in but deliberately downplayed; these are the treat, not the lesson. All
are replayable with a saved best score (`S.arcade`), keyboard + touch input,
and share one arcade framework (canvas/DOM stage, rAF loop, intro/end
overlays).

| Invention | Mini-game | Mechanic | Hidden numeracy |
|---|---|---|---|
| Bubble Jetpack | **Bubble Flight** | hold-to-thrust flappy dodge | numbered bubbles score their value |
| Sock Radar | **Sock Hunt** | grid deduction: pings show step-distance | Manhattan distance reasoning |
| Cat Translator | **Cat Chat** | Simon-style growing miaow sequence | sequence memory/length |
| Jelly Trampoline | **Jelly Bounce** | paddle-catch, springy sweet spot, stars | tallying, trajectory sense |
| Rocket Skates | **Skate Dash** | two-lane runner, dodge crates | boost gates: pick the **bigger** number |
| Robo-Dog | **Fetch!** | catapult drag-to-throw, dog retrieves | land near a number-line target (estimation) |
| Weather-in-a-Jar | **Storm Catcher** | catch rain, dodge lightning | fill the beaker to the 20 line (1/2/5 drops) |
| Shrink-Ray | **Shrink Zap** | reaction zapper, rule changes each wave | odd/even, >/<, counting-in-2s/5s/10s |
| Moon Piano | **Moon Melody** | falling-note rhythm game, real synth tune | beat timing/counting |
| Alarm Clock | **Time Warp** | stop the fast-spinning hand on the target | o'clock & half-past reading |

**The Impossible Challenge** (finale): revealed in the Hall only when **all 10
inventions are built AND every level of every machine has ≥1 star** (the
Daily Experiment doesn't count). A boss fight against the haywire
*Impossibility Engine*: questions drawn from the **top level of every
machine**, a burning fuse per question (12s, shrinking as you land hits),
critical double-damage for fast answers, streak bonuses, 3 power cores; 21
hits wins. Replayable for best score — the fuse maths makes repeat wins
progressively harder.

---

## 4. Principle mappings

### Mayer multimedia principles → concrete features
| Principle | Where it shows up |
|---|---|
| Multimedia (words + pictures) | Every question pairs symbols with a visual model: ten-frames, number lines with hop animation, base-10 rods, gear arrays, balance scales |
| Modality (narrate, don't caption) | Optional speech narration (SpeechSynthesis, en-GB) reads questions and Professor Gizmo's lines aloud — big help at age 7½ reading level |
| Coherence (cut extraneous load) | The question card is clean and quiet; theming lives in the frame, rewards and transitions, never inside the problem space |
| Signaling | The numbers being operated on pulse/highlight in the model as the question is read |
| Segmenting | Short 10-question missions; one skill per machine; learner-paced intros |
| Pre-training | Each machine's first visit runs a short animated "How it works" demo of its visual model before questions start (skippable, replayable) |
| Personalization | Conversational, first-person Professor Gizmo ("Let's charge this thing up!"), player's name used |
| Temporal/spatial contiguity | Feedback lands directly on the answer just given, at the moment it's given |

### Nielsen heuristics → concrete features
| Heuristic | Where it shows up |
|---|---|
| Visibility of status | Question progress pips, spark meter, streak flames, level stars on every machine door |
| Match to real world | Kid language, concrete objects (batteries, gears, robots), UK conventions |
| User control & freedom | Exit/pause any time without losing sparks earned; skip intros; replay any level |
| Consistency | Every machine uses the same mission layout, same button grammar, same feedback choreography |
| Error prevention | Huge touch targets (≥60px), generous spacing, keypad ignores impossible input (leading zeros, >3 digits), destructive reset is double-confirmed and buried in the grown-ups screen |
| Recognition over recall | All options visible; icons + labels everywhere; no hidden gestures |
| Flexibility & efficiency | Keyboard digits/Enter work on desktop; MCQ hotkeys 1–4; narration repeat button |
| Aesthetic & minimalist | One question at a time, one action asked of the player |
| Error recovery | Wrong answer → gentle sound, correct answer shown with the model, then a retry of the same fact later |
| Help | Hint button on every question; Professor Gizmo demos on demand |

### Kosslyn science-of-learning principles → concrete features
| Principle | Where it shows up |
|---|---|
| Deep processing / generation | Typed answers (not recognition) at higher levels; fact-family and balance formats force relational thinking |
| Deliberate practice | Weakness-weighted question selection; immediate, informative feedback |
| Dual coding | Symbolic + visual model on every question; correct-answer replay shows the model |
| Chunking | Strategies taught as chunks: bridge-through-ten, near-doubles, make-the-next-ten |
| Spaced practice | Daily Experiment + staleness term in fact weighting + lab-log day streak |
| Interleaving | Mix Lab interleaves all unlocked skills; within-machine missions mix formats (a+□, □−a) |
| Desirable difficulty | Adaptive levels; 40% of questions from the full pool keeps retrieval effortful |
| Immediate feedback | Sub-second, on-the-spot, always explanatory on errors |
| Motivation & growth mindset | Effort-praise copy, visible progress (stars/blueprints/titles), no fail states |

---

## 5. Look, feel & sound

**Aesthetic:** "midnight workshop" — a deep indigo lab where everything the
player touches glows. Neon spark-yellow, electric cyan, coral and lime against
navy; chunky rounded cards with thick borders; slow-turning background gears
and drifting spark motes (both disabled under reduced motion). Rounded
kid-friendly type via the `ui-rounded` system stack (no external fonts — the
file must stay self-contained); display text gets its personality from weight,
tilt and glow, not from a webfont.

**Audio (Web Audio API, all synthesised — no samples):**
- Correct: bright major-arpeggio ding that rises in pitch as the streak grows.
- Quick-bonus: extra "zap". Wrong: soft, low, kind thud (never a buzzer).
- Mission complete: little fanfare + spark shower. UI taps: tiny clicks.
- Mute toggle persisted; AudioContext only created after first user gesture
  (autoplay policy); everything degrades silently if unavailable.

**Narration (SpeechSynthesis):** optional, on by default; reads questions and
feedback lines. Voices are ranked: Chrome's remote "Google UK English" voices
first (they're markedly better), then premium/enhanced `en-GB` system voices,
then any `en-GB`, then any English. If a remote voice fails (offline), it
demotes itself to the best local voice and retries once. Repeat button on the
question card. Degrades silently when no voices exist (e.g. headless runs).

**Accessibility:** honours `prefers-reduced-motion` (particles, shakes and gear
spins off); WCAG-AA text contrast on all surfaces; touch targets ≥60px; fully
keyboard playable; narration doubles as reading support.

---

## 6. Screens

1. **Title** — logo, Professor Gizmo, Play. First run: pick a robot buddy +
   optional name (defaults to "Inventor").
2. **Lab map (home)** — the workshop: 7 machine doors (each shows its star
   progress), Mix Lab door, Hall of Inventions, grown-ups corner, settings
   (sound/narration), spark total + title, daily streak chip.
3. **Machine intro** — Professor Gizmo pre-trains the visual model
   (animated, narrated, skippable).
4. **Mission** — progress pips · streak flames · spark counter; question card
   with visual model; MCQ bubbles *or* keypad; hint; pause/exit.
5. **Results** — stars with fanfare, sparks tally, quick-answer count,
   blueprint piece slotting into the current invention, effort-praise line,
   then: Play again / Next level / Back to lab.
6. **Hall of Inventions** — gallery; built gadgets animate and carry their
   mini-game's Play button + best score; the one on the workbench shows
   collected pieces; The Impossible Challenge card sits at the end (locked:
   progress toward the gate; unlocked: glowing).
6b. **Arcade** — shared mini-game screen: title bar with score/status chips,
   canvas + DOM stage, how-to-play intro overlay (narrated), end overlay with
   score, best and replay.
7. **Grown-ups corner** (hold-to-open gear) — progress dashboard: per-machine
   star ladders, per-fact fluency heatmap (sequential single-hue ramp),
   accuracy & speed stat tiles, total practice time. Also home to
   **Save / Load progress** — exports the whole save as a JSON file and
   imports it (validated, confirm-before-overwrite), so progress can be backed
   up or moved to another browser/device — and the (double-confirmed) full
   reset.

---

## 7. Architecture & state

One file, `sparklab.html`: CSS → HTML screens + inline SVG art → JS in
labelled sections: utils/PRNG · state · audio synth · speech · curriculum +
question generators · fact model · mission engine · visual-model renderers
(SVG) · screen router · FX (canvas particles) · dashboard · `window.UI` hook.

`localStorage` key **`sparklab.v1`** (schema versioned for migration):

```json
{ "version": 1,
  "profile":  { "name": "…", "avatar": 0 },
  "settings": { "sound": true, "narration": true },
  "sparks": 0,
  "machines": { "power": { "level": 1, "stars": {"1": 2} } },
  "facts":    { "add:7+8": { "n": 4, "ok": 3, "ewmaMs": 4200, "last": 0 } },
  "inventions": { "built": [], "current": 0, "pieces": 2 },
  "daily":    { "last": "2026-07-03", "streak": 3 },
  "totals":   { "answered": 0, "correct": 0, "timeMs": 0 } }
```

---

## 8. Test hook & testing plan

`window.UI`, in the house style (see TESTING.md), drives everything the
harness needs without pixel-perfect gestures:

```js
UI.seed(42);                 // deterministic PRNG for reproducible questions
UI.fx(false);                // kill animations/sound/narration for stable shots
UI.reset();                  // wipe save + back to a fresh first-run state
UI.go('home'|'hall'|'progress'|'title');
UI.start('rocket', 3);       // jump straight into a mission
UI.question();               // {text, answer, options?, mode}
UI.answer(15);               // submit programmatically (right or wrong)
UI.state();                  // {screen, sparks, mission:{i,n,correct,streak}, …}
UI.grant({sparks:500, inventions:3}); // fixture for hall/dashboard shots
UI.export();                 // progress-file JSON (the Save button's payload)
UI.import(jsonOrObject);     // apply a progress file (the Load button's action)
UI.play('jetpack');          // open a mini-game; UI.beginGame() presses Play
UI.arcade();                 // {id, running, done, score}
UI.endGame(n);               // force game-over; UI.grant({allLevels:true}) for the finale gate
```

Harness recipes (all must run with a clean console / no `pageerror`):

```sh
# Lab map, fresh profile
venv/bin/python tools/shoot.py --url sparklab.html --gesture none \
  --setup "UI.reset(); UI.fx(false); UI.go('home')" --out tools/shots/s_home.png

# Mid-mission with a streak going (answer 4 right, seed fixed)
venv/bin/python tools/shoot.py --url sparklab.html --gesture none \
  --setup "UI.reset(); UI.fx(false); UI.seed(1); UI.start('rocket',3);
           (async()=>{for(let i=0;i<4;i++){UI.answer(UI.question().answer);
           await new Promise(r=>setTimeout(r,120));}})()" \
  --out tools/shots/s_mission.png
```

Assertions beyond screenshots: `UI.state()` after scripted answer runs
(scoring, streaks, star maths, level unlocks, requeue-on-miss), localStorage
round-trip, `--touch` + phone viewport for layout, keypad input rules.
Narration/audio verified to **degrade gracefully** headless, like Whorl's mic.

---

## 9. Decisions & assumptions (flag if wrong)

- **Mental calculation only** — no clocks/shape/measure modules (P2/P3 money
  *is* mostly coin arithmetic; a Lab Shop money machine is the top future
  candidate, §10).
- **UK/Scottish conventions**, British English throughout.
- **Touch-first** for tablet use; desktop keyboard fully supported.
- **No external fonts/CDNs** — self-containment beats typographic flair.
- **Speed pressure is bonus-shaped, not failure-shaped** (see §2).
- Sound and narration **on by default**, one-tap mutable, persisted.

## 10. Future ideas (out of scope now)

Lab Shop (money machine: make amounts with coins, give change) · two-player
"lab race" on one screen · printable certificate when all inventions are
built · per-fact spaced-repetition scheduling across days (full SM-2-lite) ·
fractions machine for later P3 (½, ¼ of amounts).
