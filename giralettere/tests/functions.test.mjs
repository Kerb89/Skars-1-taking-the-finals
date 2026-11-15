// Test delle Pages Functions di Giralettere con un D1 finto su node:sqlite
// e lo schema reale (db/schema.sql). Eseguito da run_tests.py, oppure:
//   node --test giralettere/tests/functions.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';
import { randomUUID } from 'node:crypto';

const root = new URL('../../', import.meta.url);
const { onRequestPost } = await import(new URL('functions/api/giralettere/sync.js', root));
const { onRequestGet } = await import(new URL('functions/api/giralettere/tracciamento.js', root));

function fintoD1() {
  const db = new DatabaseSync(':memory:');
  db.exec('PRAGMA foreign_keys = ON;');
  db.exec(readFileSync(fileURLToPath(new URL('giralettere/db/schema.sql', root)), 'utf8'));
  const prepara = (sql) => {
    const st = { args: [] };
    st.bind = (...a) => { st.args = a; return st; };
    st.all = async () => ({ results: db.prepare(sql).all(...st.args) });
    st._run = () => db.prepare(sql).run(...st.args);
    st.run = async () => st._run();
    return st;
  };
  return {
    db,
    prepare: prepara,
    async batch(stmts) {           // atomico come D1
      db.exec('BEGIN');
      try { stmts.forEach((s) => s._run()); db.exec('COMMIT'); } catch (e) { db.exec('ROLLBACK'); throw e; }
    },
  };
}

const PROD = 'https://skars-1.pages.dev';
const PREV = 'https://feat-giralettere.skars-1.pages.dev';
const ora = () => new Date().toISOString();

async function sync(env, host, corpo) {
  const res = await onRequestPost({ request: new Request(host + '/api/giralettere/sync', { method: 'POST', body: JSON.stringify(corpo) }), env });
  return { status: res.status, ...(await res.json()) };
}
async function leggi(env, host, q) {
  const res = await onRequestGet({ request: new Request(host + '/api/giralettere/tracciamento?' + new URLSearchParams(q)), env });
  return { status: res.status, ...(await res.json()) };
}
const sessione = (extra = {}) => ({ id: randomUUID(), partita_id: 'demo', giocatore: 'Ada', gioco_avviato: 'tutti', avviata_at: ora(), ...extra });
const risposta = (sid, extra = {}) => ({
  id: randomUUID(), sessione_id: sid, partita_id: 'demo', giocatore: 'Ada', gioco: 'ruota', domanda_id: 'ru-A',
  ordine: 1, risposta_data: 'automobile', risposta_attesa: 'aereo', esito: 'sbagliata', tempo_ms: 1200, client_ts: ora(), ...extra,
});

test('sync è idempotente: reinvii non duplicano', async () => {
  const D = fintoD1(); const env = { GIRALETTERE_DB: D };
  const s = sessione(); const r1 = risposta(s.id); const r2 = risposta(s.id, { ordine: 2, domanda_id: 'ru-B', esito: 'corretta', risposta_data: 'banana', risposta_attesa: 'banana' });
  const a = await sync(env, PREV, { sessioni: [s], risposte: [r1, r2] });
  assert.equal(a.status, 200);
  assert.deepEqual(a.accettate.risposte.sort(), [r1.id, r2.id].sort());
  const b = await sync(env, PREV, { sessioni: [s], risposte: [r1, r2] });
  assert.deepEqual(b.accettate.risposte.sort(), [r1.id, r2.id].sort(), 'i duplicati risultano accettati');
  assert.equal(D.db.prepare('SELECT COUNT(*) n FROM risposte').get().n, 2);
  assert.equal(D.db.prepare('SELECT COUNT(*) n FROM sessioni').get().n, 1);
});

test('ambiente deciso dall\'host, mai dal client; campi di creazione immutabili', async () => {
  const D = fintoD1(); const env = { GIRALETTERE_DB: D };
  const s = sessione({ ambiente: 'production' });            // il client prova a dichiararsi produzione
  await sync(env, PREV, { sessioni: [s] });
  assert.equal(D.db.prepare('SELECT ambiente FROM sessioni WHERE id = ?').get(s.id).ambiente, 'preview');
  await sync(env, PROD, { sessioni: [{ ...s, giocatore: 'Altro', partita_id: 'x', punti_json: '{"parole":40}', secondi_ruota: 80, conclusa_at: ora() }] });
  const riga = D.db.prepare('SELECT * FROM sessioni WHERE id = ?').get(s.id);
  assert.equal(riga.ambiente, 'preview'); assert.equal(riga.giocatore, 'Ada'); assert.equal(riga.partita_id, 'demo');
  assert.equal(riga.secondi_ruota, 80); assert.ok(riga.conclusa_at);
  const s2 = sessione();
  await sync(env, PROD, { sessioni: [s2] });
  assert.equal(D.db.prepare('SELECT ambiente FROM sessioni WHERE id = ?').get(s2.id).ambiente, 'production');
  await sync({ GIRALETTERE_DB: D, GIRALETTERE_HOST_PRODUZIONE: 'gioco.example.org' }, 'https://gioco.example.org', { sessioni: [sessione({ id: '00000000-0000-4000-8000-000000000001' })] });
  assert.equal(D.db.prepare("SELECT ambiente FROM sessioni WHERE id = '00000000-0000-4000-8000-000000000001'").get().ambiente, 'production');
});

test('risposte non valide o orfane vengono scartate senza bloccare le altre', async () => {
  const D = fintoD1(); const env = { GIRALETTERE_DB: D };
  const s = sessione(); const buona = risposta(s.id);
  const orfana = risposta(randomUUID());
  const esitoStrano = risposta(s.id, { esito: 'quasi' });
  const out = await sync(env, PREV, { sessioni: [s], risposte: [buona, orfana, esitoStrano] });
  assert.deepEqual(out.accettate.risposte, [buona.id]);
  assert.deepEqual(out.scartate.risposte.sort(), [orfana.id, esitoStrano.id].sort());
  assert.equal(D.db.prepare('SELECT COUNT(*) n FROM risposte').get().n, 1);
});

test('tracciamento: filtro produzione di default e viste aggregate', async () => {
  const D = fintoD1(); const env = { GIRALETTERE_DB: D };
  const sp = sessione({ giocatore: 'Bea' }); const sv = sessione({ giocatore: 'Ada' });
  await sync(env, PROD, { sessioni: [sp], risposte: [
    risposta(sp.id, { giocatore: 'Bea', risposta_data: 'Automobile' }),
    risposta(sp.id, { giocatore: 'Bea', ordine: 2, domanda_id: 'ru-B', risposta_data: 'banana', risposta_attesa: 'banana', esito: 'corretta', tempo_ms: 800 }),
  ] });
  await sync(env, PREV, { sessioni: [sv], risposte: [risposta(sv.id, { risposta_data: 'automobile' })] });

  const partite = await leggi(env, PROD, { vista: 'partite' });
  assert.deepEqual(partite.sessioni.map((x) => x.giocatore), ['Bea'], 'di default solo produzione');
  const tutte = await leggi(env, PROD, { vista: 'partite', ambiente: 'tutti' });
  assert.equal(tutte.sessioni.length, 2);

  const dettaglio = await leggi(env, PROD, { vista: 'partita', partita: 'demo', giocatore: 'Bea' });
  assert.deepEqual(dettaglio.risposte.map((r) => r.ordine), [1, 2]);

  const gioc = await leggi(env, PROD, { vista: 'giocatori', ambiente: 'tutti', gioco: 'ruota' });
  const bea = gioc.giocatori.find((g) => g.giocatore === 'Bea');
  assert.equal(bea.totale, 2); assert.equal(bea.corrette, 1); assert.equal(bea.tempo_medio_ms, 1000);

  const dom = await leggi(env, PROD, { vista: 'domande', ambiente: 'tutti' });
  const ruA = dom.domande.find((d) => d.domanda_id === 'ru-A');
  assert.equal(ruA.sbagliate, 2);
  assert.deepEqual(dom.sbagliate.filter((x) => x.domanda_id === 'ru-A').map((x) => x.risposta_data).sort(), ['Automobile', 'automobile']);

  assert.equal((await leggi(env, PROD, { vista: 'partite', ambiente: 'staging' })).status, 400);
  assert.equal((await leggi({}, PROD, { vista: 'partite' })).status, 503);
});
