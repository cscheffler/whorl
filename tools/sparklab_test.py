#!/usr/bin/env python3
"""Real-input interaction test for sparklab.html (clicks, keyboard, hold, reload)."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

url = (Path(__file__).resolve().parent.parent / 'sparklab.html').as_uri()
logs, errs = [], []
checks = []
def ok(name, cond):
    checks.append((name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + name)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 900, 'height': 700})
    pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(f"{m.type}:{m.text}"))
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url, wait_until='load')
    pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
    pg.evaluate("UI.reset(); UI.fx(false); UI.seed(1)")

    # --- first-run flow, real clicks ---
    pg.click('#btn-play')
    ok('setup card appears on first Play', pg.is_visible('#setup-card'))
    pg.click('.avatar-pick[data-av="2"]')
    pg.fill('#name-input', 'Testo')
    pg.click('#btn-setup-done')
    st = pg.evaluate("UI.state()")
    ok('setup done -> home, profile saved',
       st['screen'] == 'home' and st['profile']['name'] == 'Testo' and st['profile']['avatar'] == 2)

    # --- door -> intro -> mission ---
    pg.click('.door[data-mid="power"]')
    ok('door opens intro', pg.evaluate("UI.state().screen") == 'intro')
    pg.click('#btn-intro-start')
    ok('intro starts mission', pg.evaluate("UI.state().screen") == 'mission')

    # --- MCQ real click: correct ---
    ans = pg.evaluate("UI.question().answer")
    pg.click(f'.mcq .opt[data-v="{ans}"]')
    st = pg.evaluate("UI.state()")
    ok('correct MCQ click: streak 1, sparks >= 10',
       st['mission']['streak'] == 1 and st['mission']['sparks'] >= 10)
    pg.evaluate("UI.next()")

    # --- MCQ real click: wrong -> requeue ---
    q = pg.evaluate("UI.question()")
    wrong = [o for o in q['options'] if str(o) != str(q['answer'])][0]
    pg.click(f'.mcq .opt[data-v="{wrong}"]')
    st = pg.evaluate("UI.state()")
    ok('wrong MCQ click: streak reset + retry queued',
       st['mission']['streak'] == 0 and st['mission']['retries'] == 1)
    fb = pg.text_content('#q-feedback')
    ok('wrong answer shows explanation', 'Not quite' in fb)
    pg.evaluate("UI.next()")

    # --- pause + quit banks sparks ---
    pg.click('#btn-pause')
    ok('pause overlay shows', pg.is_visible('#ov-pause'))
    pg.click('#btn-quit')
    st = pg.evaluate("UI.state()")
    ok('quit -> home with sparks banked', st['screen'] == 'home' and st['sparks'] >= 10)

    # --- keypad level: physical keyboard ---
    pg.evaluate("UI.start('power',2)")
    ans = pg.evaluate("UI.question().answer")
    pg.keyboard.type(str(ans))
    pg.keyboard.press('Enter')
    st = pg.evaluate("UI.state()")
    ok('keyboard digits + Enter submit', st['mission']['streak'] == 1)
    pg.evaluate("UI.next()")

    # --- hint reveals hidden model; keypad button clicks ---
    hidden = pg.evaluate("document.getElementById('q-model').classList.contains('hidden-model')")
    pg.click('#btn-hint')
    shown = pg.evaluate("!document.getElementById('q-model').classList.contains('hidden-model')")
    ok('hint reveals the visual model', hidden and shown)
    ans = str(pg.evaluate("UI.question().answer"))
    for ch in ans:
        pg.click(f'.pad-grid .pk[data-k="{ch}"]')
    pg.click('.pad-grid .pk[data-k="go"]')
    st = pg.evaluate("UI.state()")
    ok('keypad taps submit correct answer', st['mission']['streak'] == 2)

    # --- persistence across reload ---
    sparks = pg.evaluate("UI.state().sparks")
    pg.reload(wait_until='load')
    pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
    st = pg.evaluate("UI.state()")
    ok('localStorage persists across reload',
       st['sparks'] == sparks and st['profile']['name'] == 'Testo')

    # --- grown-ups gear: tap warns, hold opens ---
    pg.evaluate("UI.fx(false); UI.go('home')")
    box = pg.locator('#grown-btn').bounding_box()
    cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
    pg.mouse.click(cx, cy)
    ok('quick tap does NOT open grown-ups', pg.evaluate("UI.state().screen") == 'home')
    pg.mouse.move(cx, cy); pg.mouse.down(); pg.wait_for_timeout(1400); pg.mouse.up()
    ok('1.4s hold opens grown-ups corner', pg.evaluate("UI.state().screen") == 'progress')

    # --- full mission via hook: star maths & unlock ---
    pg.evaluate("""
      UI.reset(); UI.fx(false); UI.seed(42); UI.grant({name:'Testo'}); UI.start('clone',1);
      for(let i=0;i<20 && UI.state().mission;i++){ UI.answer(UI.question().answer); UI.next(); }
    """)
    st = pg.evaluate("UI.state()")
    m = st['machines']['clone']
    ok('perfect mission -> 3 stars + next level unlocked',
       st['screen'] == 'results' and m['stars']['1'] == 3 and m['unlocked'] == 2)

    # --- mix lab runs to completion ---
    pg.evaluate("""
      UI.start('mix',1);
      for(let i=0;i<24 && UI.state().mission;i++){ UI.answer(UI.question().answer); UI.next(); }
    """)
    st = pg.evaluate("UI.state()")
    ok('mix lab completes 12 questions', st['screen'] == 'results' and st['totals']['answered'] >= 22)

    # --- export / import: transfer progress to a "new browser" ---
    import tempfile, os
    pg.evaluate("UI.go('progress')")
    with pg.expect_download() as dl:
        pg.click('#btn-export')
    ok('export button downloads a progress file',
       dl.value.suggested_filename.startswith('sparklab-progress-') and
       dl.value.suggested_filename.endswith('.json'))
    exported = pg.evaluate("UI.export()")
    sparks_before = pg.evaluate("UI.state().sparks")
    tmp = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    tmp.write(exported); tmp.close()
    bad = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    bad.write('{"totally":"not a save"}'); bad.close()

    pg.evaluate("UI.reset()")                       # the "new browser"
    ok('reset wipes progress before import', pg.evaluate("UI.state().sparks") == 0)
    pg.evaluate("UI.go('progress')")
    pg.set_input_files('#import-file', bad.name)
    pg.wait_for_timeout(400)
    ok('corrupt file rejected, no confirm shown',
       not pg.is_visible('#ov-confirm') and pg.evaluate("UI.state().sparks") == 0)
    pg.set_input_files('#import-file', tmp.name)
    pg.wait_for_timeout(400)
    ok('valid file asks for confirmation', pg.is_visible('#ov-confirm'))
    pg.click('#confirm-yes')
    st = pg.evaluate("UI.state()")
    ok('import restores sparks + profile',
       st['sparks'] == sparks_before and st['profile']['name'] == 'Testo')
    pg.reload(wait_until='load')
    pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
    ok('imported progress persists after reload',
       pg.evaluate("UI.state().sparks") == sparks_before)
    os.unlink(tmp.name); os.unlink(bad.name)

    b.close()

bad_console = [l for l in logs if l.startswith(('error', 'warning')) and 'AudioContext' not in l]
ok('no page errors', not errs)
ok('no console errors/warnings', not bad_console)
if errs: print('ERRS:', errs)
if bad_console: print('CONSOLE:', bad_console)
fails = [n for n, c in checks if not c]
print(f"\n{len(checks) - len(fails)}/{len(checks)} checks passed")
sys.exit(1 if fails else 0)
