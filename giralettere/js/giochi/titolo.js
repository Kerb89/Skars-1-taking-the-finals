// Gioco 4 — Completa il titolo: titolo di una canzone con una parte mancante,
// da completare a testo libero.

import { el } from '../core/ui.js';
import { domandaLibera } from '../core/domanda.js';

export function regole({ config }) {
  return `Completa il titolo della canzone scrivendo solo la parte mancante. ` +
    `${config.tempo_domanda_s} secondi per titolo, ${config.punti_corretta} punti per risposta giusta.`;
}

function titoloConBuco(t) {
  const [prima, ...resto] = t.split('___');
  return el('p', { class: 'titolo-mascherato domanda', id: 'domanda' }, prima, el('span', { class: 'buco', 'aria-label': 'parte mancante', text: '_____' }), resto.join('___'));
}

export async function gioca({ area, config, flusso, contenuto, sessione, suoni }) {
  const voci = contenuto.voci;
  let giuste = 0;
  for (let i = 0; i < voci.length; i++) {
    const v = voci[i];
    const { esito } = await domandaLibera({
      area, gioco: 'titolo', voce: v, sessione, suoni, flusso, tempoMs: config.tempo_domanda_s * 1000,
      segnaposto: 'Parte mancante',
      intestazione: [
        el('p', { class: 'progresso', id: 'progresso', text: `Titolo ${i + 1} di ${voci.length}` }),
        el('p', { class: 'artista', id: 'artista', text: v.artista }),
        titoloConBuco(v.titolo_mascherato),
      ],
    });
    if (esito === 'corretta') giuste++;
  }
  return { punti: giuste * config.punti_corretta, riepilogo: `${giuste} titoli completati su ${voci.length}.` };
}
