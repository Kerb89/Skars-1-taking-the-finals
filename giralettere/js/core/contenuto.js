// Caricamento di config e partita + verifica dei vincoli documentati in
// partite/SCHEMA.md. Se un vincolo fallisce la partita non parte.

import { normalizza } from './normalizza.js';

const BASE = new URL('../../', import.meta.url);

export async function caricaJSON(percorso) {
  const res = await fetch(new URL(percorso, BASE), { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Impossibile caricare ${percorso} (HTTP ${res.status})`);
  return res.json();
}

export const caricaConfig = () => caricaJSON('config.json');

export async function caricaPartita(id) {
  const indice = await caricaJSON('partite/index.json');
  const voce = indice.partite.find((p) => p.id === id);
  if (!voce) throw new Error(`Partita "${id}" non trovata in partite/index.json`);
  const partita = await caricaJSON('partite/' + voce.file);
  if (partita.id !== id) throw new Error(`Il file ${voce.file} ha id "${partita.id}", atteso "${id}"`);
  return partita;
}

function forme(v) { return [v.risposta, ...(v.varianti || [])].map(normalizza); }

export function verificaPartita(p, config) {
  const err = [];
  const g = p.giochi || {};
  const idVisti = new Set();
  const controllaId = (gioco, voci) => voci.forEach((v, i) => {
    if (!v.id) err.push(`${gioco}[${i}]: id mancante`);
    else if (idVisti.has(v.id)) err.push(`${gioco}: id duplicato "${v.id}"`);
    else idVisti.add(v.id);
  });
  const controllaLibere = (gioco, voci) => voci.forEach((v) => {
    if (!normalizza(v.risposta)) err.push(`${gioco}/${v.id}: risposta vuota`);
    if (!Array.isArray(v.varianti)) err.push(`${gioco}/${v.id}: varianti deve essere un array`);
  });

  if (!p.id || !/^[a-z0-9-]+$/.test(p.id)) err.push('id partita mancante o non valido');
  if (typeof p.demo !== 'boolean') err.push('campo "demo" mancante');

  if (g.parole) {
    const v = g.parole.voci || [];
    if (v.length !== 8) err.push(`parole: servono esattamente 8 voci, trovate ${v.length}`);
    controllaId('parole', v);
  }
  if (g.bocciato) {
    const d = g.bocciato.domande || [];
    if (d.length !== 12) err.push(`bocciato: servono esattamente 12 domande, trovate ${d.length}`);
    controllaId('bocciato', d);
    d.forEach((q) => {
      if (!Array.isArray(q.opzioni) || q.opzioni.length !== 2) err.push(`bocciato/${q.id}: servono 2 opzioni`);
      if (q.corretta !== 0 && q.corretta !== 1) err.push(`bocciato/${q.id}: corretta deve essere 0 o 1`);
    });
  }
  if (g.elemento) {
    const e = g.elemento;
    const el = normalizza(e.elemento);
    if (!el) err.push('elemento: "elemento" vuoto');
    if (!['prefisso', 'suffisso'].includes(e.tipo)) err.push('elemento: tipo deve essere prefisso o suffisso');
    controllaId('elemento', e.voci || []);
    controllaLibere('elemento', e.voci || []);
    (e.voci || []).forEach((v) => forme(v).forEach((f) => {
      const ok = e.tipo === 'prefisso' ? f.startsWith(el) : f.endsWith(el);
      if (!ok) err.push(`elemento/${v.id}: "${f}" non ha il ${e.tipo} "${el}"`);
    }));
  }
  if (g.titolo) {
    controllaId('titolo', g.titolo.voci || []);
    controllaLibere('titolo', g.titolo.voci || []);
    (g.titolo.voci || []).forEach((v) => {
      if (!String(v.titolo_mascherato || '').includes('___')) err.push(`titolo/${v.id}: titolo_mascherato senza "___"`);
    });
  }
  if (g.manolesta) {
    controllaId('manolesta', g.manolesta.voci || []);
    controllaLibere('manolesta', g.manolesta.voci || []);
    (g.manolesta.voci || []).forEach((v) => forme(v).forEach((f) => {
      if (!f.startsWith(String(v.lettera || '').toLowerCase())) err.push(`manolesta/${v.id}: "${f}" non inizia con ${v.lettera}`);
    }));
  }
  if (g.ruota) {
    const v = g.ruota.voci || [];
    const lettere = config.ruota.lettere;
    if (v.length !== lettere.length) err.push(`ruota: servono ${lettere.length} voci, trovate ${v.length}`);
    controllaId('ruota', v);
    controllaLibere('ruota', v);
    v.forEach((voce, i) => {
      if (voce.lettera !== lettere[i]) err.push(`ruota: posizione ${i + 1} ha lettera "${voce.lettera}", attesa "${lettere[i]}"`);
      const l = String(voce.lettera || '').toLowerCase();
      forme(voce).forEach((f) => {
        const ok = voce.regola === 'contiene' ? f.includes(l) : f.startsWith(l);
        if (!ok) err.push(`ruota/${voce.id}: "${f}" non ${voce.regola === 'contiene' ? 'contiene' : 'inizia con'} ${voce.lettera}`);
      });
    });
  }
  return err;
}
