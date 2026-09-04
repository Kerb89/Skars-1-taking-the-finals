# CLAUDE.md — Quizzone (SKARS)

Contratti e regole di generazione dettagliate vivono in `.kiro/steering/*.md`
(11 file, `quizzone-00` core → `quizzone-11` schema D1). Questo file è
l'orientamento operativo rapido, non li sostituisce. In caso di conflitto
vince la steering più specifica sul tema.

## Gate obbligatori — non bypassabili, non modificabili per farli passare

Pipeline di validazione di una puntata, ordine fisso:

1. `python valida_quiz.py <file.md>` + `python quiz_dedup.py check <file.md>`
   — invocati dall'hook `quiz-valida-post-creazione` su ogni nuovo
   `puntate/quiz_puntata*.md`. **`valida_quiz.py` è referenziato dall'hook ma
   non esiste nel repo né nella history git** (`git log --all -- valida_quiz.py`
   vuoto): gate rotto, va ricreato o l'hook va corretto — non ignorare in
   silenzio l'assenza.
2. `python scripts/validate_quiz_html.py <file.html>` — statico, sul JSON
   `const questions` inline. FAIL bloccante include: conteggio ≠45, `ans`
   array (risposte multiple, vedi bug noto sotto), distribuzione lettere
   <8, >2 consecutive uguali, anagrammi con distrattore-anagramma valido,
   media >60KB singola / >1.5MB totale, fetch D1 mancante (`API_D1_URL`).
3. `python scripts/smoke_test_quiz.py <file.html>` — runtime, Playwright
   headless. **Gate finale**: exit 0 obbligatorio prima che una puntata sia
   "pronta". Intercetta entrambe le fetch (worker + D1), verifica payload.

Selettori e contratti condivisi tra i due validatori: `scripts/quizzone_validator_config.json`.

**Regola assoluta**: se un check sembra sbagliato, si segnala e ci si ferma
per approvazione umana. Non si disattiva, commenta o aggira un check per
far passare una validazione.

## File autogenerati o canonici — non toccare a mano

- `index.html` — generato da `scripts/genera_indice.py` (hook
  `rigenera-indice-home`, scatta alla creazione di un HTML puntata).
  Modificare l'aspetto della home nel template dentro `genera_indice.py`,
  mai nel file generato.
- `puntate/answers_index.txt` — generato da `python quiz_dedup.py index`.
  Non editare a mano.
- `worker/quiz-results.js` — **sorgente in uso** del Worker Cloudflare fase 1
  (deploy: `wrangler deploy` da `worker/`, `main` in `worker/wrangler.toml`).
  Si modifica solo lì, poi si deploya.
- **`worker.js` in root è una copia morta/divergente**, più vecchia (ultimo
  tocco 2026-07-11) e priva del retry-on-409 sul salvataggio del grezzo che
  `worker/quiz-results.js` ha. È anche listata in `.gitignore` (riga
  `worker.js`) insieme ad altri file root (`quiz_dedup.py`, `build_p*.py`,
  `anagramma*.py`, `rileva_regalo.py`, `show_stats.py`,
  `generate_chart.py`, `link_utili.md`) che restano tracciati solo perché
  committati prima della regola — il gitignore lì è aspirazionale, non lo
  stato reale. Non editare/deployare mai `worker.js` di root: è quello
  sbagliato.
- Storico domande (`puntate/quiz_history_pXX_pYY.md`) — si aggiorna solo
  tramite l'hook `quiz-aggiorna-history` (agentStop) o manualmente seguendo
  lo stesso formato; mai a mano in modo estemporaneo.

## Stato reale — fase 2 (D1)

Contratto vigente: `quizzone-10-api-worker.md` (worker fase 1, GitHub
Contents API). `quizzone-11-d1-schema.md` è approvato ma non in vigore.

Rollout a 6 passi, **fermo al passo 3**:
1. ✅ Infrastruttura D1 (`db/schema.sql`, binding in `wrangler.toml`)
2. ✅ Pages Functions (`functions/api/*`)
3. 🔶 Dual-write nel template — **implementato e live** (ogni puntata da
   P34 in poi manda sia a `WORKER_URL` sia a `D1_URL`), ma **non chiuso**:
   il gate di promozione al passo 4 è una serata reale giocata col
   template dual-write, seguita dal confronto grezzi GitHub vs
   `/api/export` via `scripts/confronta_dualwrite.py`. Si è in attesa di
   quella serata — nessuna evidenza che sia già avvenuta.
4. ⬜ Migrazione storico (`scripts/migrate_to_d1.py` esiste, non risulta
   eseguito contro i 44 grezzi + 21 orfane)
5. ⬜ Verifica criteri di accettazione
6. ⬜ Switch (spegnimento worker vecchio)

Non anticipare il passo 4 finché il passo 3 non è chiuso con la prova
sopra descritta.

## Stato reale — fase 3 (dashboard giocatori)

In corso, non contrattualizzata in steering dedicata:
- `classifica.html`, `giocatore.html` in root — navbar condivisa
  (Puntate/Classifica/Giocatori), CSS condiviso `assets/style.css`.
  `classifica.html` legge `GET /api/leaderboard`.
- `functions/api/login.js` — auth con password condivisa via
  `env.AUTH_PASSWORD`, cookie HttpOnly HMAC-derivato.
- **`functions/api/_middleware.js` non applica questa auth**: gli endpoint
  di lettura sono attualmente aperti senza protezione ("verrà riabilitata
  in futuro se necessario"). La dashboard è di fatto pubblica adesso —
  tenerlo presente prima di esporre dati sensibili nuovi.

## Bug noti da non regredire

- **Risposte multiple disabilitate** — `processAnswer` nel template quiz
  confronta `chosen === correct`: con `correct` array (domanda a doppia
  risposta) il confronto è sempre `false` e `q.opts[correct]` è
  `undefined`. `validate_quiz_html.py` → check `RISPOSTA_JSON` fa FAIL
  bloccante su qualunque `ans` array, quindi il divieto è enforced, non
  solo convenzionale.
  **Il fix è accoppiato**: sbloccare le risposte multiple richiede di
  modificare **nello stesso intervento** sia `processAnswer` (gestire
  `Array.isArray(correct)`, match con `.includes`, display multi-opzione)
  sia rimuovere il FAIL da `RISPOSTA_JSON` in `validate_quiz_html.py`.
  Un fix parziale (solo template o solo validatore) lascia il sistema
  inconsistente — o il bug resta live, o il gate blocca quiz già corretti.
- **Campo `contest` mai testato end-to-end** (fase 1) — il flusso
  `contestBtn → saveContestBtn → r.contest` potrebbe arrivare sempre
  `null` al worker anche quando il giocatore contesta davvero. Da
  verificare prima della progettazione fase 2 definitiva.

## Regole operative

- Puntate vecchie (pre-dual-write, 1-30): falliscono `API_D1_URL` per
  costruzione — è intenzionale, non un errore da correggere in massa. Se
  una puntata vecchia viene toccata per qualsiasi altro motivo, la sua
  sezione upload va portata al dual-write nello stesso intervento.
- File di prova per i gate → sempre in `_test/` (gitignored), mai
  `puntate/quiz_puntata*.html`: quel pattern è agganciato agli hook e a
  `genera_indice.py`.
- `scripts/replay_stats.py` è strumento **permanente** di riconciliazione
  (non un fix una tantum): recupera stats perse per race persistente sul
  worker fase 1 (dry-run di default, `--apply` per scrivere). Usarlo ogni
  volta che si sospetta un `statsUpdated: false`.
- Chiamate programmatiche alle API Cloudflare/GitHub da script (Python,
  cron) devono dichiarare uno User-Agent non-default: Bot Fight Mode
  blocca le firme nude `Python-urllib`/`python-requests` con errore 1010.
  Usare UA browser-like, es. `Mozilla/5.0 (QuizzoneScript/1.0)`.
- Push con pack grandi (immagini/audio base64 in history) possono fallire
  su HTTP/2: `git config http.version HTTP/1.1` prima del push se capita.
