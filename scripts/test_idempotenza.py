#!/usr/bin/env python3
"""
Test idempotenza endpoint POST /api/results (D1).

Uso:
    python scripts/test_idempotenza.py https://d1-setup.skars-1.pages.dev

Genera un uploadId NUOVO a ogni run (suffisso timestamp corrente).
Esegue in sequenza:
  1. GET conteggio iniziale (via /api/leaderboard)
  2. POST 1 → attende inserted:true
  3. POST 2 identico → attende inserted:false
  4. GET /api/contestations → verifica che la contestazione di prova sia presente

Esce con exit code 0 solo se tutti i criteri passano.
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


# === Configurazione payload di test ===

def make_test_payload():
    """Genera un payload di test con uploadId univoco."""
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    upload_id = f'quiz_puntata99_idemp_test_{ts}'
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')

    return {
        'uploadId': upload_id,
        'quizId': 'quiz_puntata99_test',
        'quizTitle': 'Test Idempotenza',
        'playerName': '1',  # maps to 'test' in PLAYER_MAP → escluso da classifiche
        'timestamp': timestamp,
        'score': 500,
        'correct': 2,
        'total': 3,
        'percentage': 67,
        'maxStreak': 2,
        'avgTime': 7.5,
        'multiplierStats': {'used': 0, 'remaining': 4},
        'results': [
            {
                'question': 'Domanda test 1 - idempotenza',
                'category': 'tecnologia',
                'correct': True,
                'timeout': False,
                'points': 200,
                'streakBonus': 0,
                'multiplierUsed': False,
                'timeUsed': 5.0,
                'chosenOption': 'Python',
                'correctOption': 'Python',
                'contest': None
            },
            {
                'question': 'Domanda test 2 - contestazione prova',
                'category': 'scienze',
                'correct': False,
                'timeout': False,
                'points': -75,
                'streakBonus': 0,
                'multiplierUsed': False,
                'timeUsed': 12.3,
                'chosenOption': 'Marte',
                'correctOption': 'Giove',
                'contest': 'Contestazione di prova per test idempotenza'
            },
            {
                'question': 'Domanda test 3 - idempotenza',
                'category': 'storia',
                'correct': True,
                'timeout': False,
                'points': 250,
                'streakBonus': 50,
                'multiplierUsed': False,
                'timeUsed': 8.1,
                'chosenOption': '1492',
                'correctOption': '1492',
                'contest': None
            }
        ]
    }


# === Utility HTTP ===

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) test_idempotenza/1.0'


def http_get(url):
    """GET request, ritorna (status, body_dict)."""
    req = urllib.request.Request(url, method='GET', headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        raw = e.read()
        if raw:
            try:
                body = json.loads(raw.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = {'error': f'HTTP {e.code}: {raw[:200]}'}
        else:
            body = {'error': f'HTTP {e.code}'}
        return e.code, body
    except Exception as e:
        return 0, {'error': str(e)}


def http_post(url, data):
    """POST request JSON, ritorna (status, body_dict)."""
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        method='POST',
        headers={'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        raw = e.read()
        if raw:
            try:
                body = json.loads(raw.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = {'error': f'HTTP {e.code}: {raw[:200]}'}
        else:
            body = {'error': f'HTTP {e.code}'}
        return e.code, body
    except Exception as e:
        return 0, {'error': str(e)}


# === Test runner ===

def main():
    if len(sys.argv) < 2:
        print('Uso: python scripts/test_idempotenza.py <base_url>')
        print('  Es: python scripts/test_idempotenza.py https://d1-setup.skars-1.pages.dev')
        sys.exit(1)

    base_url = sys.argv[1].rstrip('/')
    payload = make_test_payload()
    upload_id = payload['uploadId']
    results = []

    print(f'=== Test Idempotenza D1 ===')
    print(f'Base URL: {base_url}')
    print(f'Upload ID: {upload_id}')
    print()

    # --- Step 1: GET conteggio iniziale ---
    print('--- Step 1: GET /api/leaderboard (conteggio iniziale) ---')
    status, body = http_get(f'{base_url}/api/leaderboard')
    print(f'  Status: {status}')
    print(f'  Response: {json.dumps(body, indent=2, ensure_ascii=False)[:500]}')
    step1_ok = status == 200
    results.append(('GET leaderboard raggiungibile', step1_ok))
    print(f'  -> {"PASS" if step1_ok else "FAIL"}: endpoint raggiungibile')
    print()

    # --- Step 2: POST 1 (primo invio) ---
    print('--- Step 2: POST /api/results (primo invio) ---')
    status, body = http_post(f'{base_url}/api/results', payload)
    print(f'  Status: {status}')
    print(f'  Response: {json.dumps(body, ensure_ascii=False)}')
    step2_ok = status == 200 and body.get('success') is True and body.get('inserted') is True
    results.append(('POST 1 -> inserted:true', step2_ok))
    print(f'  -> {"PASS" if step2_ok else "FAIL"}: success=true, inserted=true')
    print()

    # --- Step 2b: GET /api/export (conteggio dopo POST 1) ---
    print('--- Step 2b: GET /api/export (conteggio dopo POST 1) ---')
    status, export1 = http_get(f'{base_url}/api/export')
    games_after_post1 = export1.get('games_count', -1)
    answers_after_post1 = export1.get('answers_count', -1)
    print(f'  Status: {status}')
    print(f'  games_count={games_after_post1}, answers_count={answers_after_post1}')

    # Verifica: esattamente 1 game col nostro uploadId, con 3 answers
    our_games = [g for g in export1.get('games', []) if g.get('upload_id') == upload_id]
    our_game_ids = [g['id'] for g in our_games]
    our_answers = [a for a in export1.get('answers', []) if a.get('game_id') in our_game_ids]
    print(f'  Game con nostro uploadId: {len(our_games)}, answers agganciate: {len(our_answers)}')
    step2b_game_ok = len(our_games) == 1
    step2b_answers_ok = len(our_answers) == 3
    results.append(('Export post-POST1: 1 game col nostro uploadId', step2b_game_ok))
    results.append(('Export post-POST1: 3 answers agganciate', step2b_answers_ok))
    print(f'  -> {"PASS" if step2b_game_ok else "FAIL"}: 1 game trovato')
    print(f'  -> {"PASS" if step2b_answers_ok else "FAIL"}: 3 answers trovate')
    print()

    # --- Step 3: POST 2 (retry identico) ---
    print('--- Step 3: POST /api/results (retry identico) ---')
    status, body = http_post(f'{base_url}/api/results', payload)
    print(f'  Status: {status}')
    print(f'  Response: {json.dumps(body, ensure_ascii=False)}')
    step3_ok = status == 200 and body.get('success') is True and body.get('inserted') is False
    results.append(('POST 2 -> inserted:false (dedup)', step3_ok))
    print(f'  -> {"PASS" if step3_ok else "FAIL"}: success=true, inserted=false')
    print()

    # --- Step 3b: GET /api/export (conteggio dopo POST 2 — deve essere IDENTICO) ---
    print('--- Step 3b: GET /api/export (conteggio dopo POST 2) ---')
    status, export2 = http_get(f'{base_url}/api/export')
    games_after_post2 = export2.get('games_count', -1)
    answers_after_post2 = export2.get('answers_count', -1)
    print(f'  Status: {status}')
    print(f'  games_count={games_after_post2}, answers_count={answers_after_post2}')
    print(f'  Attesi: games={games_after_post1}, answers={answers_after_post1}')
    count_games_ok = games_after_post2 == games_after_post1
    count_answers_ok = answers_after_post2 == answers_after_post1
    results.append(('COUNT games invariato dopo POST 2', count_games_ok))
    results.append(('COUNT answers invariato dopo POST 2', count_answers_ok))
    print(f'  -> {"PASS" if count_games_ok else "FAIL"}: games_count invariato')
    print(f'  -> {"PASS" if count_answers_ok else "FAIL"}: answers_count invariato')
    print()

    # --- Step 4: GET /api/contestations ---
    print('--- Step 4: GET /api/contestations (verifica contestazione) ---')
    status, body = http_get(f'{base_url}/api/contestations')
    print(f'  Status: {status}')
    contestations = body.get('contestations', [])
    print(f'  Contestazioni totali: {len(contestations)}')

    # Cerca la contestazione del nostro test
    found_contest = False
    for c in contestations:
        if c.get('contest') == 'Contestazione di prova per test idempotenza':
            found_contest = True
            print(f'  Trovata: player={c.get("player_key")}, quiz={c.get("quiz_id")}, '
                  f'q_num={c.get("question_num")}')
            break

    if not found_contest:
        # Mostra le ultime 3 per debug
        print(f'  Ultime 3 contestazioni:')
        for c in contestations[:3]:
            print(f'    - {c.get("contest", "")[:60]}... (quiz={c.get("quiz_id")})')

    results.append(('Contestazione presente in /api/contestations', found_contest))
    print(f'  -> {"PASS" if found_contest else "FAIL"}: contestazione di prova trovata')
    print()

    # === Riepilogo ===
    print('=' * 50)
    print('RIEPILOGO')
    print('=' * 50)
    all_pass = True
    for label, ok in results:
        status_str = 'PASS' if ok else 'FAIL'
        print(f'  [{status_str}] {label}')
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print('TUTTI I TEST PASSATI - idempotenza verificata.')
        sys.exit(0)
    else:
        print('ALCUNI TEST FALLITI.')
        sys.exit(1)


if __name__ == '__main__':
    main()
