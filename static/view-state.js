// Per-tab, per-profile view preferences. Storage failures never block navigation.
window.JournalViewState = {
  async create(page, fields, defaults = {}) {
    const profile = await (window.journalProfileReady || Promise.resolve(null));
    const key = profile ? `rift-journal:view:1:${encodeURIComponent(profile)}:${page}` : null;
    let saved = {};
    try { saved = key ? JSON.parse(sessionStorage.getItem(key) || '{}') : {}; } catch {}
    if (!saved || typeof saved !== 'object' || Array.isArray(saved)) saved = {};
    for (const id of fields) {
      const control = document.getElementById(id), value = saved[id];
      if (!control || typeof value !== 'string') continue;
      if (control.tagName === 'SELECT' && !Array.from(control.options).some(o => o.value === value)) continue;
      control.value = value.slice(0, 200);
    }
    let pendingScroll = Number.isFinite(saved.scroll) && saved.scroll >= 0 ? saved.scroll : 0;
    const state = {...defaults, ...saved};
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    const save = (extra = {}) => {
      Object.assign(state, extra);
      for (const id of fields) state[id] = document.getElementById(id)?.value || '';
      state.scroll = window.scrollY;
      try { if (key) sessionStorage.setItem(key, JSON.stringify(state)); } catch {}
    };
    const restoreScroll = () => {
      const position = pendingScroll; pendingScroll = null;
      if (position === null) return;
      requestAnimationFrame(() => requestAnimationFrame(() => window.scrollTo(0, position)));
    };
    window.addEventListener('pagehide', () => save());
    return {state, save, restoreScroll, resetScroll() { pendingScroll = null; }};
  }
};
