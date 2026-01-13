(() => {
  // Use same-origin when served via /web; fallback to localhost:8000 for dev servers
  const API = (location.port === '8000' ? `${location.origin}/api/v1` : 'http://localhost:8000/api/v1');
  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));

  const state = {
    aborts: {
      suggest: null,
      run: null,
      query: null,
    },
  };

  function setStatus(id, text, ok) {
    const el = $(id);
    el.textContent = text || '';
    el.style.color = ok === true ? 'var(--good)' : ok === false ? 'var(--bad)' : 'var(--muted)';
  }

  function getLangs() {
    return $$('input[name="langs"]:checked').map(i => i.value);
  }

  function throttle(fn, delay) {
    let last = 0;
    let timer;
    return (...args) => {
      const now = Date.now();
      const remaining = delay - (now - last);
      if (remaining <= 0) {
        clearTimeout(timer);
        last = now;
        fn(...args);
      } else {
        clearTimeout(timer);
        timer = setTimeout(() => {
          last = Date.now();
          fn(...args);
        }, remaining);
      }
    };
  }

  async function doFetch(url, opts, abortKey) {
    // Abort previous request of same kind for responsiveness
    if (state.aborts[abortKey]) state.aborts[abortKey].abort();
    const controller = new AbortController();
    state.aborts[abortKey] = controller;
    const res = await fetch(url, { ...opts, signal: controller.signal });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
  }

  // Suggest Topics
  $('#suggest-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    setStatus('#suggest-status', 'Carregando...');
    $('#topics').innerHTML = '';
    const payload = {
      model: $('#model').value,
      specialist: $('#specialist').value,
      lang: $('#lang').value,
      subject: $('#subject').value.trim(),
    };
    if (!payload.subject) return setStatus('#suggest-status', 'Assunto é obrigatório', false);
    try {
      const data = await doFetch(`${API}/suggest-topics`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      }, 'suggest');
      const topics = (data.topics || []).slice(0, 5);
      if (topics.length === 0) {
        setStatus('#suggest-status', 'Nenhum tópico sugerido', false);
        return;
      }
      const frag = document.createDocumentFragment();
      topics.forEach(t => {
        const li = document.createElement('li');
        li.textContent = t;
        li.addEventListener('click', () => { $('#selected_topic').value = t; });
        frag.appendChild(li);
      });
      $('#topics').appendChild(frag);
      setStatus('#suggest-status', 'OK', true);
    } catch (err) {
      setStatus('#suggest-status', err.message, false);
    }
  });

  // Run TTS
  $('#run-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    setStatus('#run-status', 'Gerando...');
    $('#run-output').textContent = '';
    const payload = {
      model: $('#model').value,
      specialist: $('#specialist').value,
      langs: getLangs(),
      selected_topic: $('#selected_topic').value.trim(),
    };
    if (!payload.selected_topic) return setStatus('#run-status', 'Selecione um tópico', false);
    try {
      const data = await doFetch(`${API}/run-tts`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      }, 'run');
      $('#run-output').textContent = (data.output || '').trim();
      setStatus('#run-status', 'OK', true);
    } catch (err) {
      setStatus('#run-status', err.message, false);
    }
  });

  // Query Qdrant (throttled for performance)
  const queryHandler = throttle(async () => {
    setStatus('#query-status', 'Consultando...');
    $('#query-output').textContent = '';
    const payload = { query_text: $('#query_text').value.trim() };
    if (!payload.query_text) return setStatus('#query-status', 'Texto é obrigatório', false);
    try {
      const data = await doFetch(`${API}/query-qdrant`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      }, 'query');
      $('#query-output').textContent = (data.data || '').trim();
      setStatus('#query-status', 'OK', true);
    } catch (err) {
      setStatus('#query-status', err.message, false);
    }
  }, 600);

  $('#query-form').addEventListener('submit', (e) => { e.preventDefault(); queryHandler(); });
})();