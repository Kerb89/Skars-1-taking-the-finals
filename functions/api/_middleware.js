/**
 * Middleware auth per /api/*.
 *
 * Protegge le GET agli endpoint dati (leaderboard, player, contestations, export).
 * ECCEZIONI ASSOLUTE (mai bloccati):
 *   - POST /api/results (dual-write dei quiz, fire-and-forget)
 *   - POST /api/login (il login stesso)
 *   - OPTIONS (CORS preflight)
 */

export async function onRequest(context) {
  const { request, env, next } = context;
  const method = request.method.toUpperCase();
  const url = new URL(request.url);
  const path = url.pathname;

  // Mai bloccare OPTIONS (CORS preflight)
  if (method === 'OPTIONS') {
    return next();
  }

  // Mai bloccare POST /api/results
  if (method === 'POST' && path === '/api/results') {
    return next();
  }

  // Mai bloccare POST /api/login
  if (method === 'POST' && path === '/api/login') {
    return next();
  }

  // Per tutto il resto (GET agli endpoint dati): richiedi cookie valido
  const cookie = parseCookie(request.headers.get('Cookie') || '');
  const token = cookie['qz_auth'];

  if (!token) {
    return unauthorizedResponse();
  }

  // Valida il token: deve corrispondere all'HMAC del secret
  if (!env.AUTH_PASSWORD) {
    return unauthorizedResponse();
  }

  const encoder = new TextEncoder();
  const keyData = encoder.encode(env.AUTH_PASSWORD);
  const key = await crypto.subtle.importKey(
    'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const signature = await crypto.subtle.sign(
    'HMAC', key, encoder.encode('qz_auth_token')
  );
  const expectedToken = btoa(String.fromCharCode(...new Uint8Array(signature)));

  if (token !== expectedToken) {
    return unauthorizedResponse();
  }

  // Token valido, prosegui
  return next();
}

function parseCookie(cookieHeader) {
  const cookies = {};
  cookieHeader.split(';').forEach(pair => {
    const [name, ...rest] = pair.trim().split('=');
    if (name) cookies[name.trim()] = rest.join('=').trim();
  });
  return cookies;
}

function unauthorizedResponse() {
  return new Response(JSON.stringify({ error: 'Non autenticato' }), {
    status: 401,
    headers: { 'Content-Type': 'application/json' }
  });
}
