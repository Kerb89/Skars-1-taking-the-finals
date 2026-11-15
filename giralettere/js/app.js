// Orchestratore di una partita: carica contenuti e config, crea la sessione,
// fa girare le manche in sequenza da solo, converte i punti in secondi per la
// ruota finale. Nessun conduttore: il giocatore deve solo rispondere.

import { caricaConfig, caricaPartita, verificaPartita } from './core/contenuto.js';
import { CodaInvio } from './core/coda-invio.js';
import { Sessione } from './core/stato.js';
import { suoni } from './core/suoni.js';
import { el, svuota, fase } from './core/ui.js';
import { Timer } from './core/timer.js';

const GIOCHI = {
  parole: 'Parole impossibili',
  bocciato: 'Bocciato',
  elemento: 'Elemento comune',
  titolo: 'Completa il titolo',
  manolesta: 'Mano lesta',
  ruota: 'Ruota finale',
};

const $ = (s) => document.querySelector(s);

function errore(msg, dettagli = []) {
  fase('errore');
  const area = svuota($('#area'));
  area.append(el('section', { class: 'pannello errore', id: 'errore' },
    el('h2', { text: 'La partita non può partire' }), el('p', { text: msg }),
    dettagli.length ? el('ul', {}, dettagli.map((d) => el('li', { text: d }))) : null,
    el('a', { class: 'btn', href: '../', text: 'Torna alla home' })));
}

export function secondiRuota(totalePunti, cfg) {
  const s = cfg.secondi_base + totalePunti * cfg.secondi_per_punto;
  return Math.round(Math.min(cfg.secondi_massimi, Math.max(cfg.secondi_minimi, s)));
}

// Schermata di passaggio con conto alla rovescia automatico e bottone per
// anticipare. Risolve quando si prosegue.
function attesa({ id, titolo, corpo, secondi, etichetta = 'Inizia subito' }) {
  return new Promise((risolvi) => {
    const area = svuota($('#area'));
    const conto = el('span', { class: 'conto', id: 'conto' });
    let fatto = false;
    const vai = () => { if (fatto) return; fatto = true; t.ferma(); suoni.sblocca(); risolvi(); };
    const btn = el('button', { class: 'btn btn-primario', id, type: 'button', text: etichetta, onclick: vai });
    area.append(el('section', { class: 'pannello intro' }, el('h2', { text: titolo }), corpo,
      el('p', { class: 'auto' }, 'Si parte da solo tra ', conto), btn));
    const t = new Timer(secondi * 1000, {
      onTick: (r) => { conto.textContent = Math.ceil(r / 1000) + ' s'; },
      onScadenza: vai,
    }).avvia();
    btn.focus();
  });
}

async function main() {
  const qs = new URLSearchParams(location.search);
  const partitaId = qs.get('partita') || 'demo';
  const gioco = qs.get('gioco') || 'tutti';
  let nick = (qs.get('nick') || '').trim();
  if (!nick) { try { nick = (localStorage.getItem('giralettere.nick') || '').trim(); } catch (_) {} }
  if (!nick) { location.replace('../?partita=' + encodeURIComponent(partitaId)); return; }
  if (gioco !== 'tutti' && !GIOCHI[gioco]) return errore(`Gioco sconosciuto: "${gioco}"`);

  let config, partita;
  try {
    [config, partita] = await Promise.all([caricaConfig(), caricaPartita(partitaId)]);
  } catch (e) { return errore(e.message); }
  const problemi = verificaPartita(partita, config);
  if (problemi.length) return errore('Il file della partita non rispetta lo schema.', problemi);

  const sequenza = gioco === 'tutti'
    ? [...config.ordine_giochi.filter((g) => partita.giochi[g]), ...(partita.giochi.ruota ? ['ruota'] : [])]
    : [gioco];
  if (!sequenza.length || sequenza.some((g) => !partita.giochi[g])) {
    return errore(`La partita "${partita.id}" non contiene il gioco richiesto.`);
  }

  const coda = new CodaInvio({
    endpoint: config.rete.endpoint_sync, batchMax: config.rete.batch_max,
    retryBaseMs: config.rete.retry_base_ms, retryMaxMs: config.rete.retry_max_ms,
  });
  const statoInvio = $('#stato-invio');
  coda.onCambio((n) => {
    statoInvio.textContent = n === 0 ? 'Risposte salvate' : `In invio: ${n}`;
    statoInvio.dataset.inAttesa = String(n);
  });
  coda.invia(); // eventuali residui di partite precedenti

  const sessione = new Sessione({ coda, partitaId: partita.id, giocatore: nick, giocoAvviato: gioco });
  window.__giralettere = { sessione, coda, config, partita };
  $('#giocatore').textContent = nick;
  $('#partita').textContent = partita.titolo;
  const totale = () => Object.entries(sessione.punti).filter(([g]) => g !== 'ruota').reduce((s, [, p]) => s + p, 0);
  const aggiornaPunti = () => { $('#punti').textContent = String(totale()); };

  let risultatoRuota = null;
  let secondi = null;
  for (const g of sequenza) {
    $('#manche').textContent = GIOCHI[g];
    const modulo = await import(`./giochi/${g}.js`);
    const ctx = { config: config[g], flusso: config.flusso, contenuto: partita.giochi[g], sessione, suoni };
    if (g === 'ruota') {
      secondi = gioco === 'tutti' ? secondiRuota(totale(), config.ruota) : config.ruota.secondi_standalone;
      ctx.secondi = secondi;
      fase('intro:ruota');
      const corpo = el('div', {},
        gioco === 'tutti'
          ? el('p', { class: 'conversione', id: 'conversione' },
            `${totale()} punti × ${config.ruota.secondi_per_punto} + ${config.ruota.secondi_base} s base = `,
            el('strong', { id: 'secondi-ruota', text: `${secondi} secondi` }))
          : el('p', { class: 'conversione', id: 'conversione' }, 'Partita singola: ',
            el('strong', { id: 'secondi-ruota', text: `${secondi} secondi` })),
        el('p', { text: modulo.regole(ctx) }));
      await attesa({ id: 'btn-inizia', titolo: GIOCHI.ruota, corpo, secondi: config.flusso.intro_manche_s });
    } else {
      fase('intro:' + g);
      await attesa({ id: 'btn-inizia', titolo: GIOCHI[g], corpo: el('p', { text: modulo.regole(ctx) }), secondi: config.flusso.intro_manche_s });
    }
    fase('gioco:' + g);
    const area = svuota($('#area'));
    ctx.area = area;
    const ris = await modulo.gioca(ctx);
    sessione.impostaPunti(g, ris.punti);
    aggiornaPunti();
    if (g === 'ruota') risultatoRuota = ris;
    if (g !== sequenza[sequenza.length - 1]) {
      fase('riepilogo:' + g);
      await attesa({
        id: 'btn-avanti', titolo: `${GIOCHI[g]}: ${ris.punti} punti`, etichetta: 'Avanti',
        corpo: el('p', { class: 'riepilogo-testo', text: ris.riepilogo }), secondi: config.flusso.riepilogo_manche_s,
      });
    }
  }

  sessione.concludi({ secondiRuota: secondi });
  suoni.fine();
  fase('fine');
  const area = svuota($('#area'));
  const righe = sequenza.map((g) => el('tr', {}, el('td', { text: GIOCHI[g] }),
    el('td', { class: 'num', text: g === 'ruota' ? `${risultatoRuota?.corrette ?? 0} lettere` : `${sessione.punti[g]} punti` })));
  area.append(el('section', { class: 'pannello fine', id: 'fine' },
    el('h2', { text: `Partita finita, ${nick}!` }),
    el('table', { class: 'tabella-fine' }, el('tbody', {}, righe)),
    el('p', { class: 'nota', id: 'esito-invio' }, 'Le risposte vengono salvate anche se la rete cade: restano in coda e partono appena possibile.'),
    el('div', { class: 'azioni' },
      el('a', { class: 'btn btn-primario', href: location.href, id: 'rigioca', text: 'Rigioca' }),
      el('a', { class: 'btn', href: '../', text: 'Home' }),
      el('a', { class: 'btn', href: '../tracciamento/?partita=' + encodeURIComponent(partita.id) + '&giocatore=' + encodeURIComponent(nick), text: 'Tracciamento' }))));
}

main().catch((e) => { console.error(e); errore('Errore imprevisto: ' + e.message); });
