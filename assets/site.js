
    const root = document.documentElement;
    const body = document.body;
    const menuButton = document.getElementById('menuButton');
    const scrim = document.getElementById('mobileScrim');
    const themeButton = document.getElementById('themeButton');
    const langEn = document.getElementById('langEn');
    const langEs = document.getElementById('langEs');
    const langCa = document.getElementById('langCa');
    const langFr = document.getElementById('langFr');
    const sidebarLinks = [...document.querySelectorAll('.sidebar-nav a')];
    const autoScrollButton = document.getElementById('autoScrollButton');
    let autoScrollActive = false;
    let autoScrollFrame = null;
    let lastAutoScrollTime = 0;

    function safeGet(key){ try { return localStorage.getItem(key); } catch(e) { return null; } }
    function safeSet(key,val){ try { localStorage.setItem(key,val); } catch(e) {} }

    root.dataset.theme = safeGet('oriol-theme') || 'light';
    // Save and restore the four selectable interface accent colours.
    const accentChoices = [...document.querySelectorAll('.accent-choice')];
    const accentColours = new Set(['blue', 'red', 'orange', 'purple']);
    function applyAccent(choice) {
      const colour = accentColours.has(choice) ? choice : 'blue';
      root.dataset.accent = colour;
      accentChoices.forEach(btn => {
        const current = btn.dataset.choice === colour;
        btn.classList.toggle('is-selected', current);
        btn.setAttribute('aria-pressed', String(current));
      });
      safeSet('oriol-accent', colour);
    }
    applyAccent(safeGet('oriol-accent') || 'blue');
    accentChoices.forEach(button => button.addEventListener('click', () => applyAccent(button.dataset.choice)));

    themeButton.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      safeSet('oriol-theme', root.dataset.theme);
    });

    const compact = window.matchMedia('(max-width: 980px)');
    function setMenu(open){ body.classList.toggle('sidebar-open', open); menuButton.setAttribute('aria-expanded', String(open)); }
    function syncMenu(){ if(compact.matches) setMenu(false); else setMenu(true); }
    syncMenu();
    compact.addEventListener ? compact.addEventListener('change', syncMenu) : compact.addListener(syncMenu);
    menuButton.addEventListener('click', () => setMenu(!body.classList.contains('sidebar-open')));
    scrim.addEventListener('click', () => setMenu(false));
    sidebarLinks.forEach(link => link.addEventListener('click', () => { if(compact.matches) setMenu(false); }));
    document.getElementById('year').textContent = new Date().getFullYear();

    const translations = window.PortfolioTranslations;

    // Apply visual identities to brand mentions in both languages.
    // Working on text nodes keeps links, strong elements, and inline structure intact.
    function colourBrandNames() {
      const matcher = /(?<![\p{L}\p{N}])(?:Associació\s+Guspira\s+Lleure|Guspira\s+Lleure|Accenture|Guspira|UPC|UPF)(?![\p{L}\p{N}])/giu;
      const roots = [document.querySelector('.page'), document.querySelector('.sidebar'), document.querySelector('.site-brand')].filter(Boolean);
      roots.forEach(scope => {
        const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, {
          acceptNode(node) {
            if (!node.nodeValue || !matcher.test(node.nodeValue)) { matcher.lastIndex = 0; return NodeFilter.FILTER_REJECT; }
            matcher.lastIndex = 0;
            if (node.parentElement.closest('.brand-word, script, style, svg, textarea, button')) return NodeFilter.FILTER_REJECT;
            return NodeFilter.FILTER_ACCEPT;
          }
        });
        const matches = [];
        while (walker.nextNode()) matches.push(walker.currentNode);
        matches.forEach(node => {
          const original = node.nodeValue;
          const frag = document.createDocumentFragment();
          let from = 0;
          for (const found of original.matchAll(matcher)) {
            if (found.index > from) frag.appendChild(document.createTextNode(original.slice(from, found.index)));
            const span = document.createElement('span');
            span.className = 'brand-word brand-' + (/guspira/i.test(found[0]) ? 'guspira' : found[0].toLowerCase());
            span.textContent = found[0];
            frag.appendChild(span);
            from = found.index + found[0].length;
          }
          if (from < original.length) frag.appendChild(document.createTextNode(original.slice(from)));
          node.parentNode.replaceChild(frag, node);
        });
      });
    }

    const translatableIds = [
      'navAbout','navEducation','navExperience','navPersonal','sidebarTitle','sideHome','sideAbout','sideEducation','sideExperience','sidePersonal','sideContact','sidebarBottom','sidebarCta','heroEyebrow','homeHeading','heroSubtitle','jumpLabel','jumpAbout','jumpEducation','jumpExperience','jumpPersonal','jumpContact','aboutTitle','educationTitle','educationSummary','edu1Title','edu1Meta','edu1Desc','edu2Title','edu2Meta','edu2Desc','edu3Title','edu3Meta','edu3Desc','edu4Title','edu4Meta','edu4Desc','eduSpanishTitle','eduSpanishMeta','eduSpanishDesc','edu5Title','edu5Meta','edu5Desc','experienceTitle','legendWork','legendProject','accTag','accTitle','accMeta','accDesc','gusTag','gusTitle','gusMeta','gusDesc1','gusDesc2','metric1','metric2','metric3','metric4','d180Tag','d180Title','d180Meta','d180Desc','scoutTag','scoutTitle','scoutMeta','scoutDesc','tutorTag','tutorTitle','tutorMeta','tutorOrg','tutorDesc','onTag','onTitle','onMeta','onDesc','personalTitle','p1Title','p1Desc','p2Title','p2Desc','p3Title','p3Desc','p4Title','p4Desc','p5Title','p5Desc','photoPlaceholder1','photoPlaceholder2','contactTitle','contactHeading','contactCopy','contactNote','footerBack'
    ];
    const htmlTargets = ['aboutText','educationIntro','educationStory','experienceIntro','personalIntro','footerCopy'];

    function updateReadingTime() {
      // textContent includes the education-story text even when collapsed.
      const text = document.getElementById('main-content').textContent || '';
      const words = text.trim().split(/\s+/).filter(Boolean).length;
      const minutes = Math.max(1, Math.ceil(words / 220));
      const labels = { en: 'Estimated reading time', es: 'Tiempo estimado de lectura', ca: 'Temps estimat de lectura', fr: 'Temps de lecture estimé' };
      const units = { en: 'minutes', es: 'minutos', ca: 'minuts', fr: 'minutes' };
      const lang = root.lang in labels ? root.lang : 'en';
      const el = document.getElementById('readingTime');
      el.textContent = `⏱ ${minutes} min`;
      el.title = labels[lang];
      el.setAttribute('aria-label', `${labels[lang]}: ${minutes} ${units[lang]}`);
    }

    function applyLang(lang){
      const t = translations[lang] || translations.en;
      translatableIds.forEach(id => {
        const el = document.getElementById(id);
        if(el && t[id] !== undefined) el.innerHTML = t[id];
      });
      htmlTargets.forEach(id => {
        const el = document.getElementById(id);
        if(el && t[id] !== undefined) el.innerHTML = t[id];
      });
      langEn.classList.toggle('active', lang === 'en');
      langEs.classList.toggle('active', lang === 'es');
      langCa.classList.toggle('active', lang === 'ca');
      langFr.classList.toggle('active', lang === 'fr');
      safeSet('oriol-lang', lang);
      document.documentElement.lang = lang;
      document.getElementById('year').textContent = new Date().getFullYear();
      updateAutoScrollUI();
      colourBrandNames();
      updateReadingTime();
    }
    const storedLang = safeGet('oriol-lang') || 'en';
    applyLang(storedLang);
    langEn.addEventListener('click', () => applyLang('en'));
    langEs.addEventListener('click', () => applyLang('es'));
    langCa.addEventListener('click', () => applyLang('ca'));
    langFr.addEventListener('click', () => applyLang('fr'));


    // The floating thinker starts gentle continuous scrolling; click again to pause.
    function updateAutoScrollUI() {
      const es = document.documentElement.lang === 'es';
      const label = autoScrollActive ? (es ? 'Pausar desplazamiento automático' : 'Pause automatic scrolling')
                                     : (es ? 'Iniciar desplazamiento automático' : 'Start automatic scrolling');
      autoScrollButton.setAttribute('aria-label', label);
      autoScrollButton.setAttribute('title', label);
      autoScrollButton.setAttribute('aria-pressed', String(autoScrollActive));
      body.classList.toggle('auto-scrolling', autoScrollActive);
    }
    function stopAutoScroll() {
      autoScrollActive = false;
      if (autoScrollFrame != null) cancelAnimationFrame(autoScrollFrame);
      autoScrollFrame = null;
      lastAutoScrollTime = 0;
      updateAutoScrollUI();
    }
    function autoScrollStep(timestamp) {
      if (!autoScrollActive) return;
      const maxTop = document.documentElement.scrollHeight - window.innerHeight;
      if (maxTop <= 0 || window.scrollY >= maxTop - 1) { stopAutoScroll(); return; }
      if (!lastAutoScrollTime) lastAutoScrollTime = timestamp;
      const dt = Math.min(timestamp - lastAutoScrollTime, 100) / 1000;
      lastAutoScrollTime = timestamp;
      const next = Math.min(maxTop, window.scrollY + dt * 42);
      window.scrollTo({ top: next, behavior: 'instant' });
      autoScrollFrame = requestAnimationFrame(autoScrollStep);
    }
    autoScrollButton.addEventListener('click', () => {
      if (autoScrollActive) { stopAutoScroll(); return; }
      const maxTop = document.documentElement.scrollHeight - window.innerHeight;
      if (window.scrollY >= maxTop - 1 && maxTop > 0) window.scrollTo({ top: 0, behavior: 'instant' });
      autoScrollActive = true;
      updateAutoScrollUI();
      lastAutoScrollTime = 0;
      autoScrollFrame = requestAnimationFrame(autoScrollStep);
    });
    window.addEventListener('wheel', stopAutoScroll, { passive: true });
    // Any click/tap on the rest of the page pauses reading immediately.
    // Exclude the thinker itself so its normal start/pause toggle still works.
    document.addEventListener('pointerdown', event => {
      if (autoScrollActive && !autoScrollButton.contains(event.target)) stopAutoScroll();
    }, { capture: true });
    // Touch fallback for older browsers without Pointer Events.
    window.addEventListener('touchstart', event => {
      if (autoScrollActive && !autoScrollButton.contains(event.target)) stopAutoScroll();
    }, { passive: true });
    document.addEventListener('keydown', event => {
      if (['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '].includes(event.key)) stopAutoScroll();
    });
    document.addEventListener('click', event => {
      if (autoScrollActive && !autoScrollButton.contains(event.target)) stopAutoScroll();
    });
    document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', stopAutoScroll));

    const sectionIds = ['home','about','education','experience','personal','contact'];
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if(!entry.isIntersecting) return;
        sidebarLinks.forEach(a => {
          const active = a.getAttribute('href') === '#' + entry.target.id;
          a.classList.toggle('active', active);
          if(active) a.setAttribute('aria-current','location'); else a.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '-15% 0px -65% 0px', threshold: 0 });
    sectionIds.forEach(id => { const el = document.getElementById(id); if(el) observer.observe(el); });
  
