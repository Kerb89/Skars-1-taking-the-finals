// Pagina di tracciamento: elenco partite, dettaglio risposte, viste per
// giocatore e per domanda. Filtri in querystring. Si vede sempre la produzione:
// nessun selettore di ambiente. Solo i test e2e passano ?ambiente=preview nell'URL.

import { caricaConfig } from './core/contenuto.js';
import { normalizza } from './core/normalizza.js';
import { el, svuota } from './core/ui.js';

const NOMI = { parole: 'Parole impossibili', bocciato: 'Bocciato', elemento: 'Elemento comune', titolo: 'Completa il titolo', manolesta: 'Mano lesta', ruota: 'Ruota finale' };
const ESITI = { corretta: 'corretta', sbagliata: 'sbagliata', passata: 'passata', tempo_scaduto: 'tempo scaduto' };
const VISTE = ['partite', 'partita', 'giocatori', 'domande'];

const $ = (s) => document.querySelector(s);
const contenuto = $('#contenuto');
const stato = $('#stato');
const sel = { partita: $('#f-partita'), giocatore: $('#f-giocatore'), gioco: $('#f-gioco') };
const AMBIENTE = ['production', 'preview'].includes(new URLSearchParams(location.search).get('ambiente'))
  ? new URLSearchParams(location.search).get('ambiente') : 'production';
let config;
let vista = 'partite';

const sec = (ms) => (ms == null ? '—' : (ms / 1000).toFixed(1) + ' s');
const pct = (a, b) => (b ? Math.round((100 * a) / b) + '%' : '—');
const data = (iso) => (iso ? new Date(iso).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'short' }) : '—');
const pill = (esito) => el('span', { class: 'esito esito-' + esito, text: ESITI[esito] || esito });

function tabella(intestazioni, righe, attrs = {}) {
  return el('table', { class: 'tabella', ...attrs },
    el('thead', {}, el('tr', {}, intestazioni.map(([t, c]) => el('th', { class: c || null, text: t })))),
    el('tbody', {}, righe));
}

function filtriCorrenti() {
  const q = new URLSearchParams();
  for (const [k, s] of Object.entries(sel)) if (s.value) q.set(k, s.value);
  q.set('ambiente', AMBIENTE);
  return q;
}

function sincronizzaURL() {
  const q = filtriCorrenti();
  if (AMBIENTE === 'production') q.delete('ambiente');
  q.set('vista', vista);
  history.replaceState(null, '', '?' + q.toString());
  document.querySelectorAll('#schede [data-vista]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.vista === vista)));
}

async function api(v, extra = {}) {
  const q = filtriCorrenti();
  q.set('vista', v);
  Object.entries(extra).forEach(([k, val]) => q.set(k, val));
  const res = await fetch(config.rete.endpoint_tracciamento + '?' + q.toString(), { cache: 'no-store' });
  const corpo = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(corpo.errore || 'HTTP ' + res.status);
  return corpo;
}

function riempi(s, valori, etichettaVuota) {
  const corrente = s.value || new URLSearchParams(location.search).get(s.name) || '';
  svuota(s).append(el('option', { value: '', text: etichettaVuota }));
  const tutti = corrente && !valori.includes(corrente) ? [corrente, ...valori] : valori;
  tutti.forEach((v) => s.append(el('option', { value: v, text: NOMI[v] || v })));
  s.value = corrente;
}

async function caricaFiltri() {
  const f = await api('filtri');
  riempi(sel.partita, f.partite, 'Tutte');
  riempi(sel.giocatore, f.giocatori, 'Tutti');
  riempi(sel.gioco, f.giochi, 'Tutti');
}

// ---- viste

function vistaPartite({ sessioni }) {
  if (!sessioni.length) return el('p', { class: 'nota', text: 'Nessuna partita con questi filtri.' });
  const perPartita = new Map();
  sessioni.forEach((s) => { if (!perPartita.has(s.partita_id)) perPartita.set(s.partita_id, []); perPartita.get(s.partita_id).push(s); });
  return el('div', { id: 'vista-partite' }, [...perPartita].map(([pid, ss]) => el('div', { class: 'blocco-partita', dataset: { partita: pid } },
    el('h2', {}, `Partita ${pid} `, el('span', { class: 'nota', text: `${ss.length} sessioni, ${new Set(ss.map((x) => x.giocatore)).size} giocatori` })),
    tabella([['Giocatore'], ['Avviata'], ['Gioco'], ['Punti'], ['Secondi ruota', 'num'], ['Risposte', 'num'], ['Corrette', 'num'], ['']],
      ss.map((s) => {
        let punti = '';
        try { punti = Object.entries(JSON.parse(s.punti_json || '{}')).map(([g, p]) => `${NOMI[g] || g}: ${p}`).join(' · '); } catch (_) {}
        return el('tr', { dataset: { sessione: s.sessione_id } },
          el('td', { text: s.giocatore }), el('td', { text: data(s.avviata_at) + (s.conclusa_at ? '' : ' · in corso') }),
          el('td', { text: s.gioco_avviato === 'tutti' ? 'completa' : NOMI[s.gioco_avviato] || s.gioco_avviato }),
          el('td', { text: punti || '—' }), el('td', { class: 'num', text: s.secondi_ruota ?? '—' }),
          el('td', { class: 'num', text: s.risposte }), el('td', { class: 'num', text: `${s.corrette} (${pct(s.corrette, s.risposte)})` }),
          el('td', {}, el('a', { href: '#', text: 'risposte', onclick: (e) => { e.preventDefault(); sel.partita.value = pid; sel.giocatore.value = s.giocatore; mostra('partita'); } })));
      })))));
}

function vistaPartita({ risposte }) {
  if (!risposte.length) return el('p', { class: 'nota', text: 'Nessuna risposta con questi filtri.' });
  return tabella([['#', 'num'], ['Giocatore'], ['Sessione'], ['Gioco'], ['Domanda'], ['Risposta data'], ['Attesa'], ['Esito'], ['Tempo', 'num'], ['Ora']],
    risposte.map((r) => el('tr', { dataset: { id: r.id, esito: r.esito } },
      el('td', { class: 'num', text: r.ordine }), el('td', { text: r.giocatore }),
      el('td', {}, el('code', { title: r.sessione_id, text: r.sessione_id.slice(0, 8) })),
      el('td', { text: NOMI[r.gioco] || r.gioco }), el('td', {}, el('code', { text: r.domanda_id })),
      el('td', { class: 'risposta-data', text: r.risposta_data ?? '—' }), el('td', { text: r.risposta_attesa }),
      el('td', {}, pill(r.esito)), el('td', { class: 'num', text: sec(r.tempo_ms) }), el('td', { text: data(r.client_ts) }))),
    { id: 'vista-partita' });
}

function vistaGiocatori({ giocatori }) {
  if (!giocatori.length) return el('p', { class: 'nota', text: 'Nessun dato con questi filtri.' });
  return tabella([['Giocatore'], ['Gioco'], ['Risposte', 'num'], ['% corrette', 'num'], ['Sbagliate', 'num'], ['Passate', 'num'], ['Scadute', 'num'], ['Tempo medio', 'num'], ['Sessioni', 'num']],
    giocatori.map((g) => el('tr', { dataset: { giocatore: g.giocatore, gioco: g.gioco } },
      el('td', { text: g.giocatore }), el('td', { text: NOMI[g.gioco] || g.gioco }), el('td', { class: 'num', text: g.totale }),
      el('td', { class: 'num pct', text: pct(g.corrette, g.totale) }), el('td', { class: 'num', text: g.sbagliate }),
      el('td', { class: 'num', text: g.passate }), el('td', { class: 'num', text: g.scadute }),
      el('td', { class: 'num', text: sec(g.tempo_medio_ms) }), el('td', { class: 'num', text: g.sessioni }))),
    { id: 'vista-giocatori' });
}

// Le risposte sbagliate vengono raggruppate per forma normalizzata: due
// scritture diverse della stessa parola contano come la stessa risposta
// ricorrente, ed è quella forma da valutare come nuova variante.
export function raggruppaSbagliate(righe, soglia) {
  const mappa = new Map();
  for (const r of righe) {
    const chiave = `${r.gioco}|${r.domanda_id}`;
    if (!mappa.has(chiave)) mappa.set(chiave, new Map());
    const n = normalizza(r.risposta_data) || r.risposta_data;
    const g = mappa.get(chiave);
    const voce = g.get(n) || { normalizzata: n, volte: 0, scritture: new Set() };
    voce.volte += r.volte;
    voce.scritture.add(r.risposta_data);
    g.set(n, voce);
  }
  const out = new Map();
  mappa.forEach((g, k) => out.set(k, [...g.values()].sort((a, b) => b.volte - a.volte)
    .map((v) => ({ ...v, scritture: [...v.scritture], ricorrente: v.volte >= soglia }))));
  return out;
}

function vistaDomande({ domande, sbagliate }) {
  if (!domande.length) return el('p', { class: 'nota', text: 'Nessun dato con questi filtri.' });
  const soglia = config.tracciamento.soglia_ricorrente;
  const gruppi = raggruppaSbagliate(sbagliate, soglia);
  const ordinate = [...domande].map((d) => ({ ...d, gruppi: gruppi.get(`${d.gioco}|${d.domanda_id}`) || [] }))
    .sort((a, b) => b.gruppi.filter((x) => x.ricorrente).length - a.gruppi.filter((x) => x.ricorrente).length || b.sbagliate - a.sbagliate);
  return el('div', {},
    el('p', { class: 'nota' }, `In evidenza le risposte sbagliate date almeno ${soglia} volte (dopo normalizzazione): candidate da valutare come `, el('code', { text: 'varianti' }), ' nel JSON della partita.'),
    tabella([['Gioco'], ['Voce'], ['Risposta attesa'], ['Volte', 'num'], ['Sbagliate', 'num'], ['Scadute/passate', 'num'], ['Risposte sbagliate date']],
      ordinate.map((d) => el('tr', { dataset: { domanda: d.domanda_id }, class: d.gruppi.some((x) => x.ricorrente) ? 'ricorrente' : null },
        el('td', { text: NOMI[d.gioco] || d.gioco }), el('td', {}, el('code', { text: d.domanda_id })),
        el('td', { text: d.risposta_attesa }), el('td', { class: 'num', text: d.totale }),
        el('td', { class: 'num', text: `${d.sbagliate} (${pct(d.sbagliate, d.totale)})` }),
        el('td', { class: 'num', text: `${d.scadute} / ${d.passate}` }),
        el('td', {}, d.gruppi.length
          ? el('ul', { class: 'lista-sbagliate' }, d.gruppi.map((g) => el('li', { dataset: { normalizzata: g.normalizzata, volte: String(g.volte), ricorrente: String(g.ricorrente) } },
            g.ricorrente ? el('span', { class: 'ricorrente-badge', text: `ricorrente ×${g.volte} ` }) : `×${g.volte} `,
            el('code', { text: g.normalizzata }),
            g.scritture.length > 1 || g.scritture[0] !== g.normalizzata ? el('span', { class: 'nota', text: ' scritta come: ' + g.scritture.map((x) => `"${x}"`).join(', ') }) : null)))
          : '—'))),
      { id: 'vista-domande' }));
}

const RENDER = { partite: vistaPartite, partita: vistaPartita, giocatori: vistaGiocatori, domande: vistaDomande };

async function mostra(v) {
  vista = VISTE.includes(v) ? v : 'partite';
  sincronizzaURL();
  stato.textContent = 'Caricamento…';
  document.body.dataset.stato = 'caricamento';
  try {
    const dati = await api(vista);
    svuota(contenuto).append(RENDER[vista](dati));
    stato.textContent = AMBIENTE === 'production' ? '' : `Ambiente: ${AMBIENTE}`;
    document.body.dataset.stato = 'pronto';
  } catch (e) {
    svuota(contenuto);
    stato.textContent = 'Errore: ' + e.message;
    document.body.dataset.stato = 'errore';
  }
}

async function main() {
  config = await caricaConfig();
  const q = new URLSearchParams(location.search);
  try { await caricaFiltri(); } catch (e) { stato.textContent = 'Errore: ' + e.message; }
  document.querySelectorAll('#schede [data-vista]').forEach((b) => b.addEventListener('click', () => mostra(b.dataset.vista)));
  Object.values(sel).forEach((s) => s.addEventListener('change', async () => {
    document.body.dataset.stato = 'caricamento';
    mostra(vista);
  }));
  mostra(q.get('vista') || 'partite');
}

main();
