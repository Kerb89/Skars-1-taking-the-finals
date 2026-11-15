// Gioco 1 — Parole impossibili: 8 parole rare da abbinare a 8 definizioni
// entro il tempo. Un abbinamento sbagliato fa ripartire la sequenza da zero.
// Bonus se si chiudono tutti e 8 gli abbinamenti.

import { Timer, cronometro } from '../core/timer.js';
import { el, barraTempo, mescola } from '../core/ui.js';

export function regole({ config }) {
  return `Abbina le 8 parole alle loro definizioni in ${config.durata_s} secondi. ` +
    `Se sbagli un abbinamento, tutti quelli fatti si annullano e riparti da zero. ` +
    `${config.punti_per_abbinamento} punti per abbinamento valido alla fine, ` +
    `+${config.bonus_completamento} se li chiudi tutti.`;
}

export function gioca({ area, config, contenuto, sessione, suoni }) {
  return new Promise((fine) => {
    const voci = contenuto.voci;
    const totaleMs = config.durata_s * 1000;
    const tempo = barraTempo('Tempo per gli abbinamenti');
    const stato = el('p', { class: 'progresso', id: 'progresso' });
    const colParole = el('div', { class: 'colonna', role: 'group', 'aria-label': 'Parole' });
    const colDef = el('div', { class: 'colonna', role: 'group', 'aria-label': 'Definizioni' });
    area.append(el('section', { class: 'pannello' },
      el('p', { class: 'etichetta', text: 'Parole impossibili' }), tempo.nodo, stato,
      el('div', { class: 'abbinamento' }, colParole, colDef)));

    const abbinate = new Set();
    let selParola = null;
    let selDef = null;
    let finito = false;
    let tempoAttesa = cronometro();
    const bottoniParola = new Map();
    const bottoniDef = new Map();

    const aggiornaStato = () => { stato.textContent = `Abbinate: ${abbinate.size} / ${voci.length}`; stato.dataset.abbinate = String(abbinate.size); };

    const seleziona = (mappa, id) => mappa.forEach((b, k) => b.classList.toggle('selezionata', k === id));

    const chiudi = (motivo) => {
      if (finito) return;
      finito = true;
      timer.ferma();
      if (motivo === 'tempo') {
        voci.filter((v) => !abbinate.has(v.id)).forEach((v) => sessione.registra({
          gioco: 'parole', domanda_id: v.id, risposta_data: null, risposta_attesa: v.definizione,
          esito: 'tempo_scaduto', tempo_ms: null,
        }));
        suoni.sbagliata();
      } else suoni.fine();
      [...bottoniParola.values(), ...bottoniDef.values()].forEach((b) => { b.disabled = true; });
      const completo = abbinate.size === voci.length;
      const punti = abbinate.size * config.punti_per_abbinamento + (completo ? config.bonus_completamento : 0);
      fine({
        punti,
        riepilogo: completo
          ? `Tutte e ${voci.length} abbinate: bonus di ${config.bonus_completamento} punti!`
          : `Tempo scaduto con ${abbinate.size} abbinamenti validi su ${voci.length}.`,
      });
    };

    const valuta = () => {
      const voce = voci.find((v) => v.id === selParola);
      const scelta = voci.find((v) => v.id === selDef);
      const ok = voce.id === scelta.id;
      sessione.registra({
        gioco: 'parole', domanda_id: voce.id, risposta_data: scelta.definizione,
        risposta_attesa: voce.definizione, esito: ok ? 'corretta' : 'sbagliata', tempo_ms: tempoAttesa(),
      });
      tempoAttesa = cronometro();
      const bp = bottoniParola.get(selParola);
      const bd = bottoniDef.get(selDef);
      selParola = selDef = null;
      seleziona(bottoniParola, null); seleziona(bottoniDef, null);
      if (ok) {
        suoni.giusta();
        abbinate.add(voce.id);
        [bp, bd].forEach((b) => { b.classList.add('abbinata'); b.disabled = true; });
        aggiornaStato();
        if (abbinate.size === voci.length) chiudi('completo');
      } else {
        suoni.sbagliata();
        [bp, bd].forEach((b) => { b.classList.remove('errore'); void b.offsetWidth; b.classList.add('errore'); });
        abbinate.clear();
        [...bottoniParola.values(), ...bottoniDef.values()].forEach((b) => { b.classList.remove('abbinata'); b.disabled = false; });
        aggiornaStato();
      }
    };

    mescola(voci).forEach((v) => {
      const b = el('button', { class: 'tessera', type: 'button', dataset: { tipo: 'parola', id: v.id }, text: v.parola,
        onclick: () => { if (finito || abbinate.has(v.id)) return; selParola = v.id; seleziona(bottoniParola, v.id); if (selDef) valuta(); } });
      bottoniParola.set(v.id, b); colParole.append(b);
    });
    mescola(voci).forEach((v) => {
      const b = el('button', { class: 'tessera', type: 'button', dataset: { tipo: 'definizione', id: v.id }, text: v.definizione,
        onclick: () => { if (finito || abbinate.has(v.id)) return; selDef = v.id; seleziona(bottoniDef, v.id); if (selParola) valuta(); } });
      bottoniDef.set(v.id, b); colDef.append(b);
    });

    aggiornaStato();
    const timer = new Timer(totaleMs, { onTick: (r) => tempo.aggiorna(r, totaleMs), onScadenza: () => chiudi('tempo') }).avvia();
  });
}
