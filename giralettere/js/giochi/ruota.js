// Gioco 6 — Ruota finale: una definizione per ciascuna delle 21 lettere.
// Timer unico a scalare (secondi guadagnati nei giochi 1-5), fermo durante
// il feedback. "Passo" rimanda la lettera al giro successivo. Finisce a tempo
// scaduto o quando non restano lettere da fare o passate.

import { Timer, cronometro, attendi } from '../core/timer.js';
import { el, svuota, feedback, campoRisposta } from '../core/ui.js';
import { eAccettata } from '../core/normalizza.js';

const SVG = 'http://www.w3.org/2000/svg';
const s = (tag, attrs = {}, ...figli) => {
  const n = document.createElementNS(SVG, tag);
  Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
  figli.forEach((f) => n.append(f));
  return n;
};

export function regole() {
  return 'Una definizione per ogni lettera: la risposta inizia con la lettera, oppure la contiene se indicato. ' +
    'Con "Passo" la lettera torna al giro dopo. Il tempo scorre solo mentre una lettera è aperta.';
}

function disegnaRuota(lettere) {
  const C = 200, R1 = 192, R0 = 128, n = lettere.length, passo = (2 * Math.PI) / n;
  const pt = (r, a) => `${(C + r * Math.sin(a)).toFixed(2)} ${(C - r * Math.cos(a)).toFixed(2)}`;
  const spicchi = new Map();
  const svg = s('svg', { class: 'ruota-svg', viewBox: '0 0 400 400', role: 'img', 'aria-label': 'Ruota delle lettere' });
  lettere.forEach((l, i) => {
    const a0 = i * passo - passo / 2 + 0.01, a1 = a0 + passo - 0.02, am = i * passo;
    const d = `M ${pt(R0, a0)} L ${pt(R1, a0)} A ${R1} ${R1} 0 0 1 ${pt(R1, a1)} L ${pt(R0, a1)} A ${R0} ${R0} 0 0 0 ${pt(R0, a0)} Z`;
    const [tx, ty] = pt((R0 + R1) / 2, am).split(' ');
    const g = s('g', { 'data-lettera': l, 'data-stato': 'da_fare' }, s('path', { class: 'spicchio', d }), s('text', { x: tx, y: ty }, l));
    g.append(s('title', {}, `Lettera ${l}`));
    spicchi.set(l, g);
    svg.append(g);
  });
  const tempoTxt = s('text', { class: 'centro-tempo', x: C, y: C - 6, id: 'ruota-tempo' }, '');
  svg.append(s('circle', { class: 'centro', cx: C, cy: C, r: R0 - 12 }), tempoTxt,
    s('text', { class: 'centro-etichetta', x: C, y: C + 32 }, 'secondi'));
  return { svg, spicchi, tempoTxt };
}

export function gioca({ area, contenuto, flusso, sessione, suoni, secondi }) {
  return new Promise((fine) => {
    const voci = contenuto.voci;
    const { svg, spicchi, tempoTxt } = disegnaRuota(voci.map((v) => v.lettera));
    const stato = new Map(voci.map((v) => [v.id, 'da_fare']));
    const totaleMs = secondi * 1000;
    const infoLettera = el('p', { class: 'etichetta', id: 'regola-lettera' });
    const definizione = el('p', { class: 'domanda', id: 'domanda' });
    const esitoBox = el('div', { id: 'esito' });
    const azioni = el('div', { class: 'ruota-azioni' });
    const legenda = el('p', { class: 'legenda' },
      ...[['da fare', 'var(--neutro)'], ['corretta', 'var(--ok)'], ['sbagliata', 'var(--ko)'], ['passata', 'var(--passo)']]
        .map(([t, c]) => el('span', {}, el('i', { style: `background:${c}` }), t)));
    svuota(area).append(el('section', { class: 'pannello ruota-layout' }, svg, legenda, infoLettera, definizione, azioni, esitoBox));

    let giro = voci.slice();
    let prossimoGiro = [];
    let corrente = null;
    let finito = false;
    let misura = null;
    let campo = null;

    const imposta = (voce, st) => {
      stato.set(voce.id, st);
      spicchi.get(voce.lettera).setAttribute('data-stato', st);
    };
    const aggiornaTempo = (r) => { tempoTxt.textContent = String(Math.ceil(r / 1000)); tempoTxt.setAttribute('data-restante-ms', String(Math.round(r))); };
    const timer = new Timer(totaleMs, { onTick: aggiornaTempo, onScadenza: () => scaduto() });
    aggiornaTempo(totaleMs);

    const termina = () => {
      if (finito) return;
      finito = true;
      timer.ferma();
      spicchi.forEach((g) => g.classList.remove('corrente'));
      const corrette = [...stato.values()].filter((x) => x === 'corretta').length;
      const sbagliate = [...stato.values()].filter((x) => x === 'sbagliata').length;
      suoni.fine();
      fine({
        punti: corrette, corrette, sbagliate,
        riepilogo: `${corrette} lettere corrette, ${sbagliate} sbagliate, ${voci.length - corrette - sbagliate} non risolte.`,
      });
    };

    function scaduto() {
      if (finito || !corrente) return;
      campo?.disabilita();
      azioni.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      sessione.registra({ gioco: 'ruota', domanda_id: corrente.id, risposta_data: null, risposta_attesa: corrente.risposta, esito: 'tempo_scaduto', tempo_ms: misura() });
      suoni.sbagliata();
      feedback(esitoBox, 'tempo_scaduto', `Era: ${corrente.risposta}`);
      termina();
    }

    async function chiudiLettera(esito, testo) {
      if (finito) return;
      timer.pausa();
      campo.disabilita();
      azioni.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      const voce = corrente;
      sessione.registra({ gioco: 'ruota', domanda_id: voce.id, risposta_data: testo, risposta_attesa: voce.risposta, esito, tempo_ms: misura() });
      if (esito === 'passata') { imposta(voce, 'passata'); prossimoGiro.push(voce); suoni.passo(); feedback(esitoBox, 'passata', 'Torna al prossimo giro'); }
      else { imposta(voce, esito); if (esito === 'corretta') suoni.giusta(); else suoni.sbagliata(); feedback(esitoBox, esito, esito === 'corretta' ? '' : `Era: ${voce.risposta}`); }
      await attendi(flusso.pausa_feedback_ms);
      prossima();
    }

    function prossima() {
      if (finito) return;
      if (!giro.length) { giro = prossimoGiro; prossimoGiro = []; }
      if (!giro.length) { corrente = null; termina(); return; }
      corrente = giro.shift();
      spicchi.forEach((g, l) => g.classList.toggle('corrente', l === corrente.lettera));
      svg.setAttribute('data-corrente', corrente.lettera);
      infoLettera.textContent = corrente.regola === 'contiene' ? `Contiene la ${corrente.lettera}` : `Inizia con la ${corrente.lettera}`;
      infoLettera.dataset.lettera = corrente.lettera;
      definizione.textContent = corrente.definizione;
      svuota(esitoBox);
      campo = campoRisposta({ segnaposto: corrente.regola === 'contiene' ? `…${corrente.lettera}…` : `${corrente.lettera}…` });
      const passo = el('button', { class: 'btn', id: 'passo', type: 'button', text: 'Passo', onclick: () => chiudiLettera('passata', null) });
      svuota(azioni).append(campo.form, passo);
      const voce = corrente;
      const attendiInvio = (c) => c.inviata.then((t) => {
        if (finito || corrente !== voce || c !== campo) return;
        if (!String(t).trim()) {
          const nuovo = campoRisposta({ segnaposto: c.input.placeholder });
          c.form.replaceWith(nuovo.form); campo = nuovo; nuovo.focus();
          return attendiInvio(nuovo);
        }
        chiudiLettera(eAccettata(t, voce) ? 'corretta' : 'sbagliata', t);
      });
      attendiInvio(campo);
      misura = cronometro();
      timer.avvia();
      campo.focus();
    }

    prossima();
  });
}
