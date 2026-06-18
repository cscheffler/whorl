# Kaleidoscope Drawing Toy — Implementation Spec

A browser-based, interactive symmetric-drawing experience inspired by the
end-of-level "sacred geometry" sequences in *Monument Valley*. The user drags
(mouse or touch) and their stroke is mirrored/rotated around a center point to
produce evolving star and snowflake forms. Includes live controls for symmetry,
color, persistence, and an optional audio-reactive mode.

---

## 1. Goals & feel

- **Meditative and immediate.** No load screen, no instructions needed — touch
  the canvas and something beautiful happens.
- **Buttery on mobile.** Primary target is touch on a phone; must also work with
  mouse on desktop. 60fps with the figure slowly turning.
- **Tweakable, not fiddly.** Controls live in a collapsible panel so the canvas
  stays the star of the show.

---

## 2. Tech stack

- **Single self-contained `index.html`** (HTML + CSS + JS inline, or a small
  `main.js` — implementer's choice, but keep it to one deployable folder, no
  build step required).
- **Canvas 2D**, not WebGL. Line-based mandalas don't need shaders, and Canvas 2D
  with `globalCompositeOperation = 'lighter'` (additive blending) gives the glow
  for free.
- **No external libraries** except optionally a tiny color helper. Vanilla JS.
- Use `devicePixelRatio` scaling so it's crisp on retina/phone screens.

---

## 3. Core drawing mechanic

### Input → segments
- Track pointer position via Pointer Events (`pointerdown`/`move`/`up`) so mouse,
  touch, and pen all work through one path. Set `touch-action: none` on the
  canvas to stop the page scrolling while drawing.
- On each move, you have a previous point `p0` and current point `p1`. The unit
  of drawing is the **segment** `p0→p1`. Everything is drawn relative to the
  canvas center `c`.

### Symmetry replication
For each segment, transform it into center-relative coordinates, then draw it
once per symmetry slice:

- **Rotational copies:** for `i in 0..N-1`, rotate the segment by `i * (2π / N)`
  and draw.
- **Mirror (dihedral):** when mirror mode is on, *also* draw the reflected copy
  of each rotated segment (reflect across the slice's axis). This is what turns a
  pinwheel into a snowflake. With mirror on you effectively get `2N` copies.

Both modes are independently **toggleable** (per the two switches in §5):
- Rotational only → pinwheel.
- Rotational + mirror → dihedral snowflake (the Monument Valley look).

`N` (fold count) is a live slider, default **6**, range **3–16**.

### Stroke styling that makes it feel alive
Implement these — they're cheap and they're what separate "neat" from "lovely":

- **Velocity-driven width.** Compute pointer speed (px/frame). Map *slow → thick,
  fast → thin* (e.g. `width = clamp(baseWidth * (1 - speed/maxSpeed), min, max)`).
  Smooth it so width doesn't jitter.
- **Round line caps and joins** (`lineCap='round'`, `lineJoin='round'`).
- **Slow global rotation.** The entire accumulated figure rotates gently
  (~2–4°/sec, direction/speed exposed as an optional slider). Implement by
  rotating the canvas before redraw, or by storing strokes and re-rendering — see
  §4.

---

## 4. Persistence model (toggleable)

Expose a **Persistence** toggle with two states, plus a decay slider:

- **Persistent (build-up):** strokes accumulate into a lasting mandala. Implement
  by *not* clearing the canvas between frames — draw new segments on top. (This is
  the cheap, classic approach and works great with additive blending.)
- **Fading (ephemeral):** each frame, paint a low-alpha fill of the background
  color over the whole canvas before drawing new segments, so old strokes decay.
  A **decay slider** controls that alpha (0 = never fades → persistent; higher =
  faster fade). This means "persistent" is really just decay = 0, but keep the
  toggle as a clear UX affordance and let the slider fine-tune.

> Note on global rotation + persistence: if you draw directly to a single canvas,
> a continuously rotating *accumulated* image will smear. Two clean options:
> **(a)** keep figure static and skip global rotation when in pure-persistent
> mode, or **(b)** store strokes as data (array of {points, color, width, time})
> and re-render every frame with the current rotation applied. Prefer **(b)** if
> feasible — it makes rotation, fade, symmetry changes, and a clean "replay"
> all trivial. Cap stored strokes (e.g. ring buffer) to bound memory.

---

## 5. Controls

Collapsible panel (hamburger or gear icon, top corner). On mobile it slides up
from the bottom. Keep the canvas fullscreen behind it.

| Control | Type | Range / options | Default |
|---|---|---|---|
| Fold count (N) | slider | 3–16 | 6 |
| Mirror symmetry | toggle | on / off | on |
| Persistence | toggle | persistent / fading | persistent |
| Decay rate | slider | 0–1 | 0 |
| Global spin | slider | −1 … +1 (signed speed) | small + |
| Brush size | slider | thin–thick | mid |
| Color mode | segmented | Palette / Speed-position / Audio | Palette |
| Clear | button | — | — |
| Save PNG | button | — | — |

Add a **Clear** (fade-to-empty animation, not a hard wipe) and **Save PNG**
(export current canvas via `toBlob`). These are low-effort, high-delight.

---

## 6. Color modes (all three)

A small enum drives per-segment color. HSL is the natural space here.

1. **Palette.** User picks a base hue / preset palette (offer ~5 curated presets:
   e.g. *aurora* cyan-violet, *ember* red-gold, *mono-gold*, *ocean*, *candy*).
   Segments draw in palette colors, optionally cycling slowly through the palette
   over time so a single drag still has gradient life.

2. **Speed / position.** Hue derived from pointer state:
   - hue from **angle around center** (position) *or* from **speed** (fast =
     hotter hue), implementer can blend both;
   - saturation/lightness can also nudge with speed.
   This makes the figure's color encode *how* you drew it.

3. **Audio-reactive (optional, graceful).**
   - Request mic via `getUserMedia({audio:true})` → `AudioContext` →
     `AnalyserNode`. Use FFT to get an amplitude/bass value per frame.
   - Map **amplitude → brush width and/or brightness**, and **dominant
     frequency band → hue**. Loud bass = thick bright strokes.
   - **Must degrade gracefully:** if the user denies permission or no mic exists,
     disable this mode with a small "mic unavailable" note and fall back to the
     last-used mode. Never let a denied permission break the toy. Only request the
     mic when the user actually selects this mode (not on page load).

Use additive blending (`'lighter'`) for all modes so overlapping symmetric arms
bloom where they cross — this is most of the visual magic.

---

## 7. Visual polish (do these)

- Dark, near-black background (slight radial vignette toward edges) so additive
  glow pops.
- Faint center dot or subtle guide rings that fade out shortly after first touch,
  hinting at the symmetry center without cluttering.
- On `pointerdown`, a soft bloom/ripple at the touch point for tactile feedback.
- Respect `prefers-reduced-motion`: if set, disable global spin and ripples.

---

## 8. Performance

- Cap stored strokes / use a ring buffer if using the re-render approach (§4b).
- Throttle pointermove work to `requestAnimationFrame` (collect points, draw once
  per frame), don't draw synchronously on every move event.
- Resize handler that re-scales canvas to `devicePixelRatio` and recenters.

---

## 9. Acceptance checklist

- [ ] Dragging produces N-fold symmetric strokes; N adjustable live 3–16.
- [ ] Mirror toggle visibly switches pinwheel ↔ snowflake.
- [ ] Persistence toggle + decay slider behave as specified (decay 0 = persistent).
- [ ] All three color modes work; audio mode degrades gracefully on denial.
- [ ] Velocity affects stroke width; additive glow on overlaps.
- [ ] Gentle global spin; respects reduced-motion.
- [ ] Smooth on a phone (touch, no page scroll while drawing) and desktop (mouse).
- [ ] Clear (animated) and Save PNG both work.
- [ ] Single folder, no build step, opens by double-clicking index.html.

---

## 10. Nice-to-haves (only if time)

- "Idle autopilot": after N seconds untouched, a synthetic drifting pointer draws
  on its own (screensaver mode), stops on touch.
- Shareable state via URL hash (encode current settings).
- A second blend mode option (`screen`) for a softer look.
