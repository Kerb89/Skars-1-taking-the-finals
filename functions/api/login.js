/**
 * POST /api/login — Auth leggera con cookie HttpOnly.
 * Confronta la password con env.AUTH_PASSWORD.
 * Se corretta: setta cookie qz_auth con token derivato (HMAC-like).
 * Se sbagliata: 401.
 */

export async function onRequestPost(context) {
  const { env, request } = context;

  try {
    const body = await request.json();
    const password = (body.password || '').trim();

    if (!password) {
      return jsonResponse({ error: 'Password mancante' }, 400);
    }

    if (!env.AUTH_PASSWORD) {
      return jsonResponse({ error: 'Auth non configurata sul server' }, 500);
    }

    if (password !== env.AUTH_PASSWORD) {
      return jsonResponse({ error: 'Password errata' }, 401);
    }

    // Genera token derivato dal secret (non la password in chiaro)
    const encoder = new TextEncoder();
    const keyData = encoder.encode(env.AUTH_PASSWORD);
    const key = await crypto.subtle.importKey(
      'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
    );
    const signature = await crypto.subtle.sign(
      'HMAC', key, encoder.encode('qz_auth_token')
    );
    const token = btoa(String.fromCharCode(...new Uint8Array(signature)));

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Set-Cookie': `qz_auth=${token}; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=86400`,
      }
    });
  } catch (err) {
    return jsonResponse({ error: err.message }, 500);
  }
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });
}
