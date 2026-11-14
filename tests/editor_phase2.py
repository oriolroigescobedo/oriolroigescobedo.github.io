#!/usr/bin/env python3
"""Phase 2 smoke/regression tests; run against development branch with Playwright."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

server = ThreadingHTTPServer(("127.0.0.1", 8962), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for width, height in [(1440, 900), (390, 844)]:
                for lang in ("en", "es", "ca", "fr"):
                    for theme in ("light", "dark"):
                        page = browser.new_page(viewport={"width": width, "height": height})
                        errors = []
                        page.on("pageerror", lambda e: errors.append(str(e)))
                        page.goto("http://127.0.0.1:8962/index.html", wait_until="networkidle")
                        assert page.locator("#cmsToolbar").count() == 0, "Editor leaked into public view"
                        page.goto("http://127.0.0.1:8962/index.html?cms=edit", wait_until="networkidle")
                        assert page.locator("#cmsToolbar").count() == 1
                        assert page.evaluate("window.PortfolioCmsEditor.getEditableCount()") >= 100
                        page.locator("#lang" + lang.capitalize()).click()
                        if theme == "dark":
                            page.locator("#themeButton").click()
                        assert page.locator("#homeHeading").is_visible()
                        assert page.locator(".sidebar-nav a").count() == 6
                        assert page.locator(".accent-choice").count() == 4
                        original = page.locator("#heroEyebrow").inner_html()
                        page.locator("#heroEyebrow").click()
                        page.locator("#heroEyebrow").fill("Phase 2 test text")
                        print("EDIT DIAGNOSTIC", json.dumps(page.locator("#heroEyebrow").evaluate("(el) => ({text:el.innerText, html:el.innerHTML, editable:el.getAttribute(\'contenteditable\'), dirty:window.PortfolioCmsEditor.isDirty(), errors:[]})")), flush=True)
                        assert page.locator("#heroEyebrow").inner_text() == "Phase 2 test text"
                        assert page.evaluate("window.PortfolioCmsEditor.isDirty()")
                        page.locator(".cms-toggle").click()
                        assert page.locator("body.cms-preview").count() == 1
                        assert page.locator("#heroEyebrow").inner_text() == "Phase 2 test text"
                        page.locator(".cms-cancel").click()
                        assert page.locator("#heroEyebrow").inner_html() == original
                        assert not page.evaluate("window.PortfolioCmsEditor.isDirty()")
                        page.locator(".cms-toggle").click()
                        page.locator("#heroEyebrow").click()
                        page.locator("#heroEyebrow").fill("Stored draft")
                        page.locator(".cms-save").click()
                        assert not page.evaluate("window.PortfolioCmsEditor.isDirty()")
                        page.reload(wait_until="networkidle")
                        assert page.locator("#heroEyebrow").inner_text() == "Stored draft"
                        assert not errors, f"Page errors {lang}/{theme}/{width}: {errors}"
                        page.close()
                        print(f"PASS {width}px / {lang} / {theme}: editing, preview, cancel, draft persist, controls", flush=True)

            page = browser.new_page()
            page.goto("http://127.0.0.1:8962/index.html?cms=edit", wait_until="networkidle")
            page.locator("#heroEyebrow").click()
            page.locator("#heroEyebrow").fill("EN only")
            page.locator(".cms-save").click()
            page.locator("#langEs").click()
            assert page.locator("#heroEyebrow").inner_text() != "EN only"
            page.locator("#heroEyebrow").click()
            page.locator("#heroEyebrow").fill("ES only")
            page.locator(".cms-save").click()
            page.locator("#langEn").click()
            assert page.locator("#heroEyebrow").inner_text() == "EN only"
            draft = page.evaluate("window.PortfolioCmsEditor.getSavedDraft()")
            assert draft["translations"]["en"]["heroEyebrow"] == "EN only"
            assert draft["translations"]["es"]["heroEyebrow"] == "ES only"
            page.locator("#heroEyebrow").click()
            page.locator("#heroEyebrow").fill("<img src=x onerror=alert(1)>")
            page.locator(".cms-save").click()
            assert "<img" not in page.evaluate("window.PortfolioCmsEditor.getSavedDraft().translations.en.heroEyebrow")
            page.close()
            print("PASS language isolation and draft HTML sanitization", flush=True)
        finally:
            browser.close()
finally:
    server.shutdown()
