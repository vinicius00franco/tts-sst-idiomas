(() => {
  // Use same-origin when served via /web; fallback to localhost:8000 for dev servers
  const API_BASE = (location.port === '8000' ? location.origin : 'http://localhost:8000');
  const API = `${API_BASE}/api/v1`;
  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));

  const state = {
    aborts: {
      suggest: null,
      run: null,
      query: null,
    },
    howl: null, // Instância do Howler para reprodução de áudio
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
    $('#player').hidden = true;
    $('#transcript').textContent = '';
    // Resetar estado dos botões
    $('#play-btn').disabled = true;
    $('#pause-btn').disabled = true;
    $('#stop-btn').disabled = true;
    $('#audio-status').textContent = '';
    // Parar e limpar áudio anterior
    if (state.howl) {
      state.howl.unload();
      state.howl = null;
    }
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
      console.log('=== RESPOSTA DA API ===' );
      console.log('Dados completos:', JSON.stringify(data, null, 2));
      console.log('data.audios:', data.audios);
      console.log('É array?:', Array.isArray(data.audios));
      console.log('Comprimento:', data.audios?.length);
      $('#run-output').textContent = (data.output || '').trim();
      setStatus('#run-status', 'OK', true);

      // Se o script retornou audios com caminhos, usar o primeiro; caso contrário, buscar /latest-tts
      let audioUrl = null;
      let transcript = null;
      if (Array.isArray(data.audios) && data.audios.length > 0) {
        const a = data.audios[0];
        console.log('=== PROCESSANDO ÁUDIO ===');
        console.log('Primeiro áudio:', a);
        console.log('a.file:', a.file);
        if (a && a.file) {
          const fileName = a.file.includes('/') ? a.file.split('/').pop() : a.file;
          audioUrl = `${API_BASE}/outputs/${fileName}`;
          console.log('URL construído:', audioUrl);
        }
        if (a && a.conversation_uuid) {
          try {
            console.log('Buscando conversa de UUID:', a.conversation_uuid);
            const res = await fetch(`${API}/get-conversation`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ conversation_uuid: a.conversation_uuid })
            });
            const convData = await res.json();
            console.log('Dados da conversa:', convData);
            if (convData.conversation) {
              // Parsear o texto da conversa em linhas
              const lines = convData.conversation.trim().split('\n').map(line => {
                const match = line.match(/^(\w+):\s*(.*)$/);
                return match ? { speaker: match[1], text: match[2] } : null;
              }).filter(Boolean);
              transcript = lines;
            }
          } catch (e) {
            console.error('Erro ao buscar conversa:', e);
          }
        }
      }
      if (!audioUrl) {
        try {
          const latest = await doFetch(`${API}/latest-tts`, { method: 'GET' }, 'run');
          if (latest && latest.audio && latest.audio.url) {
            audioUrl = `${API_BASE}${latest.audio.url}`;
          }
          if (latest && latest.transcript) transcript = latest.transcript;
        } catch {}
      }

      console.log('=== CONFIGURANDO PLAYER ===');
      console.log('Audio URL final:', audioUrl);
      console.log('API_BASE:', API_BASE);
      if (audioUrl) {
        console.log('Criando instância Howl...');
        // Mostrar player imediatamente
        $('#player').hidden = false;
        $('#audio-status').textContent = 'Carregando áudio...';
        // Usar Howler.js para reproduzir FLAC
        state.howl = new Howl({
          src: [audioUrl],
          format: ['flac'],
          html5: true, // Usar HTML5 Audio para streaming
          onload: () => {
            console.log('Áudio carregado com sucesso');
            $('#audio-status').textContent = 'Áudio pronto';
            $('#play-btn').disabled = false;
          },
          onloaderror: (id, error) => {
            console.error('Erro ao carregar áudio:', error);
            $('#audio-status').textContent = 'Erro ao carregar áudio';
          },
          onplay: () => {
            $('#play-btn').disabled = true;
            $('#pause-btn').disabled = false;
            $('#stop-btn').disabled = false;
            $('#audio-status').textContent = 'Reproduzindo...';
          },
          onpause: () => {
            $('#play-btn').disabled = false;
            $('#pause-btn').disabled = true;
            $('#audio-status').textContent = 'Pausado';
          },
          onstop: () => {
            $('#play-btn').disabled = false;
            $('#pause-btn').disabled = true;
            $('#stop-btn').disabled = true;
            $('#audio-status').textContent = 'Parado';
          },
          onend: () => {
            $('#play-btn').disabled = false;
            $('#pause-btn').disabled = true;
            $('#stop-btn').disabled = true;
            $('#audio-status').textContent = 'Finalizado';
          },
        });
        console.log('Howl instanciado, aguardando carregamento...');
      } else {
        console.error('❌ NENHUM AUDIO URL ENCONTRADO!');
        console.error('data.audios:', data.audios);
        console.error('Verifique se a API está retornando os dados corretamente');
        setStatus('#run-status', 'Áudio não encontrado na resposta', false);
      }
      if (Array.isArray(transcript)) {
        const lines = transcript.map(l => `${l.speaker}: ${l.text}`).join('\n');
        $('#transcript').textContent = lines;
        console.log('Transcript exibido:', lines);
      } else {
        console.log('Transcript não é array:', transcript);
      }
    } catch (err) {
      console.error('Erro na requisição:', err);
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

  // Controles do player de áudio
  $('#play-btn').addEventListener('click', () => {
    if (state.howl) state.howl.play();
  });
  
  $('#pause-btn').addEventListener('click', () => {
    if (state.howl) state.howl.pause();
  });
  
  $('#stop-btn').addEventListener('click', () => {
    if (state.howl) state.howl.stop();
  });
})();