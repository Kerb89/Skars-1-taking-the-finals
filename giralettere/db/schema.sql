-- Giralettere — database D1 separato dal Quizzone (binding GIRALETTERE_DB).
-- Applicazione:
--   npx wrangler d1 execute giralettere --remote --file=giralettere/db/schema.sql
-- Idempotente: si può rieseguire.

CREATE TABLE IF NOT EXISTS sessioni (
  id            TEXT PRIMARY KEY,          -- UUID generato dal client, una riga per giocata
  partita_id    TEXT NOT NULL,             -- id del file partita (es. "demo")
  giocatore     TEXT NOT NULL,
  gioco_avviato TEXT NOT NULL,             -- 'tutti' o il nome del gioco singolo
  ambiente      TEXT NOT NULL CHECK (ambiente IN ('production', 'preview')),  -- deciso dalla Function
  punti_json    TEXT,                      -- {"parole":40,"bocciato":35,...}
  secondi_ruota INTEGER,
  avviata_at    TEXT NOT NULL,
  conclusa_at   TEXT,
  creata_server TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS risposte (
  id              TEXT PRIMARY KEY,        -- UUID client: chiave di idempotenza
  sessione_id     TEXT NOT NULL REFERENCES sessioni(id),
  partita_id      TEXT NOT NULL,
  giocatore       TEXT NOT NULL,
  gioco           TEXT NOT NULL CHECK (gioco IN ('parole','bocciato','elemento','titolo','manolesta','ruota')),
  domanda_id      TEXT NOT NULL,           -- id stabile della voce nel JSON
  ordine          INTEGER NOT NULL,        -- progressivo nella sessione
  risposta_data   TEXT,                    -- testo grezzo come scritto (NULL se tempo scaduto/passo senza testo)
  risposta_attesa TEXT NOT NULL,
  esito           TEXT NOT NULL CHECK (esito IN ('corretta','sbagliata','passata','tempo_scaduto')),
  tempo_ms        INTEGER,                 -- dalla comparsa della domanda all'invio
  client_ts       TEXT NOT NULL,
  server_ts       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sessioni_partita   ON sessioni (partita_id, ambiente);
CREATE INDEX IF NOT EXISTS idx_sessioni_giocatore ON sessioni (giocatore);
CREATE INDEX IF NOT EXISTS idx_risposte_sessione  ON risposte (sessione_id, ordine);
CREATE INDEX IF NOT EXISTS idx_risposte_partita   ON risposte (partita_id);
CREATE INDEX IF NOT EXISTS idx_risposte_giocatore ON risposte (giocatore, gioco);
CREATE INDEX IF NOT EXISTS idx_risposte_domanda   ON risposte (gioco, domanda_id, esito);
