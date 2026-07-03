# Visual testing harness

This app is a browser-based **Canvas 2D** toy with **no server** — it opens by
double-clicking `whorl.html` (`file://`). Because the visuals only appear in
response to pointer input and a `requestAnimationFrame` loop, testing means
*driving input* in a real headless browser, then capturing and inspecting the
rendered pixels.

The harness lets a developer (or an AI agent) "see" the output: it scripts a
drag gesture, lets the animation settle, and writes a PNG screenshot.

## Setup (one time)

Uses the Python venv in `venv/`:

```sh
venv/bin/pip install playwright Pillow
venv/bin/playwright install chromium
```

- **Playwright** — drives a headless Chromium: loads the page, dispatches pointer
  events, takes screenshots.
- **Pillow** — programmatic pixel checks (e.g. brightness centroid for centering),
  so results can be *asserted*, not just eyeballed.

## Usage

```sh
venv/bin/python tools/shoot.py --url whorl.html --out tools/shots/default.png
```

The screenshot lands in `tools/shots/` (gitignored). Open it, or read it with an
image-capable tool.

### Options

| Flag | Default | Purpose |
|---|---|---|
| `--url` | *(required)* | HTML file path or URL (path is auto-resolved to `file://`) |
| `--out` | `tools/shots/out.png` | Output PNG path |
| `--gesture` | `spiral` | Drag path: `spiral`, `arc`, `line`, `scribble`, or `none` |
| `--width` / `--height` | `900` / `700` | Viewport size (CSS px) |
| `--dpr` | `2.0` | `devicePixelRatio` — exercises the retina/phone scaling path |
| `--touch` | off | Emulate a touch device (tests touch input + `touch-action:none`) |
| `--step-ms` | `6` | Pause between pointer-move steps (varies pointer speed → velocity-driven width) |
| `--settle` | `600` | ms to wait after the gesture before screenshotting |
| `--setup` | — | JS string evaluated before the gesture (e.g. to set controls) |

### Examples

```sh
# Snowflake look, 8-fold, on an emulated phone with touch input
venv/bin/python tools/shoot.py --url whorl.html --touch \
  --setup "UI.set({folds:8, mirror:true})" \
  --gesture spiral --out tools/shots/snowflake.png

# A single sweeping arc, no symmetry tweaks
venv/bin/python tools/shoot.py --url whorl.html --gesture arc \
  --out tools/shots/arc.png
```

> The `--setup` JS is app-specific and only matters once the app exposes a hook
> (e.g. a global like `UI.set(...)`). Gestures and screenshots work on any canvas
> regardless.

## What the harness verifies

- Captures `console` and uncaught `pageerror` output, so JS exceptions surface in
  the run output instead of failing silently.
- Supports a screenshot **matrix** for the acceptance checklist: pinwheel vs.
  snowflake (mirror toggle), fold counts, all color modes, persistent vs. fading,
  touch vs. mouse, retina scaling.
- Pillow enables quantitative assertions — e.g. confirming the figure is centered
  via brightness centroid, or checking N-fold symmetry.

Audio-reactive mode can only be verified to **degrade gracefully** here (headless
has no microphone) — which is exactly its specified fallback behavior.

## Testing Escher

`escher.html` (the isometric ribbon toy) uses the same harness. Because its
geometry is axis-snapped beams, the most reliable tests **build figures through
the `UI` hook** (deterministic world coords) rather than relying on pixel-perfect
drags, and use a couple of real drags to prove the pointer→snap pipeline.

Escher's `window.UI` hook adds, beyond `set/get/clear/count`:

- `UI.path([{axis:'x',len:4},{axis:'y',len:3}, …])` — build a figure from
  world-axis steps (`len` may be negative). Returns the segment count.
- `UI.moveTo({x,y,z})` — lift the pen and reposition the head, so a test can lay
  down two **deliberately-crossing** strokes (e.g. a ground beam plus an elevated
  overpass).
- `UI.tapAt(sx, sy)` — flip the over/under at a screen point; returns `true` if a
  crossing was hit.
- `UI.flips()` — flipped crossings as `[segIdxA, segIdxB]` pairs (a flip is a
  *per-crossing* override, not a per-beam state).
- `UI.segments()` — draw order plus each beam's projected endpoints/midpoint
  (`ax,ay` / `bx,by` / `sx,sy`), for assertions.
- `UI.head()` — the current ribbon tip (world + projected `sx,sy`), or `null` when
  empty. Useful for testing continue-vs-new-path.
- `UI.joints()` — number of mitered corner cubes. Useful for the turn-debounce
  test below (a clean straight drag should leave this at 0).
- `UI.project({x,y,z})` — world→screen, handy for computing where to tap.

**Continue-vs-new-path:** a drag that begins within ~1.1 world units of the last
tip continues the ribbon (the next beam's start `ax,ay` equals the old
`UI.head()`); a drag that begins farther away starts a new path at the press
point. The choice is made on first movement, so a tap (no drag) never moves the
pen. Drive two real drags with Playwright's `mouse.down()/move()/up()` to verify
both branches.

**Turn debounce (no stray end-block):** a direction change only commits a corner
once it accumulates `MIN_TURN_UNITS` (~0.45 world units) of off-axis travel, so a
small finger-lift wobble can't drop a stray joint cube + stub at the end of a
ribbon. To test: drive a clean straight drag, then append a few small perpendicular
move points just before `mouse.up()`. A correct result is `UI.count() == 1` and
`UI.joints() == 0`. Guard against over-correcting by also asserting a *deliberate*
L-shaped drag still turns (`UI.count() >= 2`, `UI.joints() >= 1`). Both branches
must run clean of `console`/`pageerror` output. (These are real-input checks, so
use a direct Playwright `mouse` script rather than `shoot.py`'s canned gestures.)

**Corners must read as one continuous solid.** A corner is a cube where two
consecutive beams meet. To keep it continuous the renderer (a) skips the beam end
caps that meet the cube, (b) **trims** each connected beam end back by half a
cube-width so the beam *abuts* the cube instead of overlapping it, (c) strokes
every face in its own fill colour, and (d) **inflates** each face ~0.6px toward its
own corners so abutting *same-shade* faces overlap rather than leaving a thin
anti-aliased seam (this is what removed the faint hairline at a corner apex where
the cube top met the beam tops). The trim matters because faces are depth-sorted by
their **centroid**: an
overlapping beam side-face (centroid at the beam's middle) can otherwise sort over
the cube and poke a wrong-shade quad into the corner — and because the sort
depends on absolute position, the *same* drawing motion can break *differently* at
different spots. The canonical regression: build two identical corner ribbons at
different positions via `UI.path` + `UI.moveTo` (e.g. `[{axis:'y',len:-4},
{axis:'x',len:4}]` twice) and confirm the two corners render the same — a quick
check is that a sampled patch at each corner has the same dominant colours.

**A corner is not a crossing.** `UI.tapAt` only flips when two *overlapping but
unconnected* beams are hit; two beams that share a vertex (a corner) are left
stable. Test: `UI.path([{axis:'x',len:4},{axis:'y',len:3}])`, then `UI.tapAt` on
the corner — it must return `false` and leave `UI.flips()` empty.

**A flip is LOCAL to its crossing.** This is the important one. A flip is *not* a
per-beam state — flipping it must not change anything except that one crossing
(an earlier per-beam `raised`+depth-bias also flipped every corner that beam
formed). Implementation: **a single render pass** with a flip-aware face
comparator (`faceCompare`). Faces normally sort far-to-near by depth, but for the
two beams of a flipped crossing the comparator reverses their relative order.
Because two straight beams overlap *only* at their crossing, reversing their order
changes only that crossing — corner cubes (`beam == null`, ordered purely by
depth) and every other crossing are untouched. There is **no second pass / clip**,
so no anti-aliased redraw seam (an earlier clip-and-redraw approach left a faint
hairline at flipped junctions — see the hairline note below).

Over/under (which beam draws on top) uses `depth, then segIdx`: the main sort is
*stable*, so equal-depth beams (very common on symmetric loop crossings) are
ordered by push order (`segIdx`). A plain `>=` tie-break picks the already-on-top
beam and the flip is a visible no-op. Regression: two equal-depth crossing beams
(coincident centroids) must still flip visibly.

Impossible *cycles* (A over B over C over A) have no valid total order; the
comparator is then non-transitive and the sort degrades gracefully (one crossing
won't flip) but must never throw — assert no `pageerror` after flipping all
crossings of three mutually-crossing beams.

Definitive regression: build a shape where a crossing is **far from any corner**
(e.g. a big square body whose edge an elevated tail crosses at mid-span), sample
canvas pixels (`getImageData`) at the crossing *and* at each corner, `UI.tapAt`
the crossing, and assert the crossing changed while **every corner pixel is
unchanged** (Δ ≈ 0). Also assert **toggle identity**: two taps leave the canvas
pixel-identical and `UI.flips()` empty. Cover elevated/flat crossings, equal-depth
crossings, a beam crossing two others, and connected self-crossing ribbons.
(Note: for *small* test shapes the crossing fills much of the frame, so a
"changed-pixel bounding box" check yields false negatives — sample specific corner
pixels instead.)

**No hairline at flipped junctions.** Because flips are now done in the single
sort pass (not a clipped redraw over the finished frame), a flipped crossing must
render pixel-clean — identical quality to an un-flipped one. Regression: zoom a
flipped junction and confirm there's no faint seam line through the on-top beam;
equivalently, a flipped crossing should match the *same* crossing built naturally
in the opposite draw order.

**Magnetic loop closure (preview until release).** Mid-drag, once the head has
*left* the start by `DEPART_UNITS` (~1.7) and then returns within `MAGNET_UNITS`
(~1.0), a clean closure is **previewed** (a ring at the start hints as you
approach). The preview is **non-destructive**: `UI.count()` stays at the open
count while previewing; only **release inside the zone commits** it. Pull back out
of the zone and the preview vanishes and drawing continues. It **arms** as soon as
the head leaves the start by `DEPART_UNITS` — *independent of segment count* (an
earlier bug gated arming behind ≥3 beams, so small/unequal squares whose 3rd
corner was already inside `DEPART` never armed and silently fell back to
`closeIfNear`). The *snap* still requires ≥3 beams, so it won't close on launch or
short strokes. Use `UI.closing()` to assert whether a preview is active. The
plan adjusts the last two perpendicular beams so the head lands exactly on the
tail with a square corner — i.e. the **beam before the current one shifts** to make
the ends meet (`planClosure`/`commitClosure`); it falls back to `closeIfNear` when
the last corner isn't a clean perpendicular near-close.

This is a **real-input** behaviour. To test, drive a Playwright `mouse` drag of
three sides plus a fourth heading back into the zone, and:
- *preview is non-destructive* — screenshot before `mouse.up()` shows a closed
  loop while `UI.count()` is still the open count (3);
- *release commits* — after `mouse.up()`, `UI.count()` is the closed count and
  `UI.head()`'s projected `sx,sy` equals the start press point;
- *pull-away* — entering then leaving the zone before release must leave the path
  open (head not at the start).

Note `pathStart` is `groundUnproject(pressPoint)`, **not** world-origin, so compare
the snapped head to the start *screen* point, not to `(0,0,0)`.

**Corner hue continuity.** With hue drift on, a corner cube must take a hue
*between* its two beams (it links them via `b1`/`b2`); the start↔end closing corner
keeps a single intended discontinuity. Regression: `UI.set({drift:1})` + a closed
`UI.path` loop — every corner except the closing one should transition smoothly
(sample patches on either side of an interior corner should be close in hue).

**Mid-drag corner rendering.** A corner cube's `b2` is the *live `curBeam`* until
that beam commits, and a live beam has no `segIdx` yet — so the colour math must
not go `NaN` (it did once: `drift * undefined` → `NaN` → `hsl(NaN,…)` → the fill
silently fails and the cube renders as a hollow outline above the apex). Test this
**while still drawing**: draw one beam, turn, drag the second beam only partway,
and screenshot *before* `mouse.up()` (count is 1 — beam 1 committed, beam 2 live).
The in-progress corner must render filled, identical to the committed corner. Do
this for corners turning in each direction (the two ground axes × both signs).

New harness flags/gestures for Escher:

- `--gesture iso-l` / `iso-stairs` — real off-axis drags that should snap to clean
  iso beams (exercises the snapping pipeline).
- `--tap "X,Y"` (repeatable) — a down/up with no move at screen `X,Y`, to drive a
  crossing flip via real input.

Example checks (all assert no `console`/`pageerror` output):

```sh
# A single beam shows three flat face shades (top/mid/dark)
venv/bin/python tools/shoot.py --url escher.html --gesture none \
  --setup "UI.clear(); UI.path([{axis:'x',len:5}])" --out tools/shots/e_beam.png

# Crossing depth-sort vs. impossible flip (same figure, with/without a tap)
venv/bin/python tools/shoot.py --url escher.html --gesture none \
  --setup "UI.clear(); UI.path([{axis:'x',len:8}]); UI.moveTo({x:4,y:-4,z:1.4}); UI.path([{axis:'y',len:8}])" \
  --out tools/shots/e_cross.png
venv/bin/python tools/shoot.py --url escher.html --gesture none \
  --setup "UI.clear(); UI.path([{axis:'x',len:8}]); UI.moveTo({x:4,y:-4,z:1.4}); UI.path([{axis:'y',len:8}])" \
  --tap "582,426" --out tools/shots/e_flip.png
```

> **Gotcha — where the crossing actually is:** an elevated beam shifts *up* on
> screen by `S·z`, so the visual crossing is **not** the projection of the world
> intersection point. Intersect the two beams' projected center-lines (or eyeball
> the screenshot) to find the tap target.

Pillow assertions used during bring-up: count distinct bright face shades in a
beam's bounding box (expect ≥3), and diff a patch around the crossing between the
depth-sorted and flipped screenshots (expect a clear change). `UI.flips()`
gives a non-pixel confirmation that the crossing's flip toggled.

## Testing SparkLab

`sparklab.html` (the maths game) is DOM/SVG UI rather than a free-drawing
canvas, so tests **drive its `window.UI` hook** instead of pointer gestures
(`--gesture none` always). Two calls make runs reproducible:

- `UI.seed(n)` — deterministic PRNG, so the same questions come up every run.
- `UI.fx(false)` — kills animations, particles, sound and narration, so
  screenshots are stable (it also neutralises entrance animations that would
  otherwise catch elements mid-flight).

The rest of the hook:

```js
UI.reset();                  // wipe the save, back to first-run state
UI.go('home'|'hall'|'progress'|'title'|<machineId>);   // navigate
UI.start('rocket', 3);       // jump straight into a mission (unlocks to there)
UI.question();               // {fact, text, prompt, answer, mode, options, retry, target}
UI.answer(v);                // submit (returns true/false); works for MCQ + keypad
UI.next();                   // skip the feedback delay (tests don't need to wait)
UI.state();                  // screen, sparks, mission progress, machines, facts…
UI.grant({sparks, inventions, pieces, name, avatar}); // fixtures for hall/dashboard shots
```

A scripted mission is a synchronous loop — no waits needed:

```sh
venv/bin/python tools/shoot.py --url sparklab.html --gesture none --setup "
  UI.reset(); UI.fx(false); UI.seed(3); UI.start('power',1);
  for(let i=0;i<20 && UI.state().mission;i++){
    const q=UI.question(); UI.answer(i===2 ? q.answer+1 : q.answer); UI.next(); }
" --out tools/shots/sl_results.png
```

(That run asserts the whole pipeline via `UI.state()`: 10 base questions + the
missed one re-queued, first-try 9/10 → star maths, level unlock, blueprint
pieces, daily streak, per-fact stats.)

To catch **feedback states** mid-flight, answer in `--setup` and use a short
`--settle`: correct feedback lingers ~800 ms, wrong feedback ~3.2 s
(`--settle 300` lands inside both).

**Real-input suite.** `tools/sparklab_test.py` drives the game the way a child
does — real clicks on doors/options/keypad, physical keyboard digits + Enter,
the press-and-hold grown-ups gear (a quick tap must *not* open it), pause/quit
spark banking, and a reload to prove `localStorage` persistence — 19 checks,
must end `19/19` with no console errors:

```sh
venv/bin/python tools/sparklab_test.py
```

Gotchas found during bring-up:

- **`.no-fx` vs entrance animations:** anything animated *into* place
  (e.g. the results stars scale from 0 with `forwards`) must have a `.no-fx`
  override that lands it in its final state, or FX-off screenshots show it
  missing entirely.
- **SVG `<use>` styling:** CSS can't reach `path` inside a `<use>` shadow tree;
  style the `<svg>`/`<use>` itself (`fill`/`stroke` inherit through).
- Audio and narration can only be verified to **degrade gracefully** headless
  (no `AudioContext` output device, no TTS voices) — which is their specified
  fallback behaviour, same as Whorl's mic.
- Each `shoot.py` run is a fresh browser context, so **localStorage does not
  persist between runs** — build fixture state inside one `--setup`
  (`UI.grant`, scripted missions), not across invocations.

## Notes / gotchas

- **Cold-start race:** the gesture must start only after the canvas has sized to
  the viewport, otherwise the first stroke renders against a not-yet-sized canvas
  and lands off-center. `shoot.py` waits two animation frames after page load to
  avoid this.
- `tools/selftest.html` is a throwaway stand-in canvas used to validate the
  harness before `whorl.html` exists. It can be deleted once the real app is in
  place.

## Files

- `tools/shoot.py` — the harness.
- `tools/sparklab_test.py` — SparkLab real-input interaction suite (19 checks).
- `tools/shots/` — screenshot output (gitignored).
- `tools/selftest.html` — temporary stand-in for validating the harness.
