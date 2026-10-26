#!/usr/bin/env python3
"""Headless browser check for the standalone page and the embedding API.

Serves the repo over HTTP (ES modules don't load from file://), then with Playwright + Chromium
(SwiftShader WebGL 2):
  (a) index.html renders something that isn't black, with no console errors;
  (b) tests/embed.html: mount into a 640x360 div, dispose (canvas gone, context lost), mount again,
      two simultaneous mounts, the handle methods, and the 'no-webgl2' error path.

Run: ~/.venvs/web/bin/python tests/embed_check.py   (exits non-zero on failure)
"""
import functools, http.server, io, os, sys, threading

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
failures = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def lit_fraction(png):
    """Fraction of pixels brighter than near-black (the background nebula is very dark)."""
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(int)
    return float((a.max(axis=2) > 60).mean()), int(a.max())


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def watch(page):
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    return errors


def main():
    httpd = serve()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    with sync_playwright() as p:
        browser = p.chromium.launch(args=FLAGS)

        # (a) standalone page
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        errors = watch(page)
        page.goto(base + "/index.html")
        page.wait_for_timeout(3000)
        png = page.screenshot(path=os.path.join(ROOT, "tests", "out-index.png"))
        frac, mx = lit_fraction(png)
        check(frac > 0.002, f"index.html renders (lit fraction {frac:.4f}, max {mx})")
        title = page.text_content(".lw3d-now h1")
        check(bool(title) and title != "Loading", f"index.html HUD shows a program title ({title!r})")
        check(page.evaluate("getComputedStyle(document.querySelector('.lw3d-hud')).display") != "none", "index.html HUD visible")
        page.keyboard.press("e")
        check(page.evaluate("!document.querySelector('.lw3d-panel').hidden"), "E opens the source editor")
        page.keyboard.press("Escape")
        page.keyboard.press("l")
        check(page.evaluate("localStorage.getItem('lw3d.look')") == '"neon"', "L cycles the look and the page persists it")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        check(not errors, f"index.html no console errors {errors}")
        page.close()

        # (b) embedding
        page = browser.new_page(viewport={"width": 800, "height": 900})
        errors = watch(page)
        page.goto(base + "/tests/embed.html")
        page.wait_for_function("window.__ready")
        check(page.evaluate("window.__importLeaks") == [], "import adds no globals")
        check(page.evaluate("document.querySelectorAll('#a *, #b *').length") == 0, "import touches no DOM")

        page.evaluate("window.h1 = LW.mount(document.getElementById('a'), {look:'hologram', programs:['lorenz-attractor','fireworks'], order:'sequence'})")
        page.wait_for_timeout(3000)
        frac, mx = lit_fraction(page.locator("#a").screenshot(path=os.path.join(ROOT, "tests", "out-embed-a.png")))
        check(frac > 0.002, f"mount #a renders (lit fraction {frac:.4f}, max {mx})")
        dpr = page.evaluate("devicePixelRatio")
        size = page.evaluate("(c => [c.width, c.height])(document.querySelector('#a canvas'))")
        check(size == [round(640 * min(dpr, 2)), round(360 * min(dpr, 2))], f"canvas backing size follows container x DPR {size}")
        check(page.evaluate("getComputedStyle(document.body).overflow") == "visible"
              and page.evaluate("getComputedStyle(document.body).margin") == "16px", "host html/body styles untouched")
        check(page.evaluate("document.querySelector('#a .lw3d-hud').hidden"), "hud defaults to off")

        page.evaluate("h1.pause(); h1.resume(); h1.next(); h1.set({look:'tubes', cam:'orbit', speed:2, hud:true})")
        page.wait_for_timeout(300)
        check(page.evaluate("!document.querySelector('#a .lw3d-hud').hidden"), "set({hud:true}) shows the HUD")
        check(page.text_content("#a .lw3d-now h1") in ("Lorenz attractor", "Fireworks"), "programs/order restrict the playlist")

        page.evaluate("window.c1 = document.querySelector('#a canvas'); window.gl1 = c1.getContext('webgl2'); h1.dispose(); h1.dispose()")
        check(page.evaluate("document.querySelector('#a canvas') === null && document.getElementById('a').children.length === 0"), "dispose removes canvas and DOM")
        check(page.evaluate("gl1.isContextLost()"), "dispose loses the WebGL context")
        check(page.evaluate("document.head.querySelectorAll('style').length") == 1, "no leftover styles in head")

        page.evaluate("window.h2 = LW.mount(document.getElementById('a'), {look:'random'}); window.h3 = LW.mount(document.getElementById('b'), {look:'dream', cam:'drift', fps:30})")
        page.wait_for_timeout(3000)
        for sel in ("#a", "#b"):
            frac, mx = lit_fraction(page.locator(sel).screenshot(path=os.path.join(ROOT, "tests", f"out-embed2-{sel[1]}.png")))
            check(frac > 0.002, f"remount / simultaneous mount {sel} renders (lit fraction {frac:.4f}, max {mx})")
        page.evaluate("h2.dispose(); h3.dispose()")
        check(page.evaluate("document.querySelectorAll('#a *, #b *').length") == 0, "both disposed cleanly")

        code = page.evaluate("""() => {
            const orig = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = () => null;
            try { LW.mount(document.getElementById('a')); return 'no throw' }
            catch (e) { return e.code }
            finally { HTMLCanvasElement.prototype.getContext = orig }
        }""")
        check(code == "no-webgl2", f"no WebGL 2 throws err.code 'no-webgl2' ({code})")
        check(page.evaluate("document.getElementById('a').children.length") == 0, "failed mount injects no DOM")
        check(not errors, f"embed page no console errors {errors}")
        browser.close()
    httpd.shutdown()
    print("FAILED: %d" % len(failures) if failures else "all checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
