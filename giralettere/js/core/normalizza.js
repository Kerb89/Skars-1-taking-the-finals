// Normalizzazione delle risposte a testo libero. Nessun fuzzy matching:
// due stringhe sono equivalenti solo se le loro forme normalizzate coincidono.

const ARTICOLO_SPAZIO = /^(il|lo|la|gli|le|i|uno|una|un)\s+/;
const ARTICOLO_APOSTROFO = /^(l|un)'\s*/;

export function normalizza(testo) {
  let s = String(testo ?? '').toLowerCase().trim();
  s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
  s = s.replace(/[‘’‛`´ʼ]/g, "'");
  s = s.replace(/\s+/g, ' ');
  s = s.replace(ARTICOLO_APOSTROFO, '').replace(ARTICOLO_SPAZIO, '');
  s = s.replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim();
  return s;
}

export function formeAccettate(voce) {
  return [voce.risposta, ...(voce.varianti || [])].map(normalizza).filter(Boolean);
}

export function eAccettata(input, voce) {
  const n = normalizza(input);
  return n !== '' && formeAccettate(voce).includes(n);
}
