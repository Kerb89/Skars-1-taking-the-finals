#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
confronta_dualwrite.py — Confronto grezzi GitHub vs D1 per verifica dual-write.

Decide la promozione: se tutte le partite post-dual-write sono in D1 con dati
identici, il worker vecchio può essere spento.

USO:
    python scripts/confronta_dualwrite.py --da 2026-07-17

PREREQUISITO: git pull prima di eseguire (i grezzi sono in stats/results/).

EXIT CODE: 0 = tutti MATCH (o zero grezzi nel periodo), 1 = almeno un MISSING/MISMATCH.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) confronta_dualwrite/1.0'
D1_EXPORT_URL = 'https://skars-1.pages.dev/api/export'
RESULTS_DIR = Path('stats/results')

PLAYER_MAP = {
    'mattia': 'mattia', 'matt': 'mattia',
    'jacopo': 'jacopo', 'manuel': 'manuel',
    'tato': 'tato', 'gunny': 'gunny', 'ronny': 'gunny',
}


def http_get(url):
    """GET request con User-Agent custom."""
    req = urllib.request.Request(url, method='GET', headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read()
        if raw:
            try:
                return e.code, json.loads(raw.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return e.code, {'error': f'HTTP {e.code}'}
        return e.code, {'error': f'HTTP {e.code}'}
    except Exception as e:
        return 0, {'error': str(e)}


def load_grezzi(da_data):
    """Carica i grezzi locali con timestamp >= da_data."""
    grezzi = []
    if not RESULTS_DIR.exists():
        return grezzi

    for f in sorted(RESULTS_DIR.glob('*.json')):
        if '_reprocessed' in f.name or '_test_' in f.name or f.name.startswith('test_'):
            continue
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            continue

        # Filtra per quizId valido
        qid = d.get('quizId', '')
        if not qid.startswith('quiz_puntata'):
            continue

        # Filtra per player riconosciuto
        pname = (d.get('playerName') or '').strip().lower()
        pkey = PLAYER_MAP.get(pname)
        if not pkey:
            continue

        # Filtra per timestamp >= da_data
        ts = d.get('timestamp', '')
        if not ts:
            continue
        try:
            game_date = datetime.fromisoformat(ts.replace('Z', '+00:00')).date()
        except (ValueError, TypeError):
            continue

        if game_date < da_data:
            continue

        grezzi.append({
            'file': f.name,
            'data': d,
            'playerKey': pkey,
            'playerNameRaw': pname,
            'quizId': qid,
            'score': d.get('score', 0),
            'correct': d.get('correct', 0),
            'total': d.get('total', 0),
            'num_results': len(d.get('results', [])),
            'contests': [r.get('contest') for r in d.get('results', [])
                         if r.get('contest') and str(r.get('contest')).strip()],
        })

    return grezzi


def find_match_in_d1(grezzo, d1_games, d1_answers):
    """Cerca un game D1 corrispondente al grezzo. Match per quizId + playerKey + score."""
    candidates = [
        g for g in d1_games
        if g.get('quiz_id') == grezzo['quizId']
        and g.get('player_key') == grezzo['playerKey']
        and g.get('score') == grezzo['score']
    ]

    if not candidates:
        return None, 'MISSING'

    # Prendi il primo match (dovrebbe essere unico per costruzione)
    game = candidates[0]
    game_id = game['id']

    # Conta answers
    answers = [a for a in d1_answers if a.get('game_id') == game_id]

    # Confronta campi
    mismatches = []
    if game.get('correct') != grezzo['correct']:
        mismatches.append(f"correct: D1={game.get('correct')} vs grezzo={grezzo['correct']}")
    if game.get('total') != grezzo['total']:
        mismatches.append(f"total: D1={game.get('total')} vs grezzo={grezzo['total']}")
    if len(answers) != grezzo['num_results']:
        mismatches.append(f"answers: D1={len(answers)} vs grezzo={grezzo['num_results']}")

    # Confronta contestazioni
    d1_contests = [a.get('contest') for a in answers
                   if a.get('contest') and str(a.get('contest')).strip()]
    grezzo_contests = grezzo['contests']
    if sorted(d1_contests) != sorted(grezzo_contests):
        mismatches.append(f"contests: D1={len(d1_contests)} vs grezzo={len(grezzo_contests)}")

    if mismatches:
        return game, 'MISMATCH: ' + '; '.join(mismatches)

    return game, 'MATCH'


def main():
    ap = argparse.ArgumentParser(description='Confronto dual-write: grezzi GitHub vs D1')
    ap.add_argument('--da', required=True,
                    help='Data inizio confronto (YYYY-MM-DD): solo grezzi da questa data in poi')
    args = ap.parse_args()

    try:
        da_data = datetime.strptime(args.da, '%Y-%m-%d').date()
    except ValueError:
        print(f'ERRORE: data non valida: {args.da} (atteso YYYY-MM-DD)')
        sys.exit(2)

    print('=' * 70)
    print(f'CONFRONTO DUAL-WRITE (grezzi dal {da_data})')
    print('=' * 70)
    print()

    # Ricorda di fare git pull
    print('NOTA: assicurati di aver fatto git pull prima di eseguire questo script.')
    print()

    # 1. Carica grezzi locali
    grezzi = load_grezzi(da_data)
    print(f'Grezzi locali nel periodo: {len(grezzi)}')
    if not grezzi:
        print('0 grezzi nel periodo, niente da confrontare.')
        sys.exit(0)

    for g in grezzi:
        print(f'  {g["file"]} | {g["playerKey"]} | {g["quizId"]} | score={g["score"]}')
    print()

    # 2. Scarica export D1
    print('Scaricamento export D1...')
    status, export_data = http_get(D1_EXPORT_URL)
    if status != 200:
        print(f'ERRORE: GET /api/export ha risposto {status}: {export_data}')
        sys.exit(2)

    d1_games = export_data.get('games', [])
    d1_answers = export_data.get('answers', [])
    print(f'D1: {len(d1_games)} games, {len(d1_answers)} answers')
    print()

    # 3. Confronto
    print('-' * 70)
    print(f'{"FILE":<55} {"ESITO"}')
    print('-' * 70)

    results = []
    for g in grezzi:
        _, esito = find_match_in_d1(g, d1_games, d1_answers)
        results.append((g['file'], esito))
        status_icon = 'OK' if esito == 'MATCH' else 'XX'
        print(f'  [{status_icon}] {g["file"]:<50} {esito}')

    print()
    print('=' * 70)
    print('RIEPILOGO')
    print('=' * 70)

    n_match = sum(1 for _, e in results if e == 'MATCH')
    n_missing = sum(1 for _, e in results if e == 'MISSING')
    n_mismatch = sum(1 for _, e in results if e.startswith('MISMATCH'))

    print(f'  Totale grezzi:  {len(results)}')
    print(f'  MATCH:          {n_match}')
    print(f'  MISSING (D1):   {n_missing}')
    print(f'  MISMATCH:       {n_mismatch}')
    print()

    if n_missing > 0:
        print('  NOTA: MISSING = la fetch D1 e fallita (fire-and-forget). Il grezzo')
        print('  e salvo su GitHub. Non e un errore critico ma va investigato se')
        print('  ricorre su molte partite.')
        print()

    if n_missing == 0 and n_mismatch == 0:
        print('TUTTI MATCH — dual-write verificato, pronto per la promozione.')
        sys.exit(0)
    else:
        print('ATTENZIONE: non tutti i grezzi corrispondono. Investigare prima della promozione.')
        sys.exit(1)


if __name__ == '__main__':
    main()
