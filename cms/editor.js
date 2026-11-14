/* Portfolio CMS phase 2 — on-page, local-only draft editor.
   URL opt-in is NOT authentication. Publishing requires Phase 4 GitHub OAuth. */
(function () {
  'use strict';
  if (new URLSearchParams(window.location.search).get('cms') !== 'edit') return;
  var dict = window.PortfolioTranslations;
  var locales = ['en', 'es', 'ca', 'fr'];
  if (!dict || !locales.every(function (l) { return dict[l] && typeof dict[l] === 'object'; })) return;

  var STORAGE_KEY = 'oriol-cms-draft-v3';
  var original = JSON.parse(JSON.stringify(dict));
  var translationKeys = Object.keys(original.en);
  var keySet = new Set(translationKeys);
  var nodes = new Map();
  var initialStatic = {};
  var editing = true;
  var active = null;
  var saved;
  var working;
  var messages = {
    en: {title:'Visual editor',preview:'Preview',edit:'Edit',save:'Save draft',cancel:'Cancel changes',exit:'Exit',local:'Local draft only · not published',dirty:'unsaved change(s)',ready:'Click any highlighted text to edit',view:'Preview mode',saved:'Draft saved on this device',error:'Unable to save. Browser storage may be disabled.',confirm:'Discard unsaved edits and exit?'},
    es: {title:'Editor visual',preview:'Vista previa',edit:'Editar',save:'Guardar borrador',cancel:'Cancelar cambios',exit:'Salir',local:'Solo borrador local · no publicado',dirty:'cambio(s) sin guardar',ready:'Haz clic en un texto para editarlo',view:'Modo vista previa',saved:'Borrador guardado en este dispositivo',error:'No se ha podido guardar. Comprueba el almacenamiento del navegador.',confirm:'¿Salir sin guardar los cambios?'},
    ca: {title:'Editor visual',preview:'Previsualitzar',edit:'Editar',save:'Desar esborrany',cancel:'Cancel·lar canvis',exit:'Sortir',local:'Només esborrany local · no publicat',dirty:'canvi(s) sense desar',ready:'Clica qualsevol text ressaltat per editar-lo',view:'Mode de previsualització',saved:'Esborrany desat en aquest dispositiu',error:'No s’ha pogut desar. Comprova l’emmagatzematge del navegador.',confirm:'Vols sortir sense desar els canvis?'},
    fr: {title:'Éditeur visuel',preview:'Aperçu',edit:'Modifier',save:'Enregistrer',cancel:'Annuler les changements',exit:'Quitter',local:'Brouillon local · non publié',dirty:'modification(s) non enregistrée(s)',ready:'Cliquez sur un texte pour le modifier',view:'Mode aperçu',saved:'Brouillon enregistré sur cet appareil',error:'Enregistrement impossible. Vérifiez le stockage du navigateur.',confirm:'Quitter sans enregistrer les modifications ?'}
  };

  // Restrict stored/editable rich text so a local draft never injects executable markup.
  function sanitize(value, allowYear) {
    var template = document.createElement('template');
    template.innerHTML = String(value);
    var allowed = new Set(['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'span', 'a', 'div']);
    var removeEntirely = new Set(['script', 'style', 'iframe', 'object', 'embed', 'svg', 'math', 'form', 'input', 'textarea', 'button', 'img', 'audio', 'video', 'link', 'meta']);
    function walk(parent) {
      Array.from(parent.childNodes).forEach(function (node) {
        if (node.nodeType === Node.COMMENT_NODE) { node.remove(); return; }
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        var tag = node.tagName.toLowerCase();
        if (removeEntirely.has(tag)) { node.remove(); return; }
        walk(node);
        if (!allowed.has(tag)) {
          node.replaceWith.apply(node, Array.from(node.childNodes));
          return;
        }
        var attributes = {};
        if (tag === 'span') {
          var permitted = (node.getAttribute('class') || '').split(/\s+/).filter(function (x) {
            return x === 'name-accent' || x === 'brand-word' || /^brand-(?:guspira|accenture|upc|upf)$/.test(x);
          });
          if (permitted.length) attributes.class = permitted.join(' ');
          if (node.id === 'year' && allowYear) attributes.id = 'year';
        }
        if (tag === 'a') {
          var href = node.getAttribute('href') || '';
          if (/^(https?:\/\/|mailto:|#|\/(?!\/))/i.test(href)) {
            attributes.href = href;
            if (node.getAttribute('target') === '_blank') {
              attributes.target = '_blank';
              attributes.rel = 'noopener noreferrer';
            }
          }
        }
        Array.from(node.attributes).forEach(function (attr) { node.removeAttribute(attr.name); });
        Object.keys(attributes).forEach(function (attr) { node.setAttribute(attr, attributes[attr]); });
      });
    }
    walk(template.content);
    return template.innerHTML;
  }

  function registerTargets() {
    translationKeys.forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      var key = 't:' + id;
      el.dataset.cmsKey = key;
      nodes.set(key, el);
    });
    function stablePath(el) {
      var parts = [];
      while (el && el !== document.body) {
        if (el.id && !keySet.has(el.id)) { parts.unshift('#' + el.id); break; }
        var tag = el.tagName.toLowerCase();
        var siblings = Array.from(el.parentElement.children).filter(function (x) { return x.tagName === el.tagName; });
        parts.unshift(tag + ':nth-of-type(' + (siblings.indexOf(el) + 1) + ')');
        el = el.parentElement;
      }
      return parts.join('>');
    }
    var tags = new Set(['A', 'SPAN', 'STRONG', 'P', 'H1', 'H2', 'H3', 'SMALL', 'DIV']);
    document.querySelectorAll('.site-header *, .sidebar *, #main-content *').forEach(function (el) {
      if (!tags.has(el.tagName) || el.hasAttribute('data-cms-key')) return;
      if (el.closest('[data-cms-key],button,summary,.lang-switch,.accent-picker,.reading-time,.scroll-pause-indicator,.story-plus,.num')) return;
      if (el.querySelector('[data-cms-key]')) return;
      if (el.matches('a') && el.querySelector('svg,img')) return;
      if (el.childElementCount && !(el.matches('a') && !el.querySelector('svg,img'))) return;
      if (el.classList.contains('brand-word') || !(el.textContent || '').trim()) return;
      var key = 's:' + stablePath(el);
      if (nodes.has(key)) return;
      el.dataset.cmsKey = key;
      nodes.set(key, el);
      initialStatic[key] = el.innerHTML;
    });
  }
  registerTargets();
  var advanced = window.PortfolioCmsAdvanced({
    locales: locales, sanitize: sanitize, language: language,
    get: function () { return working; }, finish: finishActive,
    change: function () { render(); updateUI(); },
    importDraft: function (value) { finishActive(); working = normalize(value); render(); updateUI(); },
    getDraft: function () { finishActive(); return copy(working); }
  });

  function emptyDraft() { return {version:3, translations:{en:{},es:{},ca:{},fr:{}}, static:{}, staticLocales:{en:{},es:{},ca:{},fr:{}}, content: advanced.empty()}; }
  function copy(value) { return JSON.parse(JSON.stringify(value)); }
  function normalize(value) {
    var out = emptyDraft();
    if (!value || ![1,3].includes(value.version) || typeof value !== 'object') return out;
    locales.forEach(function (l) {
      var source = value.translations && value.translations[l];
      if (!source || typeof source !== 'object') return;
      Object.keys(source).forEach(function (id) {
        if (!keySet.has(id) || typeof source[id] !== 'string') return;
        var val = sanitize(source[id], id === 'footerCopy');
        if (id === 'footerCopy' && !val.includes('id="year"')) val += ' <span id="year"></span>';
        if (val !== original[l][id]) out.translations[l][id] = val;
      });
    });
    if (value.static && typeof value.static === 'object') {
      Object.keys(value.static).forEach(function (key) {
        if (!Object.prototype.hasOwnProperty.call(initialStatic,key) || typeof value.static[key] !== 'string') return;
        var val = sanitize(value.static[key]);
        if (val !== initialStatic[key]) out.static[key] = val;
      });
    }
    locales.forEach(function (l) {
      var source = value.version === 1 ? out.static : (value.staticLocales || {})[l];
      Object.keys(source || {}).forEach(function (k) {
        if (Object.prototype.hasOwnProperty.call(initialStatic,k) && typeof source[k] === 'string') out.staticLocales[l][k] = sanitize(source[k]);
      });
    });
    out.static = {};
    out.content = advanced.normalize(value.content);
    return out;
  }
  try { saved = normalize(JSON.parse(localStorage.getItem(STORAGE_KEY) || localStorage.getItem('oriol-cms-draft-v1'))); }
  catch (_) { saved = emptyDraft(); }
  working = copy(saved);

  var toolbar = document.createElement('section');
  toolbar.id = 'cmsToolbar';
  toolbar.setAttribute('role', 'region');
  toolbar.setAttribute('aria-label', 'Portfolio visual editor');
  var info = document.createElement('div');
  info.className = 'cms-info';
  var title = document.createElement('strong');
  title.className = 'cms-title';
  var status = document.createElement('span');
  status.className = 'cms-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  info.append(title, status);
  var actions = document.createElement('div');
  actions.className = 'cms-actions';
  function makeButton(className, onClick) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.addEventListener('click', onClick);
    actions.appendChild(button);
    return button;
  }
  var toggle = makeButton('cms-toggle', function () {
    finishActive();
    editing = !editing;
    updateUI();
  });
  var save = makeButton('cms-save', function () {
    finishActive();
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(working));
      saved = copy(working);
      updateUI('saved');
    } catch (_) { updateUI('error'); }
  });
  var cancel = makeButton('cms-cancel', function () {
    finishActive();
    working = copy(saved);
    render();
    editing = false;
    updateUI();
  });
  var exit = makeButton('cms-exit', function () {
    finishActive();
    if (isDirty() && !window.confirm(messages[language()].confirm)) return;
    var url = new URL(window.location.href);
    url.searchParams.delete('cms');
    window.location.assign(url.href);
  });
  toolbar.append(info, actions);
  document.body.appendChild(toolbar);

  function language() { return locales.includes(document.documentElement.lang) ? document.documentElement.lang : 'en'; }
  function dirtyCount() {
    return JSON.stringify(working) === JSON.stringify(saved) ? 0 : 1;
  }
  function isDirty() { return dirtyCount() > 0; }
  function updateUI(messageKey) {
    var t = messages[language()];
    advanced.mode(editing);
    document.body.classList.toggle('cms-editing', editing);
    document.body.classList.toggle('cms-preview', !editing);
    title.textContent = t.title;
    toggle.textContent = editing ? t.preview : t.edit;
    save.textContent = t.save;
    cancel.textContent = t.cancel;
    exit.textContent = t.exit;
    cancel.disabled = !isDirty();
    save.disabled = !isDirty();
    status.textContent = messageKey ? t[messageKey] : (t.local + ' · ' + (isDirty() ? dirtyCount() + ' ' + t.dirty : (editing ? t.ready : t.view)));
  }
  function record(key, html) {
    var value = sanitize(html, key === 't:footerCopy');
    if (key === 't:footerCopy' && !value.includes('id="year"')) value += ' <span id="year">' + new Date().getFullYear() + '</span>';
    var ref = nodes.get(key)?.dataset.cmsRef;
    if (ref && working.content.fields[ref]) working.content.fields[ref][language()] = value;
    if (key.slice(0,2) === 't:') {
      var id = key.slice(2);
      var locale = language();
      if (value === original[locale][id]) delete working.translations[locale][id];
      else working.translations[locale][id] = value;
      dict[locale][id] = value;
    } else if (key.slice(0,2) === 's:') {
      if (value === initialStatic[key]) delete working.staticLocales[language()][key];
      else working.staticLocales[language()][key] = value;
    }
  }
  function finishActive() {
    if (!active) return;
    var el = active;
    active = null;
    record(el.dataset.cmsKey, el.innerHTML);
    el.removeAttribute('contenteditable');
    // Remove unsafe attributes introduced by rich-text paste, without losing structure.
    el.innerHTML = el.dataset.cmsKey === 't:footerCopy' ? dict[language()].footerCopy : sanitize(el.innerHTML);
    updateUI();
  }
  function render() {
    advanced.structure();
    locales.forEach(function (l) {
      translationKeys.forEach(function (key) {
        dict[l][key] = Object.prototype.hasOwnProperty.call(working.translations[l],key) ? working.translations[l][key] : original[l][key];
      });
    });
    Object.keys(initialStatic).forEach(function (key) {
      var el = nodes.get(key);
      if (el) el.innerHTML = Object.prototype.hasOwnProperty.call(working.staticLocales[language()],key) ? working.staticLocales[language()][key] : initialStatic[key];
    });
    var current = document.getElementById('lang' + language().charAt(0).toUpperCase() + language().slice(1));
    if (current) current.click(); // Invokes the existing translation, brand-highlight and reading-time logic.
  }

  // Capture clicks to edit rather than accidentally follow existing links.
  document.addEventListener('click', function (event) {
    if (!editing || toolbar.contains(event.target)) return;
    if (event.target.closest('[data-cms-ui], [data-cms-new]')) return;
    var el = event.target.closest('[data-cms-key]');
    if (!el || !nodes.has(el.dataset.cmsKey)) return;
    event.preventDefault();
    event.stopPropagation();
    if (active === el) return;
    finishActive();
    active = el;
    el.setAttribute('contenteditable','true');
    el.setAttribute('spellcheck','true');
    el.focus();
    var range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }, true);
  document.addEventListener('input', function (event) {
    if (!active || !active.contains(event.target)) return;
    record(active.dataset.cmsKey, active.innerHTML);
    updateUI();
  }, true);
  document.addEventListener('focusout', function (event) {
    if (active && event.target === active) finishActive();
  }, true);
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && active) {
      event.preventDefault();
      var focused = active;
      finishActive();
      focused.blur();
    }
  }, true);
  document.querySelectorAll('.lang-switch button').forEach(function (button) {
    button.addEventListener('click', function () { finishActive(); }, true);
    button.addEventListener('click', function () {
      Object.keys(initialStatic).forEach(function (key) {
        nodes.get(key).innerHTML = Object.prototype.hasOwnProperty.call(working.staticLocales[language()],key) ? working.staticLocales[language()][key] : initialStatic[key];
      });
      advanced.render(); updateUI();
    });
  });
  advanced.mount(actions);
  render();
  updateUI();
  window.PortfolioCmsEditor = Object.freeze({
    getDraft: function () { finishActive(); return copy(working); },
    getSavedDraft: function () { return copy(saved); },
    isDirty: isDirty,
    getEditableCount: function () { return nodes.size; }
  });
})();
