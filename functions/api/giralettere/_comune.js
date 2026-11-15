// Utilità condivise dalle Functions di Giralettere.
// Non esporta handler onRequest*, quindi Pages non ne ricava alcuna route.

export const GIOCHI = ['parole', 'bocciato', 'elemento', 'titolo', 'manolesta', 'ruota'];
export const ESITI = ['corretta', 'sbagliata', 'passata', 'tempo_scaduto'];

// Host del deploy di produzione. I deploy di preview (branch) rispondono solo
// sui propri sottodomini <hash|branch>.skars-1.pages.dev: l'host che arriva
// alla Function identifica quindi il deploy che la sta eseguendo, e il
// client non può farsi classificare come produzione da un deploy di preview.
const HOST_PRODUZIONE = ['skars-1.pages.dev'];

export function ambienteDa(request, env) {
  const host = new URL(request.url).hostname.toLowerCase();
  const extra = String(env.GIRALETTERE_HOST_PRODUZIONE || '').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
  return [...HOST_PRODUZIONE, ...extra].includes(host) ? 'production' : 'preview';
}

export function json(dati, status = 200) {
  return new Response(JSON.stringify(dati), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

export function db(env) {
  if (!env.GIRALETTERE_DB) throw new Error('binding GIRALETTERE_DB non configurato');
  return env.GIRALETTERE_DB;
}
