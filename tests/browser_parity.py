#!/usr/bin/env python3
"""Browser regression checks for original vs migrated portfolio (run in GitHub Actions)."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import io, json, subprocess, threading, sys, tempfile
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE="8a51574bd49bb8a28b5a2e8815cc48e491fd0f26"

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
def serve(directory,port):
 server=ThreadingHTTPServer(("127.0.0.1",port),partial(Quiet,directory=str(directory)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 return server

baseline=subprocess.check_output(["git","show",f"{BASE}:index.html"],cwd=ROOT)
results=[]
with tempfile.TemporaryDirectory() as temp:
 original=Path(temp)
 (original/"index.html").write_bytes(baseline)
 s0=serve(original,8960)
 s1=serve(ROOT,8961)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True)
   try:
    for width,height in [(1440,900),(390,844)]:
     for lang in ["en","es","ca","fr"]:
      for theme in ["light","dark"]:
       records=[]
       for port in [8960,8961]:
        page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
        errors=[]
        page.on("pageerror",lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{port}/index.html",wait_until="networkidle")
        if lang!="en": page.locator(f"#lang{lang.capitalize()}").click()
        if theme=="dark": page.locator("#themeButton").click()
        page.wait_for_timeout(150)
        data=page.evaluate("""() => ({
         text:document.querySelector('main').innerText,
         heading:document.querySelector('#homeHeading').innerHTML,
         lang:document.documentElement.lang,
         theme:document.documentElement.dataset.theme,
         accent:document.documentElement.dataset.accent,
         images:[...document.images].map(i=>({loaded:i.complete&&i.naturalWidth>0,w:i.naturalWidth,h:i.naturalHeight})),
         sections:[...document.querySelectorAll('main section[id]')].map(i=>i.id),
         links:[...document.querySelectorAll('.sidebar-nav a')].map(a=>a.getAttribute('href')),
         computed:[...document.querySelectorAll('h1,h2,.site-header,.sidebar')].map(el=>{const c=getComputedStyle(el);return [c.color,c.backgroundColor,c.fontSize,c.fontWeight,c.display]})
        })""")
        screenshot=np.asarray(Image.open(io.BytesIO(page.screenshot(full_page=True,animations="disabled"))).convert("RGB"),dtype=np.int16)
        records.append((data,screenshot,errors))
        page.close()
       old,new=records
       dom_equal=old[0]==new[0] and not old[2] and not new[2]
       pixels_diff=1.0 if old[1].shape!=new[1].shape else float(np.mean(np.any(np.abs(old[1]-new[1])>1,axis=2)))
       print(f"{width}px {lang} {theme}: DOM={dom_equal} pixel_diff={pixels_diff:.6f} errors={old[2]} {new[2]}",flush=True)
       results.append({"width":width,"lang":lang,"theme":theme,"dom_equal":dom_equal,"pixel_diff":pixels_diff,"errors_original":old[2],"errors_migrated":new[2]})
   finally:
    browser.close()
 finally:
  s0.shutdown();s1.shutdown()
(ROOT/"tests/browser-parity-results.json").write_text(json.dumps(results,indent=2)+"\n")
if not all(r["dom_equal"] and r["pixel_diff"]<0.01 for r in results):
 sys.exit("FAIL: browser parity differs from original in one or more configurations")
print("PASS: original vs migrated browser snapshots match in 16 language/viewport/theme configurations.")
