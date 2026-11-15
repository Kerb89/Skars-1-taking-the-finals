// GET /api/giralettere/tracciamento?vista=filtri|partite|partita|giocatori|domande
// Filtri: partita, giocatore, gioco, ambiente (default "production"; "tutti" per entrambi).

import { GIOCHI, json, db } from './_comune.js';

function filtri(url) {
  const q = url.searchParams;
  const ambiente = q.get('ambiente') || 'production';
  const f = { where: [], args: [] };
  if (ambiente !== 'tutti') {
    if (!['production', 'preview'].includes(ambiente)) throw new Error('ambiente non valido');
    f.where.push('s.ambiente = ?'); f.args.push(ambiente);
  }
  const partita = q.get('partita');
  if (partita) { f.where.push('s.partita_id = ?'); f.args.push(partita); }
  const giocatore = q.get('giocatore');
  if (giocatore) { f.where.push('s.giocatore = ?'); f.args.push(giocatore); }
  const gioco = q.get('gioco');
  if (gioco) {
    if (!GIOCHI.includes(gioco)) throw new Error('gioco non valido');
    f.gioco = gioco;
  }
  return f;
}

const clausola = (w) => (w.length ? 'WHERE ' + w.join(' AND ') : '');

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const vista = url.searchParams.get('vista') || 'partite';
  let D, f;
  try { D = db(env); f = filtri(url); } catch (e) { return json({ errore: e.message }, e.message.includes('binding') ? 503 : 400); }

  const conGioco = (alias = 'r') => {
    const w = [...f.where], a = [...f.args];
    if (f.gioco) { w.push(`${alias}.gioco = ?`); a.push(f.gioco); }
    return { w, a };
  };

  try {
    if (vista === 'filtri') {
      // Le opzioni dei filtri dipendono solo dall'ambiente, non dagli altri filtri.
      const amb = f.where[0] === 's.ambiente = ?' ? { w: [f.where[0]], a: [f.args[0]] } : { w: [], a: [] };
      const giocatori = await D.prepare(`SELECT DISTINCT s.giocatore AS v FROM sessioni s ${clausola(amb.w)} ORDER BY 1 LIMIT 500`).bind(...amb.a).all();
      const partite = await D.prepare(`SELECT DISTINCT s.partita_id AS v FROM sessioni s ${clausola(amb.w)} ORDER BY 1 LIMIT 500`).bind(...amb.a).all();
      return json({ giocatori: giocatori.results.map((r) => r.v), partite: partite.results.map((r) => r.v), giochi: GIOCHI });
    }

    if (vista === 'partite') {
      const w = [...f.where], a = [...f.args];
      if (f.gioco) { w.push('EXISTS (SELECT 1 FROM risposte x WHERE x.sessione_id = s.id AND x.gioco = ?)'); a.push(f.gioco); }
      const { results } = await D.prepare(
        `SELECT s.id AS sessione_id, s.partita_id, s.giocatore, s.gioco_avviato, s.ambiente, s.punti_json,
                s.secondi_ruota, s.avviata_at, s.conclusa_at,
                (SELECT COUNT(*) FROM risposte r WHERE r.sessione_id = s.id) AS risposte,
                (SELECT COUNT(*) FROM risposte r WHERE r.sessione_id = s.id AND r.esito = 'corretta') AS corrette
         FROM sessioni s ${clausola(w)} ORDER BY s.avviata_at DESC LIMIT 500`
      ).bind(...a).all();
      return json({ sessioni: results });
    }

    if (vista === 'partita') {
      const { w, a } = conGioco();
      const { results } = await D.prepare(
        `SELECT r.id, r.sessione_id, r.partita_id, r.giocatore, r.gioco, r.domanda_id, r.ordine, r.risposta_data,
                r.risposta_attesa, r.esito, r.tempo_ms, r.client_ts, r.server_ts, s.ambiente, s.avviata_at
         FROM risposte r JOIN sessioni s ON s.id = r.sessione_id ${clausola(w)}
         ORDER BY s.avviata_at, r.sessione_id, r.ordine LIMIT 5000`
      ).bind(...a).all();
      return json({ risposte: results });
    }

    if (vista === 'giocatori') {
      const { w, a } = conGioco();
      const { results } = await D.prepare(
        `SELECT r.giocatore, r.gioco, COUNT(*) AS totale,
                SUM(r.esito = 'corretta') AS corrette, SUM(r.esito = 'sbagliata') AS sbagliate,
                SUM(r.esito = 'passata') AS passate, SUM(r.esito = 'tempo_scaduto') AS scadute,
                ROUND(AVG(r.tempo_ms)) AS tempo_medio_ms, COUNT(DISTINCT r.sessione_id) AS sessioni
         FROM risposte r JOIN sessioni s ON s.id = r.sessione_id ${clausola(w)}
         GROUP BY r.giocatore, r.gioco ORDER BY r.giocatore, r.gioco`
      ).bind(...a).all();
      return json({ giocatori: results });
    }

    if (vista === 'domande') {
      const { w, a } = conGioco();
      const domande = await D.prepare(
        `SELECT r.gioco, r.domanda_id, MAX(r.risposta_attesa) AS risposta_attesa, COUNT(*) AS totale,
                SUM(r.esito = 'corretta') AS corrette, SUM(r.esito = 'sbagliata') AS sbagliate,
                SUM(r.esito = 'passata') AS passate, SUM(r.esito = 'tempo_scaduto') AS scadute
         FROM risposte r JOIN sessioni s ON s.id = r.sessione_id ${clausola(w)}
         GROUP BY r.gioco, r.domanda_id ORDER BY sbagliate DESC, r.gioco, r.domanda_id LIMIT 2000`
      ).bind(...a).all();
      const sbagliate = await D.prepare(
        `SELECT r.gioco, r.domanda_id, r.risposta_data, COUNT(*) AS volte
         FROM risposte r JOIN sessioni s ON s.id = r.sessione_id
         ${clausola([...w, "r.esito = 'sbagliata'", 'r.risposta_data IS NOT NULL'])}
         GROUP BY r.gioco, r.domanda_id, r.risposta_data ORDER BY volte DESC LIMIT 5000`
      ).bind(...a).all();
      return json({ domande: domande.results, sbagliate: sbagliate.results });
    }
  } catch (e) {
    return json({ errore: 'lettura fallita: ' + e.message }, 500);
  }
  return json({ errore: 'vista sconosciuta' }, 400);
}
