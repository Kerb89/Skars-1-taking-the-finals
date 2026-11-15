// Coda di invio idempotente. Sessioni e risposte hanno un id generato dal
// client: il server fa INSERT OR IGNORE / upsert su quell'id, quindi un
// reinvio non duplica nulla. Un elemento esce dalla coda solo quando il
// server ne conferma l'id e solo se non è stato modificato nel frattempo.

const CHIAVE = 'giralettere.coda.v1';

function leggi() {
  try {
    const raw = localStorage.getItem(CHIAVE);
    if (raw) {
      const d = JSON.parse(raw);
      return { sessioni: d.sessioni || {}, risposte: d.risposte || {} };
    }
  } catch (_) { /* storage non disponibile o corrotto */ }
  return { sessioni: {}, risposte: {} };
}

export class CodaInvio {
  constructor({ endpoint, batchMax = 50, retryBaseMs = 1000, retryMaxMs = 30000, fetchFn } = {}) {
    this.endpoint = endpoint;
    this.batchMax = batchMax;
    this.retryBaseMs = retryBaseMs;
    this.retryMaxMs = retryMaxMs;
    this.fetchFn = fetchFn || ((...a) => fetch(...a));
    this.dati = leggi();
    this.rev = 0;
    this.tentativi = 0;
    this.timerRetry = null;
    this.inCorso = null;
    this.ascoltatori = new Set();
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.invia());
    }
  }

  _salva() {
    try { localStorage.setItem(CHIAVE, JSON.stringify(this.dati)); } catch (_) { /* resta in memoria */ }
    this._notifica();
  }

  _notifica() { const n = this.inAttesa(); this.ascoltatori.forEach((f) => f(n)); }
  onCambio(f) { this.ascoltatori.add(f); f(this.inAttesa()); }
  inAttesa() { return Object.keys(this.dati.sessioni).length + Object.keys(this.dati.risposte).length; }

  aggiungiSessione(sessione) {
    const prec = this.dati.sessioni[sessione.id]?.record || {};
    this.dati.sessioni[sessione.id] = { record: { ...prec, ...sessione }, rev: ++this.rev };
    this._salva();
    this.invia();
  }

  aggiungiRisposta(risposta) {
    this.dati.risposte[risposta.id] = { record: risposta, rev: ++this.rev };
    this._salva();
    this.invia();
  }

  invia() {
    if (this.inCorso) { this.richiestaPendente = true; return this.inCorso; }
    if (this.inAttesa() === 0) return Promise.resolve(true);
    clearTimeout(this.timerRetry);
    this.inCorso = this._inviaBatch().finally(() => {
      this.inCorso = null;
      if (this.richiestaPendente && this.inAttesa() > 0 && this.tentativi === 0) {
        this.richiestaPendente = false;
        this.invia();
      }
    });
    return this.inCorso;
  }

  async _inviaBatch() {
    const sessioni = Object.entries(this.dati.sessioni).slice(0, this.batchMax);
    const risposte = Object.entries(this.dati.risposte)
      .sort((a, b) => a[1].rev - b[1].rev)
      .slice(0, Math.max(0, this.batchMax - sessioni.length));
    const inviati = {
      sessioni: Object.fromEntries(sessioni.map(([id, v]) => [id, v.rev])),
      risposte: Object.fromEntries(risposte.map(([id, v]) => [id, v.rev])),
    };
    try {
      const res = await this.fetchFn(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessioni: sessioni.map(([, v]) => v.record),
          risposte: risposte.map(([, v]) => v.record),
        }),
        keepalive: true,
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const esito = await res.json();
      const conferma = (tipo, ids) => {
        for (const id of ids || []) {
          const corrente = this.dati[tipo][id];
          if (corrente && corrente.rev === inviati[tipo][id]) delete this.dati[tipo][id];
        }
      };
      conferma('sessioni', esito.accettate?.sessioni);
      conferma('risposte', esito.accettate?.risposte);
      // Scartate dal server per dati non validi: ritentare non servirebbe.
      conferma('sessioni', esito.scartate?.sessioni);
      conferma('risposte', esito.scartate?.risposte);
      if ((esito.scartate?.risposte || []).length || (esito.scartate?.sessioni || []).length) {
        console.warn('[giralettere] elementi scartati dal server', esito.scartate);
      }
      this.tentativi = 0;
      this._salva();
      if (this.inAttesa() > 0) setTimeout(() => this.invia(), 0);
      return true;
    } catch (err) {
      this.tentativi += 1;
      const ritardo = Math.min(this.retryMaxMs, this.retryBaseMs * 2 ** (this.tentativi - 1));
      this.timerRetry = setTimeout(() => { this.tentativi = Math.max(this.tentativi, 1); this.invia(); }, ritardo);
      this._notifica();
      return false;
    }
  }
}
