/* Trusted component templates and locale-aware draft data. */
function portfolioCmsSafeURL(value, image) {
  if (typeof value !== 'string' || !value || /\s|[\u0000-\u001f\u007f\\]/.test(value)) return false;
  if (image && /^data:image\/(png|jpeg|webp|gif);base64,[a-z0-9+/]+={0,2}$/i.test(value)) return value.length < 2800000;
  if (value.length > 4096) return false;
  if (/^https?:\/\//i.test(value)) {
    try { const url = new URL(value); return !!url.hostname && !url.username && !url.password; }
    catch (_) { return false; }
  }
  return /^(?:\.\/|\.\.\/|\/(?!\/)|assets\/)/i.test(value) || (!image && /^(?:mailto:.+|tel:.+|#.*)$/i.test(value));
}

window.PortfolioCmsAdvanced = function (bridge) {
  'use strict';
  const locales = bridge.locales, clone = x => JSON.parse(JSON.stringify(x));
  const sectionNodes = new Map(), entryNodes = new Map(), targets = new Map();
  const templates = Object.create(null), base = {sections: [], fields: {}, attributes: {}, links: []};
  const entrySelector = '.timeline-item,.experience-item,.feature-card,.interest';
  let selected = null, editing = true, panel, selectionLabel, form, tree, missing;
  const uid = () => 'cms-' + crypto.randomUUID();
  const locale = () => bridge.language();
  const t = (label) => portfolioCmsText(label);
  const localizedControls = new Map();
  const model = () => bridge.get().content;
  const localized = text => Object.fromEntries(locales.map(l => [l, l === locale() ? text : '']));
  const safeURL = portfolioCmsSafeURL;
  function register(root, prefix, fresh) {
    const list = [root, ...root.querySelectorAll('*')];
    list.forEach((el, i) => {
      if (el.closest('[data-cms-ui],.brand-word')) return;
      let walk=el; const route=[];
      while(walk!==root){route.unshift([...walk.parentElement.children].filter(n=>!n.classList.contains('brand-word')).indexOf(walk));walk=walk.parentElement;}
      const key = prefix + ':' + (!fresh && el.id ? el.id : route.join('.'));
      el.dataset.cmsRef = key;
      const anchor=el.closest('[id]'); const path=[]; let cursor=el;
      while(anchor && cursor!==anchor){path.unshift([...cursor.parentElement.children].indexOf(cursor));cursor=cursor.parentElement;}
      targets.set(key, {el, anchor: fresh ? null : anchor?.id, path, html:el.innerHTML, href: el.getAttribute('href'), src: el.getAttribute('src'), alt: el.getAttribute('alt')});
      if (fresh) { el.removeAttribute('id'); el.removeAttribute('data-cms-key'); }
    });
  }
  document.querySelectorAll('main section[id]').forEach(section => {
    const item = {id: section.id, template: section.id, entries: []};
    sectionNodes.set(item.id, section);
    section.querySelectorAll(entrySelector).forEach((entry, i) => {
      const id = section.id + '-entry-' + i;
      entry.dataset.cmsEntry = id;
      entryNodes.set(id, entry);
      item.entries.push({id, template: id});
      templates[id] = entry.cloneNode(true);
    });
    base.sections.push(item);
    register(section, section.id, false);
  });
  // Also support header, sidebar, footer and the scrolling character image.
  ['.site-header', '.sidebar', '.footer', '#autoScrollButton'].forEach((s,i) => {
    const el = document.querySelector(s); if (el) register(el, 'chrome-' + i, false);
  });
  const originalNav = new Map([...document.querySelectorAll('.sidebar-nav a')].map(a => [a.hash.slice(1),a]));
  const containers = new Map();
  base.sections.forEach(s => { if (s.entries.length) containers.set(s.id, entryNodes.get(s.entries[0].id).parentElement); });
  let observer;
  function normalize(input) {
    if (!input) return clone(base);
    if (!Array.isArray(input.sections) || input.sections.length > 60) throw new Error('Invalid sections');
    const out = clone(base), used = new Set();
    const validId = id => typeof id === 'string' && /^[a-z][a-z0-9_-]{0,90}$/.test(id);
    const claim = id => { if (!validId(id) || used.has(id)) throw new Error('Invalid or duplicate ID'); used.add(id); };
    out.sections = input.sections.map(s => {
      claim(s.id);
      const old = base.sections.find(x => x.id === s.id);
      if (!old && (!s.id.startsWith('cms-') || s.template !== 'custom')) throw new Error('Unknown section');
      if (!Array.isArray(s.entries) || s.entries.length > 150) throw new Error('Invalid entries');
      if (old && (s.template !== old.template || !containers.has(old.id) && s.entries.length)) throw new Error('Invalid section template');
      return {id:s.id, template:old ? old.template : 'custom', entries:s.entries.map(e => {
        claim(e.id);
        if (!templates[e.template]) throw new Error('Unknown component');
        const originalEntry = base.sections.flatMap(x=>x.entries).find(x=>x.id===e.id);
        if (originalEntry && (originalEntry.template !== e.template || !old || !old.entries.some(x=>x.id===e.id))) throw new Error('Invalid original entry');
        if (!originalEntry && !e.id.startsWith('cms-')) throw new Error('Invalid new entry');
        return {id:e.id, template:e.template};
      })};
    });
    if (!out.sections.some(s=>s.id==='home')) throw new Error('Home is required');
    out.fields = {};
    Object.entries(input.fields || {}).forEach(([key, values]) => {
      if (!/^[a-z][a-z0-9_-]*:[a-zA-Z0-9_.-]*$/.test(key) || key.length > 200 || !values || typeof values !== 'object') throw new Error('Invalid field');
      out.fields[key] = {};
      locales.forEach(l => { if (typeof values[l] === 'string' && values[l].length < 100000) out.fields[key][l] = bridge.sanitize(values[l]); });
    });
    out.attributes = {};
    Object.entries(input.attributes || {}).forEach(([key, attrs]) => {
      if (!/^[a-z][a-z0-9_-]*:[a-zA-Z0-9_.-]*$/.test(key) || key.length > 200) throw new Error('Invalid field');
      const a = {};
      if (attrs.href !== undefined) { if (!safeURL(attrs.href,false)) throw new Error('Unsafe link'); a.href = attrs.href; }
      if (attrs.src !== undefined) { if (!safeURL(attrs.src,true)) throw new Error('Unsafe image'); a.src = attrs.src; }
      if (attrs.alt) a.alt = Object.fromEntries(locales.map(l => [l, String(attrs.alt[l] || '').slice(0,1000)]));
      if (attrs.removed === true) a.removed = true;
      out.attributes[key] = a;
    });
    out.links = (input.links || []).map(x => {
      claim(x.id);
      if (!x.id.startsWith('cms-') || typeof x.owner !== 'string' || !safeURL(x.href,false)) throw new Error('Invalid link');
      return {id:x.id,owner:x.owner,href:x.href,label:Object.fromEntries(locales.map(l=>[l,String((x.label || {})[l] || '').slice(0,500)]))};
    });
    if (out.links.length > 300) throw new Error('Too many links');
    return out;
  }
  function textTargets(root) {
    return [...root.querySelectorAll('h2,h3,p,strong,.entry-meta,.entry-org,.category-pill')].filter(el =>
      !el.parentElement.closest('h2,h3,p,strong,.entry-meta,.entry-org,.category-pill') && !el.querySelector('img,svg'));
  }
  function createEntry(e) {
    const el = templates[e.template].cloneNode(true);
    el.dataset.cmsEntry = e.id; el.dataset.cmsNew = '';
    textTargets(el).forEach(t => { t.innerHTML = ''; });
    el.querySelectorAll('img').forEach(img => { img.removeAttribute('src'); img.alt = ''; });
    el.querySelectorAll('a').forEach(a=>a.removeAttribute('href'));
    register(el,e.id,true);
    entryNodes.set(e.id,el);
    return el;
  }
  function structure() {
    const m = model(), page = document.querySelector('.footer').parentElement;
    const visible = new Set(m.sections.map(s=>s.id));
    sectionNodes.forEach((node,id) => { if (!visible.has(id)) node.remove(); });
    m.sections.forEach(s => {
      let section = sectionNodes.get(s.id);
      if (!section) {
        section = document.createElement('section'); section.className='content-section';
        section.innerHTML='<div class="section-heading"><span class="section-index"></span><h2></h2></div><div class="section-intro"><p></p></div><div class="cms-entry-list"></div>';
        section.dataset.cmsNew=''; register(section,s.id,true); section.id=s.id;
        sectionNodes.set(s.id,section); containers.set(s.id,section.querySelector('.cms-entry-list'));
      }
      page.insertBefore(section,page.querySelector('.footer'));
      const container=containers.get(s.id);
      if (container) {
        [...container.children].filter(el=>el.matches(entrySelector)).forEach(el=>el.remove());
        s.entries.forEach(e=>container.append(entryNodes.get(e.id) || createEntry(e)));
      }
    });
  }
  function render() {
    const m=model();
    targets.forEach((target,key) => {
      let {el,href,src,alt}=target;
      if(!el.isConnected && target.anchor && !el.closest('[data-cms-entry]')){
        let live=document.getElementById(target.anchor);target.path.forEach(i=>live=live?.children[i]);
        if(live && live.tagName===el.tagName){el=live;target.el=live;live.dataset.cmsRef=key;}
      }
      const values=m.fields[key];
      const canText=el.matches('[data-cms-key],h2,h3,p,strong,.entry-meta,.entry-org,.category-pill,a,span') && !el.querySelector('img,svg,button,.num,[data-cms-key]');
      if (values && canText && Object.hasOwn(values,locale())) {el.innerHTML=bridge.sanitize(values[locale()]);target.painted=true;}
      else if(target.painted && !el.hasAttribute('data-cms-key') && !el.closest('[data-cms-new]')) {el.innerHTML=target.html;target.painted=false;}
      else if(el.closest('[data-cms-new]') && el.matches('h2,h3,p,strong,.entry-meta,.entry-org,.category-pill')) el.innerHTML='';
      if (el.matches('a')) { el.hidden=false; if (href === null) el.removeAttribute('href'); else el.setAttribute('href',href); }
      if (el.matches('img')) { if(src===null) el.removeAttribute('src'); else el.setAttribute('src',src); el.alt=alt || ''; }
      const a=m.attributes[key];
      if(a) {
        if(el.matches('a') && a.href) el.setAttribute('href',a.href);
        if(el.matches('a') && a.removed) el.hidden=true;
        if(el.matches('img')) { if(a.src) el.src=a.src; if(a.alt) el.alt=a.alt[locale()] || ''; }
      }
    });
    document.querySelectorAll('[data-cms-added-link]').forEach(el=>el.remove());
    m.links.forEach(link=>{
      const owner=targets.get(link.owner)?.el;
      if(!owner?.isConnected || !owner.matches('.entry-org,.contact-links,.hero-contacts,.quick-links')) return;
      const a=document.createElement('a'); a.dataset.cmsAddedLink=link.id; a.href=link.href; a.textContent=link.label[locale()] || '…';
      owner.append(a);
    });
    navigation();
    localizedControls.forEach((label, el) => { el.textContent = t(label); });
    if (panel) panel.setAttribute('aria-label', t('Content manager'));
    refreshTree();
    if(selected && !panel?.hidden && selected.isConnected) select(selected);
  }
  function navigation() {
    const nav=document.querySelector('.sidebar-nav'), m=model();
    const changed=JSON.stringify(m.sections.map(s=>s.id))!==JSON.stringify(base.sections.map(s=>s.id));
    if(changed) {
      nav.replaceChildren();
      m.sections.forEach((s,i)=>{
        let a=originalNav.get(s.id);
        if(!a) { a=document.createElement('a'); a.href='#'+s.id; a.innerHTML='<span class="num"></span> <span></span>'; }
        a.querySelector('.num').textContent=String(i).padStart(2,'0');
        if(!originalNav.has(s.id)) a.lastElementChild.textContent=sectionNodes.get(s.id).querySelector('h2').textContent || '…';
        nav.append(a);
        const index=sectionNodes.get(s.id).querySelector('.section-index'); if(index) index.textContent=String(i).padStart(2,'0');
      });
    } else {
      nav.replaceChildren(...base.sections.map(s=>originalNav.get(s.id)));
      base.sections.forEach((s,i)=>{ originalNav.get(s.id).querySelector('.num').textContent=String(i).padStart(2,'0'); const n=sectionNodes.get(s.id).querySelector('.section-index'); if(n)n.textContent=String(i).padStart(2,'0'); });
    }
    const existing = new Set(m.sections.map(s => s.id));
    document.querySelectorAll('.top-nav a,.quick-links a,.sidebar a[href^="#"]').forEach(a=>{
      const anchor = a.getAttribute('href');
      if (anchor?.startsWith('#') && base.sections.some(s => '#'+s.id === anchor) && !existing.has(anchor.slice(1))) a.hidden = true;
    });
    if(observer) observer.disconnect();
    observer=new IntersectionObserver(entries=>{
      entries.forEach(e=>{ if(!e.isIntersecting) return; nav.querySelectorAll('a').forEach(a=>{ const on=a.hash==='#'+e.target.id; a.classList.toggle('active',on); if(on)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current'); }); });
    },{rootMargin:'-15% 0px -65% 0px'});
    m.sections.forEach(s=>observer.observe(sectionNodes.get(s.id)));
  }
  function button(label, action, parent, cls, literal = false) {
    const b=document.createElement('button'); b.type='button'; b.textContent=literal ? label : t(label); if(cls)b.className=cls;
    b.addEventListener('click',action); parent.append(b); return b;
  }
  function change(action) { bridge.finish(); action(); bridge.change(); }
  function move(array,id,delta) { const i=array.findIndex(x=>x.id===id), j=i+delta; if(j>=0 && j<array.length) [array[i],array[j]]=[array[j],array[i]]; }
  function refreshTree() {
    if(!tree) return;
    tree.replaceChildren();
    model().sections.forEach(s=>{
      const row=document.createElement('div'); row.className='cms-tree-row'; row.dataset.section=s.id;
      button(sectionNodes.get(s.id).querySelector('h1,h2')?.textContent || t('Untitled section'),()=>select(sectionNodes.get(s.id).querySelector('h1,h2')),row,undefined,true);
      button('↑',()=>change(()=>move(model().sections,s.id,-1)),row).ariaLabel=t('Move section up');
      button('↓',()=>change(()=>move(model().sections,s.id,1)),row).ariaLabel=t('Move section down');
      if(s.id!=='home') button('Delete',()=>{ if(confirm(t('Delete this section from the draft?')))change(()=>model().sections=model().sections.filter(x=>x.id!==s.id)); },row);
      if(containers.has(s.id)) button('+ Entry',()=>addEntry(s),row,'cms-add-entry');
      tree.append(row);
      s.entries.forEach(e=>{
        const r=document.createElement('div');r.className='cms-tree-row cms-tree-entry';r.dataset.entry=e.id;
        const node=entryNodes.get(e.id);
        button(node.querySelector('h3,strong')?.textContent || t('Untitled entry'),()=>{node.scrollIntoView({block:'center'}); select(node.querySelector('h3,strong'));},r,undefined,true);
        button('↑',()=>change(()=>move(s.entries,e.id,-1)),r).ariaLabel=t('Move entry up');
        button('↓',()=>change(()=>move(s.entries,e.id,1)),r).ariaLabel=t('Move entry down');
        button('Delete',()=>{if(confirm(t('Delete this entry from the draft?')))change(()=>s.entries=s.entries.filter(x=>x.id!==e.id));},r);
        tree.append(r);
      });
    });
  }
  function addEntry(s) {
    change(()=>{
      const template=s.entries[0]?.template || (s.id==='education'?'education-entry-1':s.id==='personal'?'personal-entry-0':'experience-entry-0');
      const e={id:uid(),template};s.entries.push(e);
      const el=createEntry(e), title=el.querySelector('h3,strong');
      model().fields[title.dataset.cmsRef]=localized(t('New entry'));
    });
  }
  function field(label,value,multiline=false) {
    const wrap=document.createElement('label');wrap.textContent=t(label);
    const input=document.createElement(multiline?'textarea':'input');input.value=value || '';wrap.append(input);form.append(wrap);return input;
  }
  function select(el) {
    if(!el || !panel) return;
    selected=el; panel.hidden=false;
    document.querySelectorAll('.cms-selected').forEach(x=>x.classList.remove('cms-selected'));el.classList.add('cms-selected');
    form.replaceChildren();
    selectionLabel.textContent=t('Selected')+' · '+locale().toUpperCase();
    const key=el.dataset.cmsRef, img=el.matches('img'), link=el.closest('a');
    const editableText=!img && !el.querySelector('svg,img,input,button') && !el.matches('section,#footerCopy');
    const value=editableText ? field('Text / rich text',el.innerHTML,true):null;
    if(value) {
      const preview=document.createElement('div');preview.className='cms-rich';preview.contentEditable='true';preview.setAttribute('role','textbox');preview.setAttribute('aria-multiline','true');preview.setAttribute('aria-label',t('Text / rich text'));preview.innerHTML=bridge.sanitize(value.value);form.append(preview);value.hidden=true;
      preview.addEventListener('input',()=>{value.value=bridge.sanitize(preview.innerHTML);});
      ['bold','italic','insertParagraph','insertLineBreak'].forEach(cmd=>button(cmd,()=>{preview.focus();document.execCommand(cmd);value.value=bridge.sanitize(preview.innerHTML);},form));
      button('Insert link',()=>{const url=prompt(t('Link URL'));if(url && safeURL(url,false)){preview.focus();document.execCommand('createLink',false,url);value.value=bridge.sanitize(preview.innerHTML);}},form);
    }
    const href=link ? field('Link destination',link.getAttribute('href')):null;
    const src=img ? field('Image URL (or choose a file)',el.getAttribute('src')):null;
    const alt=img ? field('Alternative text',el.alt):null;
    if(img) {
      const file=field('Upload PNG / JPEG / WebP / GIF','');file.type='file';file.accept='image/png,image/jpeg,image/webp,image/gif';
      file.addEventListener('change',()=>{const f=file.files[0];if(!f)return;if(f.size>2000000 || !/^image\/(png|jpeg|webp|gif)$/.test(f.type)){alert(t('Choose an image under 2 MB.'));return;}const reader=new FileReader();reader.onload=()=>{src.value=reader.result;};reader.readAsDataURL(f);});
    }
    const pending=locales.filter(l=> {
      if(model().fields[key]) return !model().fields[key][l];
      return el.closest('[data-cms-new]')!==null;
    });
    missing.textContent = pending.length ? t('Missing translations') + ' · ' + pending.join(', ').toUpperCase() : '';
    if (img && (!src.value || !alt.value)) missing.textContent += ' ' + t('Missing image URL or alternative text.');
    button('Apply',()=>{
      if(href && !safeURL(href.value,false) || src && !safeURL(src.value,true)) {alert(t('Use a valid HTTP(S), relative image URL, mailto, tel or page anchor.'));return;}
      change(()=>{
        if(el.dataset.cmsAddedLink) {const added=model().links.find(l=>l.id===el.dataset.cmsAddedLink);added.label[locale()]=value.value;added.href=href.value;}
        else {
          if(value) model().fields[key]={...(model().fields[key] || {}),[locale()]:bridge.sanitize(value.value)};
          if(href) {const k=link.dataset.cmsRef;model().attributes[k]={...model().attributes[k],href:href.value};}
        }
        if(src) model().attributes[key]={...model().attributes[key],src:src.value,alt:{...(model().attributes[key]?.alt || {}),[locale()]:alt.value}};
      });
      select(el);
    },form,'cms-apply');
    const owner=el.closest('.entry-org,.contact-links,.hero-contacts,.quick-links') || el.closest(entrySelector)?.querySelector('.entry-org');
    if(owner) button('+ Link',()=>{
      form.replaceChildren();const label=field('Link label',''),url=field('Link destination','https://');
      button('Add link',()=>{if(!safeURL(url.value,false)){alert(t('Invalid URL'));return;}change(()=>model().links.push({id:uid(),owner:owner.dataset.cmsRef,href:url.value,label:localized(label.value)}));select(owner);},form);
    },form);
    if(el.dataset.cmsAddedLink) button('Delete link',()=>change(()=>model().links=model().links.filter(l=>l.id!==el.dataset.cmsAddedLink)),form);
    else if(link && !link.closest('.sidebar-nav,.top-nav,.quick-links,.footer-links')) button('Delete link',()=>{
      if(confirm(t('Remove this link from the draft?')))change(()=>model().attributes[link.dataset.cmsRef]={...model().attributes[link.dataset.cmsRef],removed:true});
    },form);
  }
  function mount(actions) {
    panel=document.createElement('aside');panel.id='cmsInspector';panel.dataset.cmsUi='';panel.hidden=true;panel.setAttribute('aria-label','Content manager');
    const heading=document.createElement('h2');heading.textContent=t('Content manager');panel.append(heading);localizedControls.set(heading,'Content manager');
    const fixed = (label, action, parent, cls) => localizedControls.set(button(label, action, parent, cls), label);
    fixed('Close',()=>panel.hidden=true,panel,'cms-inspector-close');
    selectionLabel=document.createElement('h3');panel.append(selectionLabel);
    missing=document.createElement('p');missing.className='cms-missing';panel.append(missing);
    form=document.createElement('div');panel.append(form);
    fixed('+ Section',()=>change(()=>{const id=uid();model().sections.push({id,template:'custom',entries:[]});structure();const h=sectionNodes.get(id).querySelector('h2');model().fields[h.dataset.cmsRef]=localized(t('New section'));}),panel,'cms-add-section');
    tree=document.createElement('div');panel.append(tree);document.body.append(panel);
    fixed('Content',()=>{panel.hidden=!panel.hidden;refreshTree();},actions,'cms-content');
    fixed('Export JSON',()=>{
      const blob=new Blob([JSON.stringify(bridge.getDraft(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='portfolio-draft.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    },actions,'cms-export');
    const input=document.createElement('input');input.type='file';input.accept='.json,application/json';input.hidden=true;actions.append(input);
    input.addEventListener('change',async()=>{try {const f=input.files[0];if(!f)return;if(f.size>12000000)throw new Error('File too large');const value=JSON.parse(await f.text());if(![1,3].includes(value.version))throw new Error('Unsupported draft version');normalize(value.content);bridge.importDraft(value);}catch(e){alert(t('Import failed. Check the JSON file and its version.'));}finally{input.value='';}});
    fixed('Import JSON',()=>input.click(),actions,'cms-import');
    document.addEventListener('click',event=>{
      if(!editing || event.target.closest('[data-cms-ui],#cmsToolbar,.lang-switch,.accent-picker,summary') || event.target.closest('button') && !event.target.matches('img'))return;
      const el=event.target.closest('[data-cms-added-link],img,[data-cms-key],h2,h3,p,strong,.entry-meta,.entry-org,a');
      if(!el || !el.dataset.cmsRef && !el.dataset.cmsAddedLink)return;
      if(el.closest('a')) event.preventDefault();
      if(el.matches('img') || el.closest('[data-cms-new]')){event.preventDefault();event.stopImmediatePropagation();}
      select(el);
    },true);
  }
  document.querySelector('.sidebar-nav').addEventListener('click',event=>{
    if(!event.target.closest('a'))return;
    if(matchMedia('(max-width: 980px)').matches){document.body.classList.remove('sidebar-open');document.getElementById('menuButton').setAttribute('aria-expanded','false');}
  });
  return {empty:()=>clone(base),normalize,structure,render,mount,mode(value){editing=value;if(!value && panel){panel.hidden=true;document.querySelectorAll('.cms-selected').forEach(el=>el.classList.remove('cms-selected'));}}};
};
window.PortfolioCmsAdvanced.safeURL = portfolioCmsSafeURL;
