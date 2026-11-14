"""Real browser integration checks for Phase 3; no simulated DOM."""
import json, threading
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from jsonschema import validate

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results'; OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8963),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
URL='http://127.0.0.1:8963/index.html?cms=edit'
def close_panel(page):
    if page.locator('#cmsInspector').is_visible(): page.get_by_role('button',name='Close',exact=True).click()
def select(page,selector):
    close_panel(page)
    page.locator(selector).click()
def apply(page): page.locator('.cms-apply').click()
try:
  with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path=__import__('os').environ.get('CMS_BROWSER'))
    for width in [1440,390]:
      page=browser.new_page(viewport={'width':width,'height':900})
      errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
      page.on('dialog',lambda d:d.accept())
      try:
        page.goto(URL,wait_until='networkidle')
        assert page.locator('#cmsToolbar').count()==1
        # Edit a real link, with locale-aware rich text and image attributes.
        select(page,'#edu1Title')
        page.get_by_label('Link destination',exact=True).fill('https://example.com/degree')
        apply(page)
        assert page.locator('#edu1Title').get_attribute('href')=='https://example.com/degree'
        select(page,'#education img >> nth=0')
        replacement='./assets/images/image-15-fecf4ad3f372.png'
        page.get_by_label('Image URL (or choose a file)').fill(replacement)
        page.get_by_label('Alternative text').fill('Updated image')
        apply(page)
        assert page.locator('#education img').first.get_attribute('src').endswith(replacement[1:])
        assert page.locator('#education img').first.get_attribute('alt')=='Updated image'
        close_panel(page)
        page.locator('.cms-content').click()
        page.locator('[data-section="education"] .cms-add-entry').click()
        assert page.locator('#education .timeline-item').count()==7
        new=page.locator('#education [data-cms-new]').last
        new_id=new.get_attribute('data-cms-entry')
        close_panel(page)
        new.locator('h3').click()
        page.locator('.cms-rich').fill('New qualification')
        apply(page)
        assert new.locator('h3').text_content()=='New qualification'
        for lang in ['es','ca','fr','en']:
          page.locator('#lang'+lang.capitalize()).click()
          if lang!='en':
            assert new.locator('h3').text_content()==''
            close_panel(page);new.locator('h3').click()
            page.locator('.cms-rich').fill('Qualification '+lang);apply(page)
          else: assert new.locator('h3').text_content()=='New qualification'
        # Shared structural order, stable identities and generated navigation.
        page.locator('[data-entry="'+new_id+'"] button[aria-label="Move entry up"]').click()
        assert page.locator('#education .timeline-item').nth(5).get_attribute('data-cms-entry')==new_id
        page.locator('.cms-add-section').click()
        assert page.locator('.sidebar-nav a').count()==7
        new_section=page.locator('section[data-cms-new]').last
        section_id=new_section.get_attribute('id')
        page.locator('[data-section="'+section_id+'"] button[aria-label="Move section up"]').click()
        assert page.locator('.sidebar-nav a').nth(5).get_attribute('href')=='#'+section_id
        assert page.locator('.sidebar-nav .num').all_text_contents()==['00','01','02','03','04','05','06']
        ids=page.locator('[id]').evaluate_all('(els)=>els.map(el=>el.id)')
        assert len(ids)==len(set(ids))
        page.locator('.cms-save').click()
        draft=page.evaluate('PortfolioCmsEditor.getDraft()')
        validate(draft,json.loads((ROOT/'cms/content.schema.json').read_text()))
        page.reload(wait_until='networkidle')
        draft=page.evaluate('PortfolioCmsEditor.getSavedDraft()')
        assert page.locator('#education .timeline-item').count()==7
        assert page.locator('.sidebar-nav a').count()==7
        assert page.locator('#edu1Title').get_attribute('href')=='https://example.com/degree'
        page.locator('.cms-content').click()
        page.locator('[data-entry="'+new_id+'"] button').filter(has_text='Delete').click()
        assert page.locator('#education .timeline-item').count()==6
        page.locator('.cms-cancel').click()
        assert page.locator('#education .timeline-item').count()==7
        assert not page.locator('#cmsInspector').is_visible()
        assert page.locator('[contenteditable=true]').count()==0
        # Preview retains original theme/accent controls and auto-scroll.
        page.locator('#themeButton').click()
        assert page.locator('html').get_attribute('data-theme')=='dark'
        for accent in ['blue','red','orange','purple']:
          page.locator('[data-choice="'+accent+'"]').click()
          assert page.locator('html').get_attribute('data-accent')==accent
        page.evaluate('scrollTo(0,0)');page.locator('#autoScrollButton').click()
        page.wait_for_timeout(400)
        assert page.locator('#autoScrollButton').get_attribute('aria-pressed')=='true'
        assert page.evaluate('scrollY')>0
        page.locator('#autoScrollButton').click()
        if width==390:
          page.locator('#menuButton').click()
          page.locator('.sidebar-nav a[href="#'+section_id+'"]').click()
          assert 'sidebar-open' not in page.locator('body').get_attribute('class')
        page.locator('.cms-toggle').click()
        with page.expect_download() as download:
          page.locator('.cms-export').click()
        exported=json.loads(Path(download.value.path()).read_text())
        assert exported==draft
        page.locator('#cmsToolbar input[type=file]').set_input_files({'name':'restore.json','mimeType':'application/json','buffer':json.dumps(exported).encode()})
        assert page.locator('#education .timeline-item').count()==7
        assert not errors, errors
        close_panel(page)
        page.screenshot(path=str(OUT/f'phase3-{width}.png'),full_page=True)
        print(f'PASS {width}: links, images, entries, ordering, navigation, locales, persistence, cancel, preview, theme, accents, scroll, export/import',flush=True)
      except Exception:
        page.screenshot(path=str(OUT/f'failure-{width}.png'),full_page=True)
        print('PAGE ERRORS',errors,flush=True)
        raise
      finally: page.close()
    # Legacy drafts migrate without replacing the original backup.
    page=browser.new_page();page.goto(URL)
    legacy={'version':1,'translations':{'en':{'heroEyebrow':'Legacy draft'},'es':{},'ca':{},'fr':{}},'static':{}}
    page.evaluate('(value)=>localStorage.setItem("oriol-cms-draft-v1",JSON.stringify(value))',legacy)
    page.reload();assert page.locator('#heroEyebrow').text_content()=='Legacy draft'
    assert page.evaluate('PortfolioCmsEditor.getDraft().version')==3
    assert page.evaluate('localStorage.getItem("oriol-cms-draft-v1")')
    page.close()
    page=browser.new_page();page.goto(URL)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    dialogs=[];page.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
    select(page,'#accDesc')
    page.locator('.cms-rich').fill('Rich content')
    page.locator('.cms-rich').select_text()
    page.get_by_role('button',name='bold',exact=True).click()
    apply(page)
    assert page.locator('#accDesc b,#accDesc strong').text_content()=='Rich content'
    select(page,'#experience .entry-org a >> nth=0')
    page.get_by_role('button',name='+ Link',exact=True).click()
    page.get_by_label('Link label').fill('Portfolio link')
    page.get_by_label('Link destination').fill('https://example.com/project')
    page.get_by_role('button',name='Add link',exact=True).click()
    assert page.locator('[data-cms-added-link]').text_content()=='Portfolio link'
    select(page,'[data-cms-added-link]')
    page.get_by_role('button',name='Delete link',exact=True).click()
    assert page.locator('[data-cms-added-link]').count()==0
    select(page,'#education img >> nth=0')
    page.get_by_label('Upload PNG / JPEG / WebP / GIF').set_input_files(str(ROOT/'assets/images/image-15-fecf4ad3f372.png'))
    page.wait_for_function('document.querySelector("#cmsInspector input").value.startsWith("data:image/")')
    apply(page)
    assert page.locator('#education img').first.get_attribute('src').startswith('data:image/png;base64,')
    page.locator('.cms-save').click()
    saved=page.evaluate('PortfolioCmsEditor.getSavedDraft()')
    bad=json.loads(json.dumps(saved));bad['content']['sections'].append(bad['content']['sections'][0])
    page.locator('#cmsToolbar input[type=file]').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':json.dumps(bad).encode()})
    page.wait_for_timeout(100)
    assert any('duplicate' in msg for msg in dialogs)
    assert page.evaluate('PortfolioCmsEditor.getDraft()')==saved
    bad=json.loads(json.dumps(saved));bad['content']['attributes']['home:home']={'href':'javascript:alert(1)'}
    page.locator('#cmsToolbar input[type=file]').set_input_files({'name':'unsafe.json','mimeType':'application/json','buffer':json.dumps(bad).encode()})
    page.wait_for_timeout(100)
    assert any('Unsafe' in msg for msg in dialogs)
    assert page.evaluate('PortfolioCmsEditor.getDraft()')==saved
    close_panel(page);page.locator('.cms-content').click()
    page.locator('[data-section="personal"] button').filter(has_text='Delete').click()
    assert page.locator('#personal').count()==0
    assert page.locator('.sidebar-nav a[href="#personal"]').count()==0
    page.locator('.cms-cancel').click()
    assert page.locator('#personal').count()==1
    assert not errors,errors
    print('PASS rich formatting, added/deleted links, image upload, invalid/unsafe import rejection, section deletion/cancel and legacy migration',flush=True)
    browser.close()
finally: server.shutdown()
