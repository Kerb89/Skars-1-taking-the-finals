// Sessione di gioco: una per ogni giocata (chi rigioca crea una sessione
// nuova). Ogni risposta è registrata e messa nella coda di invio.

export function uuid() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40; b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map((x) => x.toString(16).padStart(2, '0')).join('');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

export const ESITI = ['corretta', 'sbagliata', 'passata', 'tempo_scaduto'];

export class Sessione {
  constructor({ coda, partitaId, giocatore, giocoAvviato }) {
    this.coda = coda;
    this.id = uuid();
    this.partitaId = partitaId;
    this.giocatore = giocatore;
    this.ordine = 0;
    this.punti = {};
    this.log = [];
    this.coda.aggiungiSessione({
      id: this.id, partita_id: partitaId, giocatore, gioco_avviato: giocoAvviato,
      avviata_at: new Date().toISOString(),
    });
  }

  registra({ gioco, domanda_id, risposta_data, risposta_attesa, esito, tempo_ms }) {
    if (!ESITI.includes(esito)) throw new Error('esito non valido: ' + esito);
    const r = {
      id: uuid(),
      sessione_id: this.id,
      partita_id: this.partitaId,
      giocatore: this.giocatore,
      gioco,
      domanda_id,
      ordine: ++this.ordine,
      risposta_data: risposta_data ?? null,
      risposta_attesa,
      esito,
      tempo_ms: tempo_ms == null ? null : Math.round(tempo_ms),
      client_ts: new Date().toISOString(),
    };
    this.log.push(r);
    this.coda.aggiungiRisposta(r);
    return r;
  }

  impostaPunti(gioco, punti) {
    this.punti[gioco] = punti;
    this.coda.aggiungiSessione({ id: this.id, punti_json: JSON.stringify(this.punti) });
  }

  concludi({ secondiRuota } = {}) {
    this.coda.aggiungiSessione({
      id: this.id, punti_json: JSON.stringify(this.punti),
      secondi_ruota: secondiRuota ?? null, conclusa_at: new Date().toISOString(),
    });
  }
}
