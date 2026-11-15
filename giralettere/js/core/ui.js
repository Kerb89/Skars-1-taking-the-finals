// Piccoli helper DOM condivisi dai giochi.

export function el(tag, attrs = {}, ...figli) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k === 'text') n.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2), v);
    else if (k === 'dataset') Object.assign(n.dataset, v);
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const f of figli.flat()) {
    if (f == null || f === false) continue;
    n.append(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  return n;
}

export function svuota(n) { while (n.firstChild) n.removeChild(n.firstChild); return n; }

export function fase(valore) { document.body.dataset.fase = valore; }

// Barra del tempo: restituisce una funzione aggiorna(restanteMs, totaleMs).
export function barraTempo(etichetta = 'Tempo') {
  const riempimento = el('div', { class: 'tempo-riempimento' });
  const testo = el('span', { class: 'tempo-testo', id: 'tempo-restante' });
  const nodo = el('div', { class: 'tempo', role: 'timer', 'aria-label': etichetta },
    el('div', { class: 'tempo-barra' }, riempimento), testo);
  const aggiorna = (restanteMs, totaleMs) => {
    const quota = totaleMs > 0 ? Math.max(0, Math.min(1, restanteMs / totaleMs)) : 0;
    riempimento.style.width = (quota * 100).toFixed(1) + '%';
    nodo.classList.toggle('tempo-critico', restanteMs <= 3000);
    testo.textContent = Math.ceil(restanteMs / 1000) + ' s';
    nodo.dataset.restanteMs = String(Math.round(restanteMs));
  };
  return { nodo, aggiorna };
}

export function feedback(contenitore, esito, testo) {
  const classi = { corretta: 'fb-ok', sbagliata: 'fb-ko', tempo_scaduto: 'fb-ko', passata: 'fb-passo' };
  const titoli = { corretta: 'Giusto!', sbagliata: 'Sbagliato', tempo_scaduto: 'Tempo scaduto', passata: 'Passo' };
  const n = el('div', { class: 'feedback ' + (classi[esito] || ''), role: 'status', dataset: { esito } },
    el('strong', { text: titoli[esito] || esito }), testo ? el('span', { text: testo }) : null);
  contenitore.append(n);
  return n;
}

// Campo di risposta libera: risolve alla pressione di Invio/bottone con il
// testo grezzo. onPrimoTasto scatta al primo carattere digitato.
export function campoRisposta({ segnaposto = 'La tua risposta', onPrimoTasto } = {}) {
  const input = el('input', {
    class: 'risposta-input', id: 'risposta', type: 'text', autocomplete: 'off',
    autocapitalize: 'off', spellcheck: 'false', placeholder: segnaposto, 'aria-label': 'Risposta',
  });
  const bottone = el('button', { class: 'btn btn-primario', id: 'invia', type: 'submit', text: 'Invia' });
  const form = el('form', { class: 'risposta-form', autocomplete: 'off' }, input, bottone);
  let risolvi;
  const inviata = new Promise((r) => { risolvi = r; });
  let primo = false;
  input.addEventListener('input', () => {
    if (!primo && input.value.length > 0) { primo = true; onPrimoTasto?.(); }
  });
  form.addEventListener('submit', (e) => { e.preventDefault(); risolvi(input.value); });
  const disabilita = () => { input.disabled = true; bottone.disabled = true; };
  return { form, input, bottone, inviata, disabilita, focus: () => setTimeout(() => input.focus(), 0) };
}

export function mescola(arr, rnd = Math.random) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
