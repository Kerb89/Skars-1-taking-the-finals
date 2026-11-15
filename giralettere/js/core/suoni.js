// Suoni originali sintetizzati con Web Audio API: nessun file audio nel repo.

let ctx = null;
function audio() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
  }
  if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  return ctx;
}

function nota(freq, durata, { tipo = 'sine', ritardo = 0, volume = 0.15 } = {}) {
  const a = audio();
  if (!a) return;
  const t = a.currentTime + ritardo;
  const o = a.createOscillator();
  const g = a.createGain();
  o.type = tipo;
  o.frequency.setValueAtTime(freq, t);
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(volume, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + durata);
  o.connect(g).connect(a.destination);
  o.start(t);
  o.stop(t + durata + 0.02);
}

export const suoni = {
  giusta() { nota(660, 0.12, { tipo: 'triangle' }); nota(990, 0.18, { tipo: 'triangle', ritardo: 0.1 }); },
  sbagliata() { nota(220, 0.25, { tipo: 'sawtooth', volume: 0.08 }); },
  passo() { nota(440, 0.1, { tipo: 'square', volume: 0.06 }); },
  tick() { nota(1200, 0.04, { tipo: 'square', volume: 0.04 }); },
  fine() { [523, 659, 784, 1047].forEach((f, i) => nota(f, 0.2, { tipo: 'triangle', ritardo: i * 0.12 })); },
  sblocca() { audio(); },
};
