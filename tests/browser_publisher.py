"""Use Chromium and the real editor/publisher on loopback with a GitHub API double."""
import os
import re
import sys
import threading
from dataclasses import replace
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from wsgiref.simple_server import WSGIRequestHandler, make_server

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publisher.app import Publisher
from test_publisher import FakeGitHub


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *_args):
        pass


def exercise(page, context, origin, github):
    page.goto(origin + '/?cms=edit')
    page.locator('#home [data-cms-key]').first.click()
    page.locator('[contenteditable="true"]').first.fill('Draft reviewed in Chromium')
    page.locator('.cms-save').click()
    page.locator('.cms-publish').click()
    dialog = page.get_by_role('dialog', name='Publish draft to development')
    status = dialog.get_by_role('status')
    dialog.get_by_role('button', name='Connect GitHub').click()
    authorize = dialog.get_by_role('link', name='Authorize on GitHub')
    expect(authorize).to_be_visible()
    state = parse_qs(urlsplit(authorize.get_attribute('href')).query)['state'][0]
    tab = context.new_page()
    tab.goto(origin + '/auth/callback?' + urlencode({'state': state, 'code': 'fixture-code'}))
    assert tab.url.endswith('/auth/connected')
    tab.close()
    dialog.get_by_role('button', name='Check connection').click()
    expect(status).to_contain_text('Connected as account')
    review = dialog.get_by_role('button', name='Review current draft')
    confirm = dialog.get_by_role('button', name='Confirm development publish')
    review.click()
    expect(confirm).to_be_visible()
    assert not github.commits
    dialog.locator('summary').click()
    expect(dialog.locator('pre')).to_contain_text('Draft reviewed in Chromium')
    dialog.get_by_role('button', name='Close').click()
    expect(page.locator('body')).to_have_class(re.compile(r'cms-preview'))
    page.locator('.cms-publish').click()
    github.race = True
    confirm.click()
    expect(status).to_contain_text('branch changed')
    assert not github.commits
    github.race = False
    review.click()
    confirm.click()
    expect(dialog.get_by_role('link', name='Open GitHub commit')).to_be_visible()
    assert len(github.commits) == 1 and b'Draft reviewed in Chromium' in github.commits[0]
    assert 'Draft reviewed in Chromium' in page.evaluate("localStorage.getItem('oriol-cms-draft-v3')")
    dialog.get_by_role('button', name='Disconnect').click()
    expect(status).to_have_text('GitHub disconnected.')
    expect(confirm).to_be_hidden()


def main():
    for width, height in ((1440, 900), (390, 844)):
        git = FakeGitHub()
        with make_server('127.0.0.1', 0, lambda *_: None, handler_class=QuietHandler) as server:
            origin = f'http://127.0.0.1:{server.server_port}'
            server.set_app(Publisher(replace(git.config, origin=origin), git))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(executable_path=os.getenv('CMS_BROWSER') or None)
                    context = browser.new_context(viewport={'width': width, 'height': height})
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    exercise(page, context, origin, git)
                    assert not errors, errors
                    browser.close()
            finally:
                server.shutdown()
                thread.join()
        print(f'PASS: authenticated draft review, conflict, commit and disconnect at {width}px.')


if __name__ == '__main__':
    main()
