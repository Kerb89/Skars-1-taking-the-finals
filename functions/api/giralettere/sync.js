// POST /api/giralettere/sync — riceve sessioni e risposte dalla coda client.
// Idempotente: sessioni in upsert (campi immutabili mai sovrascritti),
// risposte con INSERT OR IGNORE sull'id client. Restituisce gli id accettati
// (inclusi i duplicati già presenti) e quelli scartati perché non validi.

import { GIOCHI, ESITI, ambienteDa, json, db } from './_comune.js';

const MAX_TESTO = 500;
const MAX_ELEMENTI = 200;
const ID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;

const testo = (v, obbligatorio = true) => {
  if (v == null) return obbligatorio ? undefined : null;
  if (typeof v !== 'string') return undefined;
  const s = v.slice(0, MAX_TESTO);
  return obbligatorio && !s.trim() ? undefined : s;
};

function validaSessione(s) {
  if (!s || !ID_RE.test(s.id || '')) return null;
  const out = { id: s.id };
  for (const k of ['partita_id', 'giocatore', 'gioco_avviato', 'avviata_at']) {
    if (s[k] !== undefined) { const v = testo(s[k]); if (v === undefined) return null; out[k] = v; }
  }
  if (out.gioco_avviato && out.gioco_avviato !== 'tutti' && !GIOCHI.includes(out.gioco_avviato)) return null;
  for (const k of ['avviata_at', 'conclusa_at']) if (s[k] != null && !ISO_RE.test(s[k])) return null;
  if (s.conclusa_at != null) out.conclusa_at = s.conclusa_at;
  if (s.punti_json != null) {
    if (typeof s.punti_json !== 'string' || s.punti_json.length > 2000) return null;
    try { JSON.parse(s.punti_json); } catch (_) { return null; }
    out.punti_json = s.punti_json;
  }
  if (s.secondi_ruota != null) {
    if (!Number.isInteger(s.secondi_ruota) || s.secondi_ruota < 0 || s.secondi_ruota > 3600) return null;
    out.secondi_ruota = s.secondi_ruota;
  }
  return out;
}

function validaRisposta(r) {
  if (!r || !ID_RE.test(r.id || '') || !ID_RE.test(r.sessione_id || '')) return null;
  if (!GIOCHI.includes(r.gioco) || !ESITI.includes(r.esito)) return null;
  if (!Number.isInteger(r.ordine) || r.ordine < 1) return null;
  if (r.tempo_ms != null && (!Number.isInteger(r.tempo_ms) || r.tempo_ms < 0 || r.tempo_ms > 3_600_000)) return null;
  if (!ISO_RE.test(r.client_ts || '')) return null;
  const out = {
    id: r.id, sessione_id: r.sessione_id, gioco: r.gioco, esito: r.esito, ordine: r.ordine,
    tempo_ms: r.tempo_ms ?? null, client_ts: r.client_ts,
    partita_id: testo(r.partita_id), giocatore: testo(r.giocatore), domanda_id: testo(r.domanda_id),
    risposta_attesa: testo(r.risposta_attesa), risposta_data: testo(r.risposta_data, false),
  };
  return Object.values(out).some((v) => v === undefined) ? null : out;
}

export async function onRequestPost({ request, env }) {
  let corpo;
  try { corpo = await request.json(); } catch (_) { return json({ errore: 'JSON non valido' }, 400); }
  const sessioniIn = Array.isArray(corpo.sessioni) ? corpo.sessioni : [];
  const risposteIn = Array.isArray(corpo.risposte) ? corpo.risposte : [];
  if (sessioniIn.length + risposteIn.length > MAX_ELEMENTI) return json({ errore: 'troppi elementi' }, 413);

  let D;
  try { D = db(env); } catch (e) { return json({ errore: e.message }, 503); }
  const ambiente = ambienteDa(request, env);
  const accettate = { sessioni: [], risposte: [] };
  const scartate = { sessioni: [], risposte: [] };
  const stmt = [];

  const sessioni = [];
  for (const s of sessioniIn) {
    const v = validaSessione(s);
    if (!v) { if (s && typeof s.id === 'string') scartate.sessioni.push(s.id); continue; }
    sessioni.push(v);
  }
  // Le sessioni nuove richiedono i campi di creazione; gli aggiornamenti no.
  const idSessioni = sessioni.map((s) => s.id);
  const esistenti = new Set();
  if (idSessioni.length) {
    const ph = idSessioni.map(() => '?').join(',');
    const { results } = await D.prepare(`SELECT id FROM sessioni WHERE id IN (${ph})`).bind(...idSessioni).all();
    results.forEach((r) => esistenti.add(r.id));
  }
  for (const s of sessioni) {
    if (!esistenti.has(s.id)) {
      if (!s.partita_id || !s.giocatore || !s.gioco_avviato || !s.avviata_at) { scartate.sessioni.push(s.id); continue; }
      stmt.push(D.prepare(
        `INSERT INTO sessioni (id, partita_id, giocatore, gioco_avviato, ambiente, punti_json, secondi_ruota, avviata_at, conclusa_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING`
      ).bind(s.id, s.partita_id, s.giocatore, s.gioco_avviato, ambiente, s.punti_json ?? null,
        s.secondi_ruota ?? null, s.avviata_at, s.conclusa_at ?? null));
      esistenti.add(s.id);
    }
    // Aggiornamento dei soli campi mutabili; ambiente, giocatore e partita restano quelli di creazione.
    stmt.push(D.prepare(
      `UPDATE sessioni SET punti_json = COALESCE(?, punti_json), secondi_ruota = COALESCE(?, secondi_ruota),
       conclusa_at = COALESCE(?, conclusa_at) WHERE id = ?`
    ).bind(s.punti_json ?? null, s.secondi_ruota ?? null, s.conclusa_at ?? null, s.id));
    accettate.sessioni.push(s.id);
  }

  // Le risposte devono appartenere a una sessione esistente o in arrivo.
  const risposte = [];
  for (const r of risposteIn) {
    const v = validaRisposta(r);
    if (!v) { if (r && typeof r.id === 'string') scartate.risposte.push(r.id); continue; }
    risposte.push(v);
  }
  const mancanti = [...new Set(risposte.map((r) => r.sessione_id).filter((id) => !esistenti.has(id)))];
  if (mancanti.length) {
    const ph = mancanti.map(() => '?').join(',');
    const { results } = await D.prepare(`SELECT id FROM sessioni WHERE id IN (${ph})`).bind(...mancanti).all();
    results.forEach((r) => esistenti.add(r.id));
  }
  for (const r of risposte) {
    if (!esistenti.has(r.sessione_id)) { scartate.risposte.push(r.id); continue; }
    stmt.push(D.prepare(
      `INSERT OR IGNORE INTO risposte (id, sessione_id, partita_id, giocatore, gioco, domanda_id, ordine,
       risposta_data, risposta_attesa, esito, tempo_ms, client_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(r.id, r.sessione_id, r.partita_id, r.giocatore, r.gioco, r.domanda_id, r.ordine,
      r.risposta_data, r.risposta_attesa, r.esito, r.tempo_ms, r.client_ts));
    accettate.risposte.push(r.id);
  }

  if (stmt.length) {
    try { await D.batch(stmt); } catch (e) { return json({ errore: 'scrittura fallita: ' + e.message }, 500); }
  }
  return json({ ambiente, accettate, scartate });
}
