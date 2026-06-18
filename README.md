# Whorl

A browser-based, interactive symmetric-drawing toy. Drag (mouse, touch, or pen)
and your stroke is mirrored and rotated around the center to grow evolving star
and snowflake forms, with additive glow where the arms cross.

## Running it

Just open **`index.html`** — double-click it, or drag it into any modern browser.
There's no server, no build step, and no dependencies. It works on desktop
(mouse) and phones/tablets (touch).

Open the controls with the **gear icon** in the corner (top-right on desktop, a
slide-up sheet at the bottom on mobile). Tap the gear again to hide it and let
the canvas fill the screen.

---

## The controls

Everything below lives in that gear panel.

### Fold count
How many rotational copies of your stroke are drawn around the center, from
**3** to **16** (default **6**). Low numbers give bold, chunky stars; high
numbers give fine, lacy mandalas. This is the single biggest lever on the overall
shape.

### Mirror symmetry
A toggle that decides whether each rotated copy is *also* reflected.

- **Off** → a **pinwheel**: the arms all spiral the same way (they have a
  direction / handedness).
- **On** (default) → a **snowflake**: every arm is mirrored, giving the balanced,
  kaleidoscopic look. With mirror on you get twice as many copies (`2 × fold
  count`).

### Persistence
A toggle for how long your drawing lasts.

- **Building up** (default) → strokes accumulate into a lasting mandala; nothing
  is erased until you Clear.
- **Fading** → older strokes gradually fade away, so the figure is ephemeral and
  always in motion. How fast they fade is set by the next slider.

### Fade rate
Controls the fade speed when **Persistence** is set to *fading* (it's greyed out
while you're in *building up* mode). Range **0–1** (default **0.10**):

- **0** → never fades (identical to *building up*).
- Higher → strokes vanish faster. Around **1** a stroke is gone in well under a
  second, leaving a comet-like trail as you draw.

> Persistence and Fade rate work together: *building up* is really just fade = 0.
> The toggle is the quick switch; the slider is the fine-tune.

### Global spin
A signed speed slider from **−1 to +1** (default a small **+**) that slowly
rotates the whole accumulated figure.

- **0** → the figure sits still.
- **Positive** → rotates one way; **negative** → the other.
- The magnitude sets how fast (roughly up to ~22°/second at the extremes).

*(If your system is set to "reduce motion", spin is forced off and this slider is
disabled — see [Accessibility](#accessibility).)*

### Brush size
Sets the base stroke thickness, from **thin** to **thick** (default **mid**).

The actual width also reacts to how fast you draw: **draw slowly for thick
strokes, quickly for thin ones.** Brush size scales that whole range up or down.

### Color mode
A three-way switch for where each stroke's color comes from:

1. **Palette** — colors come from a chosen preset (see below). The hue drifts
   slowly over time, so even a single drag has gradient life. Choosing this mode
   reveals the **Palette** row.
2. **Speed** — color is derived from *how* you draw: hue blends your angle around
   the center with your pointer speed (slow leans blue, fast leans red), and fast
   strokes get a touch brighter. The figure ends up encoding the gesture that
   made it.
3. **Audio** — color and brightness react to your microphone (see
   [Audio mode](#audio-mode-in-detail)).

### Palette
Visible only in **Palette** color mode. Five curated presets:

| Swatch | Name | Feel |
|---|---|---|
| teal → violet | **Aurora** | cool cyan-to-purple (default) |
| red → gold | **Ember** | warm fire tones |
| gold | **Mono-gold** | near-single-hue gold |
| blue → indigo | **Ocean** | deep blues and teals |
| pink → cyan | **Candy** | bright, playful, wide range |

### Blend mode
How overlapping arms combine where they cross:

- **Glow** (default) → additive blending. Overlaps add up and **bloom to white**
  at the bright center — punchy and luminous.
- **Soft** → screen blending. Overlaps still brighten, but gently, so the center
  keeps its color instead of blowing out — a calmer, more pastel look.

### Clear
Wipes the canvas with a short **fade-to-empty animation** (not a hard cut).

### Save PNG
Exports the current canvas as a PNG download (`whorl-<timestamp>.png`).

---

## Audio mode in detail

Audio mode listens to your microphone and maps:

- **loudness → stroke width and brightness** (loud = thick, bright strokes), and
- **dominant frequency → hue** (different pitches paint different colors).

A few things to know:

- The mic is **only requested when you actually select Audio mode** — never on
  page load.
- If you **deny permission** or have no microphone, the toy shows a small
  "Mic unavailable" note and quietly falls back to your previous color mode. A
  denied permission never breaks anything.
- Some browsers only allow mic access over `https://` or `file://`; if Audio mode
  silently falls back, that's usually why.

---

## Idle autopilot

Leave it alone in **fading** mode and it turns into a screensaver. Once your
pattern has fully faded away and the canvas has sat empty for **15 seconds**, a
synthetic "pen" starts drawing on its own, drifting around the center to grow an
ever-changing mandala that keeps gently fading.

- It only runs in **fading** mode — in *building up* mode it stays off, so your
  lasting work is never disturbed.
- **Touch or drag to take over.** The moment you draw, autopilot stops and leaves
  its pattern on screen; from there you can add to it, hit Clear, or just let it
  fade.
- It's disabled under the "reduce motion" system setting.

## Tips

- **Draw slowly** for bold, glowing lines; **flick quickly** for delicate
  filaments — the width follows your speed.
- Combine **fading** + a gentle **spin** for a living, breathing animation that
  never quite settles.
- Crank **fold count** up with **mirror on** for intricate snowflakes; drop it
  low with **mirror off** for punchy pinwheels.
- Overlapping arms **bloom to white** where they cross — that additive glow is
  most of the magic, so let your strokes pass through the center.

---

## Accessibility

The toy respects your OS **"reduce motion"** setting: when it's on, the gentle
global spin and the touch ripples are disabled, and the spin slider is greyed
out. Everything else works the same.

---

## Settings reference (for tinkerers)

There's a small global hook, `window.UI`, usable from the browser console (it's
also what the test harness drives):

```js
UI.set({ folds: 8, mirror: true, persistent: false, fade: 0.4,
         spin: -0.3, brush: 0.7, colorMode: 'palette', palette: 'ocean' });
UI.get();    // current settings as an object
UI.clear();  // trigger the clear animation
UI.count();  // number of stored stroke segments
```

| Key | Type / range | Meaning |
|---|---|---|
| `folds` | 3–16 | fold count |
| `mirror` | boolean | mirror symmetry on/off |
| `persistent` | boolean | true = building up, false = fading |
| `fade` | 0–1 | fade rate (when not persistent) |
| `spin` | −1…+1 | global spin speed/direction |
| `brush` | 0–1 | base stroke width |
| `colorMode` | `'palette'` \| `'speed'` \| `'audio'` | color source |
| `palette` | `'aurora'` \| `'ember'` \| `'mono-gold'` \| `'ocean'` \| `'candy'` | active preset |
| `blend` | `'lighter'` \| `'screen'` | blend mode (Glow / Soft) |

---

## Project layout

```
index.html             the entire app (HTML + CSS + JS, self-contained)
README.md              this file
whorl-spec.md          the original design spec
TESTING.md             how the visual test harness works
tools/shoot.py         Playwright screenshot harness (drives the app, captures PNGs)
tools/shots/           generated screenshots (gitignored)
```

See **TESTING.md** for how the app is visually tested.
