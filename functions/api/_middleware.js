/**
 * Middleware per /api/*.
 * Per ora: nessuna protezione sugli endpoint di lettura.
 * POST /api/results resta sempre aperto (dual-write).
 * L'auth verrà riabilitata in futuro se necessario.
 */

export async function onRequest(context) {
  return context.next();
}
