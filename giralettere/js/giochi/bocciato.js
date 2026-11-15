// Gioco 2 — Bocciato: 12 domande a due opzioni. Il primo errore è tollerato
// (soglia in config), al successivo il giocatore è bocciato e la manche finisce.
// Il tempo scaduto conta come errore.

import { Timer, cronometro, attendi } from '../core/timer.js';
import { el, svuota, barraTempo, feedback } from '../core/ui.js';

export function regole({ config }) {
  const t = config.errori_tollerati;
  return `12 domande, due risposte possibili, ${config.tempo_domanda_s} secondi ciascuna. ` +
    `${t === 1 ? 'Il primo errore è tollerato' : `Sono tollerati ${t} errori`}: a quello dopo sei bocciato. ` +
    `${config.punti_corretta} punti per ogni risposta giusta.`;
}

function chiedi({ area, domanda, indice, totale, errori, config, sessione }) {
  return new Promise((risolvi) => {
    const totaleMs = config.tempo_domanda_s * 1000;
    const tempo = barraTempo('Tempo per la domanda');
    let fatto = false;
    const misura = cronometro();
    const chiudi = (scelta) => {
      if (fatto) return;
      fatto = true;
      timer.ferma();
      bottoni.forEach((b) => { b.disabled = true; });
      const esito = scelta == null ? 'tempo_scaduto' : (scelta === domanda.corretta ? 'corretta' : 'sbagliata');
      sessione.registra({
        gioco: 'bocciato', domanda_id: domanda.id,
        risposta_data: scelta == null ? null : domanda.opzioni[scelta],
        risposta_attesa: domanda.opzioni[domanda.corretta], esito,
        tempo_ms: scelta == null ? totaleMs : misura(),
      });
      risolvi({ esito, scelta });
    };
    const bottoni = domanda.opzioni.map((o, i) => el('button', {
      class: 'btn btn-grande opzione', type: 'button', dataset: { indice: String(i) }, text: o, onclick: () => chiudi(i),
    }));
    svuota(area).append(el('section', { class: 'pannello' },
      el('p', { class: 'progresso', id: 'progresso' }, `Domanda ${indice + 1} di ${totale} · `,
        el('span', { id: 'errori', dataset: { errori: String(errori) } }, `errori: ${errori} (tollerati: ${config.errori_tollerati})`)),
      tempo.nodo, el('p', { class: 'domanda', id: 'domanda', text: domanda.testo }),
      el('div', { class: 'due-opzioni' }, bottoni), el('div', { id: 'esito' })));
    const timer = new Timer(totaleMs, { onTick: (r) => tempo.aggiorna(r, totaleMs), onScadenza: () => chiudi(null) }).avvia();
    bottoni[0].focus();
  });
}

export async function gioca({ area, config, flusso, contenuto, sessione, suoni }) {
  const domande = contenuto.domande;
  let errori = 0;
  let giuste = 0;
  let bocciato = false;
  for (let i = 0; i < domande.length; i++) {
    const d = domande[i];
    const { esito } = await chiedi({ area, domanda: d, indice: i, totale: domande.length, errori, config, sessione });
    if (esito === 'corretta') { giuste++; suoni.giusta(); } else { errori++; suoni.sbagliata(); }
    bocciato = errori > config.errori_tollerati;
    const box = area.querySelector('#esito');
    feedback(box, esito, esito === 'corretta' ? '' : `Era: ${d.opzioni[d.corretta]}`);
    if (bocciato) box.append(el('p', { class: 'bocciato', id: 'bocciato', text: 'Bocciato!' }));
    await attendi(flusso.pausa_feedback_ms);
    if (bocciato) break;
  }
  return {
    punti: giuste * config.punti_corretta,
    riepilogo: bocciato
      ? `Bocciato dopo ${giuste} risposte giuste.`
      : `Promosso: ${giuste} giuste su ${domande.length}, ${errori} errori.`,
  };
}
