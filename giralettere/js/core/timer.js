// Timer a scalare con pausa/ripresa. Usa Date.now e setInterval, così nei
// test Playwright il tempo è controllabile con page.clock.

export class Timer {
  constructor(durataMs, { onTick = () => {}, onScadenza = () => {}, passoMs = 100 } = {}) {
    this.restanteMs = Math.max(0, durataMs);
    this.onTick = onTick;
    this.onScadenza = onScadenza;
    this.passoMs = passoMs;
    this.inizio = null;
    this.intervallo = null;
    this.scaduto = false;
  }

  get attivo() { return this.intervallo !== null; }

  restante() {
    if (this.inizio === null) return this.restanteMs;
    return Math.max(0, this.restanteMs - (Date.now() - this.inizio));
  }

  avvia() {
    if (this.attivo || this.scaduto) return this;
    this.inizio = Date.now();
    this.intervallo = setInterval(() => this._tick(), this.passoMs);
    this.onTick(this.restante());
    return this;
  }

  pausa() {
    if (!this.attivo) return this.restanteMs;
    this.restanteMs = this.restante();
    clearInterval(this.intervallo);
    this.intervallo = null;
    this.inizio = null;
    return this.restanteMs;
  }

  ferma() { this.pausa(); this.scaduto = true; }

  _tick() {
    const r = this.restante();
    this.onTick(r);
    if (r <= 0) {
      this.ferma();
      this.restanteMs = 0;
      this.onScadenza();
    }
  }
}

// Cronometro per il tempo di risposta: parte quando la domanda è
// rispondibile, si legge all'invio.
export function cronometro() {
  const t0 = Date.now();
  return () => Date.now() - t0;
}

export const attendi = (ms) => new Promise((r) => setTimeout(r, ms));
