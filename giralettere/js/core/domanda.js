// Domanda a testo libero con timer: il tempo si ferma all'invio (non durante
// la digitazione), la risposta è valutata contro risposta + varianti dopo
// normalizzazione, e viene registrata così come è stata scritta.

import { Timer, cronometro, attendi } from './timer.js';
import { el, svuota, barraTempo, feedback, campoRisposta } from './ui.js';
import { eAccettata } from './normalizza.js';

export function domandaLibera({ area, intestazione, tempoMs, gioco, voce, sessione, suoni, flusso, segnaposto }) {
  return new Promise((risolvi) => {
    const tempo = barraTempo('Tempo per rispondere');
    const campo = campoRisposta({ segnaposto });
    const esitoBox = el('div', { id: 'esito' });
    svuota(area).append(el('section', { class: 'pannello' }, tempo.nodo, ...intestazione, campo.form, esitoBox));
    const misura = cronometro();
    let fatto = false;

    const chiudi = async (testo) => {
      if (fatto) return;
      fatto = true;
      timer.ferma();
      campo.disabilita();
      const esito = testo == null ? 'tempo_scaduto' : (eAccettata(testo, voce) ? 'corretta' : 'sbagliata');
      sessione.registra({
        gioco, domanda_id: voce.id, risposta_data: testo, risposta_attesa: voce.risposta, esito,
        tempo_ms: testo == null ? tempoMs : misura(),
      });
      if (esito === 'corretta') suoni.giusta(); else suoni.sbagliata();
      feedback(esitoBox, esito, esito === 'corretta' ? '' : `Risposta: ${voce.risposta}`);
      await attendi(flusso.pausa_feedback_ms);
      risolvi({ esito, testo });
    };

    const timer = new Timer(tempoMs, { onTick: (r) => tempo.aggiorna(r, tempoMs), onScadenza: () => chiudi(null) }).avvia();
    const attendiInvio = () => campo.inviata.then((t) => {
      if (fatto) return;
      if (!String(t).trim()) {   // invio vuoto: ignorato, si continua a rispondere
        const nuovo = campoRisposta({ segnaposto });
        campo.form.replaceWith(nuovo.form);
        Object.assign(campo, nuovo);
        nuovo.focus();
        return attendiInvio();
      }
      return chiudi(t);
    });
    attendiInvio();
    campo.focus();
  });
}
