/* The publication service serves the editor and its API on the same origin. */
window.PortfolioCmsPublish = function (actions, previewDraft) {
  'use strict';
  function make(tag, text, parent) {
    const element = document.createElement(tag);
    element.textContent = text;
    parent.append(element);
    return element;
  }

  const dialog = make('dialog', '', document.body);
  dialog.id = 'cmsPublish';
  dialog.dataset.cmsUi = '';
  dialog.setAttribute('aria-labelledby', 'cmsPublishTitle');
  make('h2', 'Publish draft to development', dialog).id = 'cmsPublishTitle';
  const status = make('p', '', dialog);
  status.setAttribute('role', 'status');
  const controls = make('div', '', dialog);
  controls.className = 'cms-actions';
  let busy = false, connected = false, snapshot = null;

  function button(label, handler, parent = controls) {
    const element = make('button', label, parent);
    element.type = 'button';
    element.addEventListener('click', handler);
    return element;
  }

  const open = button('Publish draft', () => {
    dialog.showModal();
    refresh();
  }, actions);
  open.className = 'cms-publish';
  const close = button('Close', () => dialog.close());
  const connect = button('Connect GitHub', () => run(async () => {
    const {url} = await request('/api/login', '{}');
    authLink.href = url;
    authLink.hidden = false;
    status.textContent = 'Authorize on GitHub in a new tab, then return here and check the connection.';
  }));
  const check = button('Check connection', () => refresh());
  const logout = button('Disconnect', () => run(async () => {
    const {revoked} = await request('/api/logout', '{}');
    clearReview();
    authLink.hidden = true;
    connected = false;
    status.textContent = revoked ? 'GitHub disconnected.' :
      'Local session ended. Revoke the app authorization in GitHub settings if needed.';
  }));
  const review = button('Review current draft', () => run(async () => {
    clearReview();
    const draft = previewDraft();
    const result = await request('/api/review', draft);
    const parsed = JSON.parse(draft);
    snapshot = draft;
    const entries = parsed.content.sections.reduce((count, section) => count + section.entries.length, 0);
    summary.textContent = `${result.change}: ${result.path} on ${result.branch} at ${result.head.slice(0, 12)}. ` +
      `This v3 snapshot includes ${parsed.content.sections.length} sections, ${entries} entries and all four locale dictionaries. ` +
      'The development branch is publicly readable. The live site is unchanged.';
    json.textContent = JSON.stringify(parsed, null, 2);
    details.hidden = false;
    status.textContent = 'Review the JSON here or return to the visual preview. Reopen this panel to confirm the same draft.';
    publish.hidden = result.change === 'unchanged';
    if (publish.hidden) status.textContent = 'This draft already matches the development branch.';
  }));
  const authLink = make('a', 'Authorize on GitHub ↗', dialog);
  authLink.target = '_blank';
  authLink.rel = 'noopener noreferrer';
  authLink.hidden = true;
  const summary = make('p', '', dialog);
  const details = make('details', '', dialog);
  details.hidden = true;
  make('summary', 'Inspect the exact draft JSON', details);
  const json = make('pre', '', details);
  const resultLink = make('a', 'Open GitHub commit ↗', dialog);
  resultLink.target = '_blank';
  resultLink.rel = 'noopener noreferrer';
  resultLink.hidden = true;
  const publish = button('Confirm development publish', () => run(async () => {
    const draft = snapshot;
    if (previewDraft() !== draft) {
      clearReview();
      throw new Error('The draft changed. Review the updated version before publishing.');
    }
    clearReview();
    const result = await request('/api/publish', draft);
    status.textContent = result.unchanged ? 'This draft is already on the development branch.' :
      'Draft committed to the development branch.';
    resultLink.href = result.url;
    resultLink.hidden = false;
  }), dialog);
  publish.hidden = true;
  [connect, check, logout, review].forEach(control => { control.hidden = true; });
  dialog.addEventListener('cancel', event => {
    if (busy) event.preventDefault();
  });

  async function request(path, body) {
    let response;
    try {
      response = await fetch(path, body === undefined ? {cache: 'no-store'} : {
        method: 'POST', cache: 'no-store',
        headers: {'Content-Type': 'application/json', 'X-Portfolio-CMS': '1'}, body,
      });
    } catch (_) {
      throw new Error('Connection lost. Your local draft is still in the editor. Try again.');
    }
    if (!response.headers.get('Content-Type')?.startsWith('application/json')) {
      throw new Error('The publisher is unavailable here. Open the editor on the configured publisher host.');
    }
    const data = await response.json();
    if (response.status === 401) {
      connected = false;
      clearReview();
    }
    if (!response.ok) throw new Error(data.error || 'The publisher could not complete the request.');
    return data;
  }

  function clearReview() {
    snapshot = null;
    summary.textContent = '';
    json.textContent = '';
    details.hidden = true;
    publish.hidden = true;
    resultLink.hidden = true;
  }

  async function run(work) {
    if (busy) return;
    busy = true;
    const buttons = [close, connect, check, logout, review, publish];
    buttons.forEach(control => { control.disabled = true; });
    status.textContent = 'Contacting the publisher…';
    try {
      await work();
    } catch (error) {
      status.textContent = error.message;
    } finally {
      buttons.forEach(control => { control.disabled = false; });
      busy = false;
      connect.hidden = connected || check.hidden;
      logout.hidden = !connected;
      review.hidden = !connected;
    }
  }

  function refresh() {
    return run(async () => {
      const {login} = await request('/api/session');
      check.hidden = false;
      connected = Boolean(login);
      if (!connected) clearReview();
      if (connected) authLink.hidden = true;
      if (snapshot || !resultLink.hidden) return;
      status.textContent = connected ? `Connected as ${login}. Select the current draft to review it.` :
        'Connect an authorized GitHub account to review and publish a draft.';
    });
  }
};
