# Visual testing harness

This app is a browser-based **Canvas 2D** toy with **no server** — it opens by
double-clicking `index.html` (`file://`). Because the visuals only appear in
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
venv/bin/python tools/shoot.py --url index.html --out tools/shots/default.png
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
venv/bin/python tools/shoot.py --url index.html --touch \
  --setup "UI.set({folds:8, mirror:true})" \
  --gesture spiral --out tools/shots/snowflake.png

# A single sweeping arc, no symmetry tweaks
venv/bin/python tools/shoot.py --url index.html --gesture arc \
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

## Notes / gotchas

- **Cold-start race:** the gesture must start only after the canvas has sized to
  the viewport, otherwise the first stroke renders against a not-yet-sized canvas
  and lands off-center. `shoot.py` waits two animation frames after page load to
  avoid this.
- `tools/selftest.html` is a throwaway stand-in canvas used to validate the
  harness before `index.html` exists. It can be deleted once the real app is in
  place.

## Files

- `tools/shoot.py` — the harness.
- `tools/shots/` — screenshot output (gitignored).
- `tools/selftest.html` — temporary stand-in for validating the harness.
