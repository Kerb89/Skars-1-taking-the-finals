# Giralettere

Gioco a manche, automatico e senza conduttore: ogni giocatore gioca dal
proprio dispositivo, sceglie un nickname e risponde. Sezione autonoma del
sito, servita su `/giralettere/`, indipendente dal Quizzone (niente template
puntate, validatori, `genera_indice.py`, API o database del Quizzone).

## Struttura

| Percorso | Cosa |
|---|---|
| `index.html`, `js/home.js` | home: nickname, scelta partita e gioco |
| `gioca/index.html`, `js/app.js` | motore: `?partita=<id>&gioco=tutti\|parole\|bocciato\|elemento\|titolo\|manolesta\|ruota&nick=<nome>` |
| `js/core/` | normalizzazione, timer, coda di invio, sessione, contenuti, suoni, UI |
| `js/giochi/` | un modulo per gioco (`regole(ctx)`, `gioca(ctx)` → `{punti, riepilogo}`) |
| `tracciamento/` | elenco partite, dettaglio, vista per giocatore e per domanda |
| `config.json` | timer, soglie, punteggi, conversione punti → secondi |
| `partite/` | contenuti: `index.json`, un JSON per partita, schema in `SCHEMA.md` |
| `db/schema.sql` | database D1 `giralettere` (binding `GIRALETTERE_DB`) |
| `tests/` | test Playwright (`python giralettere/tests/run_tests.py`) |
| `../functions/api/giralettere/` | `sync` (POST idempotente) e `tracciamento` (GET) |

## Database

```
npx wrangler d1 create giralettere --location weur      # una volta
npx wrangler d1 execute giralettere --remote --file=giralettere/db/schema.sql
```

La colonna `ambiente` (`production` / `preview`) la decide la Function
dall'host del deploy che la esegue, mai il client: solo il deploy di
produzione risponde su `skars-1.pages.dev`. Host di produzione aggiuntivi
(es. un dominio custom) vanno nella variabile `GIRALETTERE_HOST_PRODUZIONE`
del progetto Pages, separati da virgola.

## Test

```
python giralettere/tests/run_tests.py            # tutti i test locali (API simulate, tempo controllato)
python giralettere/tests/run_tests.py ruota      # un solo file
python giralettere/tests/test_preview.py <url>   # e2e sulla preview reale: DEMO → tracciamento
```
