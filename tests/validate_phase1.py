#!/usr/bin/env python3
"""Check that all Phase 1 changes are structural only."""
from pathlib import Path
import base64, hashlib, json, re, subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE='8a51574bd49bb8a28b5a2e8815cc48e491fd0f26'
original=subprocess.check_output(['git','show',f'{BASE}:index.html'],cwd=ROOT).decode('utf8')
html=(ROOT/'index.html').read_text(encoding='utf8')
style=re.search(r'<style\b[^>]*>(.*?)</style>',original,re.S|re.I)
script=re.search(r'<script\b[^>]*>(.*?)</script>',original,re.S|re.I)
assert style and script
assert (ROOT/'assets/site.css').read_text(encoding='utf8') == style.group(1)+'\n'
js=script.group(1)
start=js.index('    const translations = {')
end=js.index('    // Apply visual identities',start)
expected_js=js[:start]+'    const translations = window.PortfolioTranslations;\n\n'+js[end:]+'\n'
assert (ROOT/'assets/site.js').read_text(encoding='utf8') == expected_js

# All images are identical binary content in exactly the original order.
image_data=re.findall(r'src="data:image/(png|jpeg|gif|webp|svg\+xml);base64,([^"]+)"',original,re.I)
manifest=json.loads((ROOT/'cms/assets-manifest.json').read_text(encoding='utf8'))
assert len(image_data)==len(manifest)==20
for (mime,payload),item in zip(image_data,manifest):
    blob=base64.b64decode(payload,validate=True)
    assert (ROOT/item['path']).read_bytes()==blob
    assert item['sha256']==hashlib.sha256(blob).hexdigest()
    assert item['mime']==f'image/{mime.lower()}'

# Every HTML byte is unchanged, except for external asset references.
normalized=html.replace('<link rel="stylesheet" href="./assets/site.css">',style.group(0),1)
normalized=normalized.replace('<script src="./cms/content/translations.js"></script>\n  <script src="./assets/site.js"></script>',script.group(0),1)
for item,(mime,payload) in zip(manifest,image_data):
    normalized=normalized.replace(f'src="./{item["path"]}"',f'src="data:image/{mime};base64,{payload}"',1)
assert normalized==original, 'Unexpected HTML changes'

translations=json.loads((ROOT/'cms/content/translations.json').read_text(encoding='utf8'))
expression=js[start:end]
node=subprocess.run(['node','-e',"const vm=require('node:vm');let s='';process.stdin.on('data',b=>s+=b);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(vm.runInNewContext(s+String.fromCharCode(10)+'translations'))))"],input=expression,text=True,capture_output=True,check=True)
assert json.loads(node.stdout)==translations
assert set(translations)=={'en','es','ca','fr'}
assert all(len(translations[lang])==100 for lang in translations)
print('PASS: HTML unchanged; CSS and JS preserved; 20 binary-identical images; 400 identical translation values.')
