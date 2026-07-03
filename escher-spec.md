# Spec: Escher Ribbon — Interactive Impossible-Geometry Drawing

## Concept

A browser canvas where dragging traces an isometric "ribbon" — a chunky 3D-looking extruded path rendered in Monument Valley's flat, pastel, axonometric style. The Escher feel comes from **true isometric projection** (no perspective): the brain reads impossible spatial continuity. Each ribbon segment is a solid beam drawn as three flat-shaded faces (top, left, right), so the path always reads as architecture.

## Rendering approach

**2.5D isometric on 2D canvas — not real 3D.** Project world coords `(x, y, z)` to screen with a fixed isometric matrix:

```
screenX = (x - y) * cos(30°)
screenY = (x + y) * sin(30°) - z
```

Every segment is a beam extruded along its axis, drawn as three parallelogram faces at three brightness levels (top brightest, one side mid, one side dark). Flat fills only — no gradients. Redraw the whole path each frame via `requestAnimationFrame`.

## Drag → geometry

- Sample pointer via Pointer Events (mouse + touch unified).
- **Snap drag direction to the three isometric screen axes** (30° / 150° / 270°). This is what makes it read as architecture rather than scribble.
- **Default: hard-snapped.** Snap strength is still a slider (0 = free curve, 1 = hard snap) but ships at 1.
- Each committed segment becomes a beam of the current width/height extruded along the snapped axis.
- Store each segment's world coords + screen-space bounding quad (needed for crossings).
- Render a mitered cube joint at every direction change so corners look solid.

## Elevation

- **Dedicated mode toggle** ("Build Up / Down" button in the panel). When active, drags change `z` instead of moving in the ground plane — paths climb and descend ramps.
- Elevation + isometric is the core Monument Valley move; it makes crossings and loops far more interesting.

## Crossings (over/under)

**No randomization.** Two layers:

1. **Baseline: depth-sort** all segments by isometric depth key (`x + y + z`), painter's algorithm. Gives consistent, physically-plausible over/under for free.
2. **Impossible toggle:** tapping a crossing flips that segment's draw order, deliberately breaking the depth rule. This is the Escher payoff — the user *creates* the paradox rather than the system randomizing it.

So: consistent by default, paradox on demand.

## Color / visual controls

Collapsible panel, top-right:

- **Palette picker** — 4–5 curated MV-style palettes (dusty pink/coral, teal/sand, lavender/peach, etc.). Each palette defines the three face shades + background. Curated triads beat a raw color wheel.
- **Hue drift** — optional gradual hue shift along path length, so the ribbon gradients as it grows.
- **Beam width / height** — sliders.
- **Snap strength** — slider (default 1).
- **Background** — flat color from the active palette.

## Geometry features worth building

- **Ramps** via the elevation mode above.
- **Auto-loop closure** — when the path head nears its tail, snap-close into a loop. Closed impossible loops (Penrose-stair style) are the most satisfying output.
- **Mitered corner joints** — solid cube at each turn.

## Stack

- Vanilla **TypeScript + 2D canvas**. No 3D engine, no heavy build.
- Pointer Events, `requestAnimationFrame` loop.
- Small module set (e.g. `projection.ts`, `ribbon.ts`, `render.ts`, `controls.ts`, `main.ts`).

## Nice-to-haves (if time)

- Export PNG.
- Undo (pop last segment).
- Subtle ground-plane drop shadow for grounding.
