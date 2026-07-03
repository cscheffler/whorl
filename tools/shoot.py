#!/usr/bin/env python3
"""
shoot.py — visual test harness for the Whorl toy.

Loads a static HTML file over file://, optionally runs setup JS (to set
controls), performs a scripted pointer gesture (so the canvas actually
draws), lets the rAF loop settle, then writes a PNG screenshot.

Console logs and uncaught page errors are captured and printed, so JS
exceptions surface here instead of failing silently.

Examples:
    venv/bin/python tools/shoot.py --url whorl.html --out tools/shots/default.png
    venv/bin/python tools/shoot.py --url whorl.html --gesture spiral --touch \
        --setup "UI.set({folds:8, mirror:true})" --out tools/shots/snowflake.png

The --setup JS is optional and app-specific; it only matters once the app
exposes a hook. Gestures work on any canvas regardless.
"""
import argparse
import math
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def gesture_points(name, w, h):
    """Return a list of (x, y) viewport points describing a drag path."""
    cx, cy = w / 2, h / 2
    pts = []
    if name == "spiral":
        # Expanding spiral from near-center outward — great whorl fodder,
        # and the changing radius/speed exercises velocity-driven width.
        turns = 3.0
        n = 140
        rmax = min(w, h) * 0.40
        for i in range(n + 1):
            t = i / n
            ang = t * turns * 2 * math.pi
            r = rmax * t
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    elif name == "arc":
        # A single sweeping arc offset from center.
        n = 80
        r = min(w, h) * 0.30
        for i in range(n + 1):
            t = i / n
            ang = -math.pi / 3 + t * (2 * math.pi / 3)
            pts.append((cx + r * math.cos(ang), cy - r * 0.3 + r * math.sin(ang)))
    elif name == "line":
        n = 60
        x0, y0 = cx - w * 0.25, cy - h * 0.15
        x1, y1 = cx + w * 0.25, cy + h * 0.15
        for i in range(n + 1):
            t = i / n
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    elif name == "scribble":
        # Lissajous-ish wander for a busier figure.
        n = 200
        for i in range(n + 1):
            t = i / n * 2 * math.pi
            pts.append((cx + w * 0.28 * math.sin(3 * t),
                        cy + h * 0.28 * math.sin(2 * t)))
    elif name == "iso-l":
        # Escher: an L along two isometric screen axes — down-right (+x) then
        # down-left (+y). Deliberately starts a few degrees off the true 30deg
        # iso axis so the app's axis-snapping has something to correct.
        seg = min(w, h) * 0.28
        a30, a150 = math.radians(34), math.radians(146)   # a touch off-axis
        sx, sy = cx - seg * 0.5, cy - seg * 0.3
        n = 40
        for i in range(n + 1):
            pts.append((sx + seg * (i / n) * math.cos(a30),
                        sy + seg * (i / n) * math.sin(a30)))
        ex, ey = pts[-1]
        for i in range(1, n + 1):
            pts.append((ex + seg * (i / n) * math.cos(a150),
                        ey + seg * (i / n) * math.sin(a150)))
    elif name == "iso-stairs":
        # Escher: alternate ground runs (down-right) and vertical climbs to
        # exercise the staircase look. Pair with --setup "UI.set({elevation:...})"
        # only if you want the vertical legs interpreted as z; otherwise this is
        # just a zig-zag that the snapper resolves to x/y runs.
        seg = min(w, h) * 0.16
        x, y = cx - seg * 2, cy
        pts.append((x, y))
        for _ in range(4):
            x += seg * math.cos(math.radians(30)); y += seg * math.sin(math.radians(30))
            pts.append((x, y))
            y -= seg                       # straight up the screen
            pts.append((x, y))
    else:
        raise SystemExit(f"unknown gesture: {name}")
    return pts


def run(args):
    url = args.url
    if "://" not in url:
        url = Path(url).resolve().as_uri()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx_kwargs = dict(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.dpr,
        )
        if args.touch:
            ctx_kwargs.update(has_touch=True, is_mobile=True)
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()
        page.on("console", lambda m: logs.append(f"[console.{m.type}] {m.text}"))
        page.on("pageerror", lambda e: logs.append(f"[pageerror] {e}"))

        page.goto(url, wait_until="load")
        # Wait out the cold-start layout race: ensure the viewport has settled
        # and let two animation frames run so any resize/rAF setup completes
        # before we start driving pointer input (otherwise the first gesture can
        # land against a not-yet-sized canvas and render off-center).
        page.evaluate(
            "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
        )
        page.wait_for_timeout(100)

        if args.setup:
            try:
                page.evaluate(args.setup)
            except Exception as e:
                logs.append(f"[setup-error] {e}")
            page.wait_for_timeout(150)

        if args.gesture != "none":
            pts = gesture_points(args.gesture, args.width, args.height)
            x0, y0 = pts[0]
            page.mouse.move(x0, y0)
            page.mouse.down()
            for (x, y) in pts[1:]:
                page.mouse.move(x, y)
                # Small per-step pause: lets the rAF loop run between moves and
                # produces a realistic, varying pointer speed.
                page.wait_for_timeout(args.step_ms)
            page.mouse.up()

        # Optional taps (a down/up with no move) — e.g. to flip an Escher
        # crossing's over/under. Format: "x,y" repeated via multiple --tap flags.
        for spec in args.tap:
            tx, ty = (float(v) for v in spec.split(","))
            page.mouse.move(tx, ty)
            page.mouse.down()
            page.mouse.up()
            page.wait_for_timeout(80)

        page.wait_for_timeout(args.settle)
        page.screenshot(path=str(out))
        browser.close()

    print(f"wrote {out}  ({os.path.getsize(out)} bytes)")
    if logs:
        print("--- page output ---")
        for line in logs:
            print(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="HTML file path or URL")
    ap.add_argument("--out", default="tools/shots/out.png")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=700)
    ap.add_argument("--dpr", type=float, default=2.0, help="devicePixelRatio")
    ap.add_argument("--touch", action="store_true", help="emulate a touch device")
    ap.add_argument("--gesture", default="spiral",
                    choices=["spiral", "arc", "line", "scribble",
                             "iso-l", "iso-stairs", "none"])
    ap.add_argument("--step-ms", type=int, default=6,
                    help="pause between pointer-move steps")
    ap.add_argument("--settle", type=int, default=600,
                    help="ms to wait after gesture before screenshot")
    ap.add_argument("--setup", default="", help="JS to eval before gesture")
    ap.add_argument("--tap", action="append", default=[], metavar="X,Y",
                    help="tap (down/up, no move) at screen X,Y after the "
                         "gesture; repeatable. Used for Escher crossing flips.")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
