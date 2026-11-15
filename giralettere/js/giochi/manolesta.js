// Gioco 5 — Mano lesta: domanda + lettera iniziale obbligata. Si hanno pochi
// secondi (config) per INIZIARE a scrivere; poi parte il tempo di risposta,
// che si ferma all'invio. Errore o tempo scaduto chiudono la manche.
// I punti crescono con la serie di risposte corrette consecutive.

import { Timer, cronometro, attendi } from '../core/timer.js';
import { el, svuota, barraTempo, feedback, campoRisposta } from '../core/ui.js';
import { eAccettata } from '../core/normalizza.js';

export function regole({ config }) {
  return `Hai ${config.tempo_inizio_s} secondi per iniziare a scrivere, poi ${config.tempo_risposta_s} per inviare. ` +
    `La risposta deve iniziare con la lettera indicata. Al primo errore o tempo scaduto la manche finisce. ` +
    `La prima risposta vale ${config.punti_primo_in_serie} punti, ogni risposta di fila ne vale ${config.incremento_serie} in più.`;
}

export const puntiSerie = (n, c) => n * c.punti_primo_in_serie + c.incremento_serie * (n * (n - 1)) / 2;

function chiedi({ area, voce, indice, totale, serie, config, sessione }) {
  return new Promise((risolvi) => {
    const inizioMs = config.tempo_inizio_s * 1000;
    const rispostaMs = config.tempo_risposta_s * 1000;
    const tempo = barraTempo('Tempo per iniziare a rispondere');
    const fasePill = el('p', { class: 'etichetta', id: 'fase-mano', dataset: { fase: 'inizio' }, text: 'Inizia a scrivere!' });
    let timer = null;
    let fatto = false;
    const misura = cronometro();

    const chiudi = (testo) => {
      if (fatto) return;
      fatto = true;
      timer.ferma();
      campo.disabilita();
      const esito = testo == null ? 'tempo_scaduto' : (eAccettata(testo, voce) ? 'corretta' : 'sbagliata');
      sessione.registra({
        gioco: 'manolesta', domanda_id: voce.id, risposta_data: testo, risposta_attesa: voce.risposta,
        esito, tempo_ms: misura(),
      });
      risolvi(esito);
    };

    const campo = campoRisposta({
      segnaposto: `${voce.lettera}…`,
      onPrimoTasto: () => {
        if (fatto) return;
        timer.ferma();
        fasePill.dataset.fase = 'risposta';
        fasePill.textContent = 'Ora invia la risposta';
        timer = new Timer(rispostaMs, { onTick: (r) => tempo.aggiorna(r, rispostaMs), onScadenza: () => chiudi(null) }).avvia();
      },
    });
    const attendiInvio = () => campo.inviata.then((t) => {
      if (fatto) return;
      if (!String(t).trim()) {
        const nuovo = campoRisposta({ segnaposto: `${voce.lettera}…` });
        campo.form.replaceWith(nuovo.form); Object.assign(campo, nuovo); nuovo.focus();
        return attendiInvio();
      }
      chiudi(t);
    });

    svuota(area).append(el('section', { class: 'pannello' },
      el('p', { class: 'progresso', id: 'progresso' }, `Domanda ${indice + 1} di ${totale} · serie: `,
        el('span', { class: 'serie', id: 'serie', text: String(serie) })),
      fasePill, tempo.nodo,
      el('p', { class: 'lettera-grande', id: 'lettera', 'aria-label': 'Lettera iniziale ' + voce.lettera, text: voce.lettera }),
      el('p', { class: 'domanda', id: 'domanda', text: voce.domanda }),
      campo.form, el('div', { id: 'esito' })));
    timer = new Timer(inizioMs, { onTick: (r) => tempo.aggiorna(r, inizioMs), onScadenza: () => chiudi(null) }).avvia();
    attendiInvio();
    campo.focus();
  });
}

export async function gioca({ area, config, flusso, contenuto, sessione, suoni }) {
  const voci = contenuto.voci;
  let serie = 0;
  let ultimoEsito = null;
  for (let i = 0; i < voci.length; i++) {
    const v = voci[i];
    ultimoEsito = await chiedi({ area, voce: v, indice: i, totale: voci.length, serie, config, sessione });
    const box = area.querySelector('#esito');
    if (ultimoEsito === 'corretta') {
      serie++;
      suoni.giusta();
      area.querySelector('#serie').textContent = String(serie);
      feedback(box, 'corretta', `Serie: ${serie}`);
    } else {
      suoni.sbagliata();
      feedback(box, ultimoEsito, `Risposta: ${v.risposta}`);
    }
    await attendi(flusso.pausa_feedback_ms);
    if (ultimoEsito !== 'corretta') break;
  }
  return {
    punti: puntiSerie(serie, config),
    riepilogo: serie === voci.length ? `Serie perfetta: ${serie} di fila!` : `Serie di ${serie} risposte di fila.`,
  };
}
