/**
 * Cloudflare Worker — Proxy per salvare risultati quiz su GitHub
 * + Aggiornamento automatico stats per giocatori riconosciuti
 *
 * v2 — FIX PONTE RACE CONDITION:
 *   - updatePlayerStats / updateOverallStats: retry con re-read COMPLETO
 *     (contenuto + sha) su 409. Su conflitto si butta lo stato stantio e
 *     si ri-applica l'aggregazione sulla versione fresca. Retry SOLO su
 *     409 (mai su errori di rete: il PUT potrebbe essere passato →
 *     rischio doppio conteggio).
 *   - writeJsonToRepo resta a tentativo singolo. NON aggiungere retry qui:
 *     ri-scrivere dati stantii con sha fresco = lost update silenzioso.
 *   - statsUpdated ora dice la verità: true solo se l'aggregazione è
 *     davvero riuscita, non solo se il giocatore è riconosciuto.
 *
 * Secrets: GITHUB_TOKEN, GITHUB_REPO ("Kerb89/Skars-1-taking-the-finals")
 * Deploy: wrangler deploy
 */

const PLAYER_MAP = {
  'mattia': 'mattia', 'matt': 'mattia',
  'jacopo': 'jacopo', 'manuel': 'manuel',
  'tato': 'tato', 'gunny': 'gunny', 'ronny': 'gunny',
  '1': 'test'
};

const MAX_RETRIES = 3;

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return corsResponse(null, 204);
    if (request.method !== 'POST') return corsResponse(JSON.stringify({ error: 'Metodo non permesso' }), 405);

    try {
      const body = await request.json();
      if (!body.filePath || !body.payload) return corsResponse(JSON.stringify({ error: 'Mancano filePath o payload' }), 400);

      const safePath = body.filePath.replace(/\\/g, '/');
      if (safePath.includes('..') || safePath.startsWith('/') || !safePath.startsWith('stats/results/') || !safePath.endsWith('.json')) {
        return corsResponse(JSON.stringify({ error: 'Path non permesso' }), 403);
      }

      const content = btoa(unescape(encodeURIComponent(JSON.stringify(body.payload, null, 2))));
      // Salvataggio grezzo con retry su 409 (race sul ref del branch:
      // PUT concorrenti anche su file DIVERSI si contendono l'head di master)
      let saveResp;
      for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        saveResp = await githubPut(env, safePath, content, body.commitMessage || 'Nuovo risultato quiz');
        if (saveResp.status === 201 || saveResp.status === 200) break;
        if (saveResp.status === 409 && attempt < MAX_RETRIES) {
          console.log(`409 (branch race) su ${safePath}, retry ${attempt}/${MAX_RETRIES}`);
          await new Promise(r => setTimeout(r, attempt * 250 + Math.random() * 200));
          continue;
        }
        break;
      }
      if (saveResp.status !== 201 && saveResp.status !== 200) {
        const err = await saveResp.json();
        return corsResponse(JSON.stringify({ error: err.message || 'Errore salvataggio' }), saveResp.status);
      }

      const playerName = (body.payload.playerName || '').trim().toLowerCase();
      const playerKey = PLAYER_MAP[playerName];
      let statsOk = false;
      if (playerKey) {
        try {
          await updatePlayerStats(env, playerKey, body.payload);
          await updateOverallStats(env, playerKey, body.payload);
          statsOk = true;
        } catch (e) { console.error('Stats error:', e.message); }
      }

      // Il grezzo è comunque salvo; se statsOk è false si recupera
      // con replay_stats.py.
      return corsResponse(JSON.stringify({ success: true, statsUpdated: statsOk }), 200);
    } catch (err) {
      return corsResponse(JSON.stringify({ error: err.message }), 500);
    }
  }
};

function corsResponse(body, status = 200) {
  return new Response(body, { status, headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  }});
}

async function githubGet(env, path) {
  return await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`, {
    headers: { 'Accept': 'application/vnd.github.v3+json', 'Authorization': `token ${env.GITHUB_TOKEN}`, 'User-Agent': 'Quiz-Results-Worker' }
  });
}

async function githubPut(env, path, contentBase64, message, sha = null) {
  const body = { message, content: contentBase64 };
  if (sha) body.sha = sha;
  return await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`, {
    method: 'PUT', headers: { 'Accept': 'application/vnd.github.v3+json', 'Authorization': `token ${env.GITHUB_TOKEN}`, 'Content-Type': 'application/json', 'User-Agent': 'Quiz-Results-Worker' },
    body: JSON.stringify(body)
  });
}

async function readJsonFromRepo(env, path) {
  const resp = await githubGet(env, path);
  if (resp.status === 404) return { data: null, sha: null };
  if (!resp.ok) throw new Error(`GitHub GET ${path}: ${resp.status}`);
  const file = await resp.json();
  const decoded = decodeURIComponent(escape(atob(file.content.replace(/\n/g, ''))));
  return { data: JSON.parse(decoded), sha: file.sha };
}

// Tentativo SINGOLO, volutamente. Il retry vive nel chiamante.
async function writeJsonToRepo(env, path, data, message, sha) {
  const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(data, null, 2))));
  return await githubPut(env, path, encoded, message, sha);
}

// Aggregazione giocatore. PURA (nessuna I/O): il retry la ri-applica
// su stato fresco. Logica identica all'originale.
function applyPlayerAggregation(s, result) {
  s.totalGames += 1;
  s.totalScore += result.score || 0;
  s.totalCorrect += result.correct || 0;
  s.totalQuestions += result.total || 0;
  s.avgPercentage = Math.round(s.totalCorrect / s.totalQuestions * 100);
  s.avgTime = parseFloat(((s.avgTime * (s.totalGames - 1) + (result.avgTime || 0)) / s.totalGames).toFixed(1));

  s.games.push({
    quizId: result.quizId, quizTitle: result.quizTitle || result.quizId,
    date: (result.timestamp || new Date().toISOString()).split('T')[0],
    score: result.score || 0, correct: result.correct || 0, total: result.total || 0,
    percentage: result.percentage || 0, maxStreak: result.maxStreak || 0, avgTime: result.avgTime || 0
  });

  if (result.results && Array.isArray(result.results)) {
    const catStats = {};
    for (const r of result.results) {
      const cat = r.category || 'altro';
      if (!catStats[cat]) catStats[cat] = { wrong: 0, total: 0 };
      catStats[cat].total += 1;
      if (!r.correct) {
        catStats[cat].wrong += 1;
        const ew = s.wrongQuestions.find(w => w.question === r.question && w.correctAnswer === r.correctOption);
        if (ew) { ew.timesWrong += 1; if (!ew.quizIds.includes(result.quizId)) ew.quizIds.push(result.quizId); }
        else { s.wrongQuestions.push({ question: r.question, category: cat, correctAnswer: r.correctOption || null, givenAnswer: r.chosenOption || '(timeout)', quizIds: [result.quizId], timesWrong: 1 }); }
      }
    }
    for (const [cat, st] of Object.entries(catStats)) {
      if (!s.weakCategories[cat]) s.weakCategories[cat] = { wrong: 0, total: 0, percentage: 0 };
      s.weakCategories[cat].wrong += st.wrong;
      s.weakCategories[cat].total += st.total;
      s.weakCategories[cat].percentage = Math.round((1 - s.weakCategories[cat].wrong / s.weakCategories[cat].total) * 100);
    }
  }

  s.wrongQuestions.sort((a, b) => b.timesWrong - a.timesWrong);

  // Contestazioni
  if (result.results && Array.isArray(result.results)) {
    if (!s.contestations) s.contestations = [];
    for (let i = 0; i < result.results.length; i++) {
      const r = result.results[i];
      if (r.contest && r.contest.trim()) {
        s.contestations.push({
          quizId: result.quizId,
          date: (result.timestamp || new Date().toISOString()).split('T')[0],
          questionNum: i + 1,
          question: r.question || '',
          correctAnswer: r.correctOption || null,
          givenAnswer: r.chosenOption || '(timeout)',
          contestText: r.contest.trim()
        });
      }
    }
  }

  return s;
}

// Aggregazione overall. PURA. Logica identica all'originale.
function applyOverallAggregation(o, playerKey, result) {
  o.lastUpdated = new Date().toISOString();
  o.totalGamesPlayed += 1;

  if (!o.leaderboard[playerKey]) o.leaderboard[playerKey] = { games: 0, totalScore: 0, totalCorrect: 0, totalQuestions: 0, avgPercentage: 0, avgTime: 0 };
  const lb = o.leaderboard[playerKey];
  lb.games += 1;
  lb.totalScore += result.score || 0;
  lb.totalCorrect += result.correct || 0;
  lb.totalQuestions += result.total || 0;
  lb.avgPercentage = Math.round(lb.totalCorrect / lb.totalQuestions * 100);
  lb.avgTime = parseFloat(((lb.avgTime * (lb.games - 1) + (result.avgTime || 0)) / lb.games).toFixed(1));

  o.history.push({
    date: (result.timestamp || new Date().toISOString()).split('T')[0],
    quizId: result.quizId, quizTitle: result.quizTitle || result.quizId,
    player: playerKey, score: result.score || 0, correct: result.correct || 0,
    total: result.total || 0, percentage: result.percentage || 0
  });

  if (result.results && Array.isArray(result.results)) {
    for (const r of result.results) {
      if (!r.correct) {
        const ew = o.mostWrongQuestions.find(w => w.question === r.question && w.correctAnswer === r.correctOption);
        if (ew) { ew.timesWrong += 1; if (!ew.wrongBy.includes(playerKey)) ew.wrongBy.push(playerKey); }
        else { o.mostWrongQuestions.push({ question: r.question, category: r.category || 'altro', correctAnswer: r.correctOption || null, wrongBy: [playerKey], timesWrong: 1 }); }
      }
    }
    o.mostWrongQuestions.sort((a, b) => b.timesWrong - a.timesWrong);
  }

  // Contestazioni
  if (result.results && Array.isArray(result.results)) {
    if (!o.contestations) o.contestations = [];
    for (let i = 0; i < result.results.length; i++) {
      const r = result.results[i];
      if (r.contest && r.contest.trim()) {
        o.contestations.push({
          player: playerKey,
          quizId: result.quizId,
          date: (result.timestamp || new Date().toISOString()).split('T')[0],
          questionNum: i + 1,
          question: r.question || '',
          contestText: r.contest.trim()
        });
      }
    }
  }

  return o;
}

async function updatePlayerStats(env, playerKey, result) {
  const path = `stats/players/${playerKey}.json`;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    // Re-read COMPLETO a ogni giro: contenuto + sha freschi.
    const { data: existing, sha } = await readJsonFromRepo(env, path);
    const base = existing || {
      player: playerKey, totalGames: 0, totalScore: 0, totalCorrect: 0,
      totalQuestions: 0, avgPercentage: 0, avgTime: 0,
      games: [], weakCategories: {}, wrongQuestions: [], contestations: []
    };

    const s = applyPlayerAggregation(base, result);
    const resp = await writeJsonToRepo(env, path, s, `Stats ${playerKey} aggiornate`, sha);

    if (resp.status === 200 || resp.status === 201) return;
    if (resp.status === 409 && attempt < MAX_RETRIES) {
      // Il 409 garantisce che il PUT NON è passato: ri-applicare è sicuro.
      console.log(`409 su ${path}, retry ${attempt}/${MAX_RETRIES}`);
      await new Promise(r => setTimeout(r, attempt * 250 + Math.random() * 200));
      continue;
    }
    throw new Error(`GitHub PUT ${path}: ${resp.status} dopo ${attempt} tentativi`);
  }
  throw new Error(`GitHub PUT stats/players/${playerKey}.json: 409 persistente dopo ${MAX_RETRIES} tentativi`);
}

async function updateOverallStats(env, playerKey, result) {
  const path = 'stats/players/overall.json';

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    const { data: existing, sha } = await readJsonFromRepo(env, path);
    const base = existing || {
      lastUpdated: null, totalGamesPlayed: 0, leaderboard: {},
      history: [], mostWrongQuestions: [], contestations: []
    };

    const o = applyOverallAggregation(base, playerKey, result);
    const resp = await writeJsonToRepo(env, path, o, `Overall stats aggiornate`, sha);

    if (resp.status === 200 || resp.status === 201) return;
    if (resp.status === 409 && attempt < MAX_RETRIES) {
      console.log(`409 su ${path}, retry ${attempt}/${MAX_RETRIES}`);
      await new Promise(r => setTimeout(r, attempt * 250 + Math.random() * 200));
      continue;
    }
    throw new Error(`GitHub PUT ${path}: ${resp.status} dopo ${attempt} tentativi`);
  }
  throw new Error(`GitHub PUT stats/players/overall.json: 409 persistente dopo ${MAX_RETRIES} tentativi`);
}
