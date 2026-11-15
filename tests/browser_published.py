"""Exercise the committed v3 renderer and local-draft isolation in Chromium."""
import copy
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

from publisher.validation import validate

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = "**/cms/content/published.v3.json"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def exercise(browser, origin):
    page = browser.new_page()
    page.goto(origin + "/?cms=edit")
    page.locator("#cmsToolbar").wait_for()
    draft = page.evaluate("PortfolioCmsEditor.getDraft()")
    page.locator(".cms-content").click()
    page.locator(".cms-add-section").click()
    created = page.evaluate("PortfolioCmsEditor.getDraft()")
    custom = created["content"]["sections"][-1]
    custom_id = custom["id"]
    heading = next(key for key in created["content"]["fields"] if key.startswith(custom_id + ":"))
    draft["content"]["sections"].insert(1, custom)
    draft["content"]["sections"] = [s for s in draft["content"]["sections"] if s["id"] != "personal"]
    draft["content"]["fields"][heading] = {l: f"Published {l}" for l in ("en", "es", "ca", "fr")}
    draft["translations"]["en"]["aboutTitle"] = "Published about"
    snapshot = validate(json.dumps(draft).encode()).decode()
    page.evaluate("localStorage.setItem('oriol-cms-draft-v3', JSON.stringify(PortfolioCmsEditor.getDraft()))")

    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    for width in (1440, 820, 390):
        page.set_viewport_size({"width": width, "height": 900})
        page.route(SNAPSHOT, lambda route: route.fulfill(content_type="application/json", body=snapshot))
        page.goto(origin + "/#" + custom_id, wait_until="networkidle")
        assert page.locator("#cmsToolbar").count() == 0
        assert page.locator("#aboutTitle").inner_text() == "Published about"
        assert page.locator("main section[id]").nth(1).get_attribute("id") == custom_id
        assert page.locator("#personal").count() == 0
        for lang in ("es", "ca", "fr", "en"):
            page.locator("#lang" + lang.capitalize()).click()
            assert page.locator("#" + custom_id + " h2").inner_text() == f"Published {lang}"
        if width <= 980:
            page.locator("#menuButton").focus()
            page.keyboard.press("Enter")
            page.locator(f'.sidebar-nav a[href="#{custom_id}"]').click()
            assert page.locator("#menuButton").get_attribute("aria-expanded") == "false"
        page.unroute(SNAPSHOT)
    unsafe = copy.deepcopy(draft)
    unsafe["content"]["fields"][heading]["en"] = '<img src="missing" onerror="window.ran = true"><b>Clean</b>'
    page.route(SNAPSHOT, lambda route: route.fulfill(content_type="application/json", json=unsafe))
    page.goto(origin, wait_until="networkidle")
    assert page.locator("#" + custom_id + " h2").inner_text() == "Clean"
    assert page.evaluate("window.ran") is None
    page.unroute(SNAPSHOT)
    for invalid in ("broken JSON", '{"version":99}', '{"version":3,"content":null}'):
        page.route(SNAPSHOT, lambda route: route.fulfill(content_type="application/json", body=invalid))
        page.goto(origin, wait_until="networkidle")
        assert page.locator("#" + custom_id).count() == 0
        assert page.locator("#personal").count() == 1
        page.unroute(SNAPSHOT)
    assert not errors, errors
    print("PASS: published v3 content, 3 viewport widths, 4 locales, safe markup and invalid snapshot fallback")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.environ.get("CMS_BROWSER"))
            exercise(browser, f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
