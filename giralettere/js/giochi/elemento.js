// Gioco 3 — Elemento comune: una serie di definizioni le cui risposte
// condividono lo stesso prefisso o suffisso, dichiarato a inizio serie.
// Risposta a testo libero; si risponde con la parola intera.

import { el } from '../core/ui.js';
import { domandaLibera } from '../core/domanda.js';

export function regole({ config, contenuto }) {
  return `Tutte le risposte ${contenuto.tipo === 'prefisso' ? 'iniziano' : 'finiscono'} con "${contenuto.elemento.toUpperCase()}". ` +
    `Scrivi la parola intera. ${config.tempo_domanda_s} secondi per definizione, ${config.punti_corretta} punti per risposta giusta.`;
}

export async function gioca({ area, config, flusso, contenuto, sessione, suoni }) {
  const voci = contenuto.voci;
  let giuste = 0;
  for (let i = 0; i < voci.length; i++) {
    const v = voci[i];
    const { esito } = await domandaLibera({
      area, gioco: 'elemento', voce: v, sessione, suoni, flusso, tempoMs: config.tempo_domanda_s * 1000,
      segnaposto: contenuto.tipo === 'prefisso' ? `${contenuto.elemento}…` : `…${contenuto.elemento}`,
      intestazione: [
        el('p', { class: 'elemento-dichiarato', id: 'elemento' }, `${contenuto.tipo === 'prefisso' ? 'Prefisso' : 'Suffisso'} comune: `,
          el('strong', { text: contenuto.elemento.toUpperCase() })),
        el('p', { class: 'progresso', id: 'progresso', text: `Definizione ${i + 1} di ${voci.length}` }),
        el('p', { class: 'domanda', id: 'domanda', text: v.definizione }),
      ],
    });
    if (esito === 'corretta') giuste++;
  }
  return { punti: giuste * config.punti_corretta, riepilogo: `${giuste} risposte giuste su ${voci.length}.` };
}
