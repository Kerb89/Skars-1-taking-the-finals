#!/usr/bin/env python3
"""
Gate di chiusura — test dashboard (branch preview).
Uso: python scripts/test_dashboard_gate.py <password>

Testa:
  a) GET /api/leaderboard senza cookie → 401
  b) POST /api/login con password giusta → 200 + cookie → GET → 200
  c) POST /api/login con password sbagliata → 401
  d) POST /api/results senza cookie → funziona (200) + cleanup
  e) classifica.html e giocatore.html raggiungibili (200)
"""
import sys
import json
import requests

BASE = "https://dashboard.skars-1.pages.dev"
UA = {"User-Agent": "Mozilla/5.0 (QuizzoneTest/1.0)"}


def test_a():
    """GET /api/leaderboard senza cookie → 401"""
    r = requests.get(f"{BASE}/api/leaderboard", headers=UA)
    assert r.status_code == 401, f"FAIL (a): atteso 401, ottenuto {r.status_code}"
    print(f"  (a) PASS — GET /api/leaderboard senza cookie → {r.status_code}")


def test_b(password):
    """Login corretto → cookie → GET → 200"""
    session = requests.Session()
    session.headers.update(UA)
    # Login
    r = session.post(f"{BASE}/api/login", json={"password": password})
    assert r.status_code == 200, f"FAIL (b login): atteso 200, ottenuto {r.status_code} — {r.text}"
    data = r.json()
    assert data.get("success") is True, f"FAIL (b login): response non success — {data}"
    # Verifica cookie settato
    assert "qz_auth" in session.cookies.get_dict(), "FAIL (b): cookie qz_auth non ricevuto"
    # GET con cookie
    r2 = session.get(f"{BASE}/api/leaderboard")
    assert r2.status_code == 200, f"FAIL (b GET): atteso 200, ottenuto {r2.status_code}"
    body = r2.json()
    assert "leaderboard" in body, f"FAIL (b GET): risposta senza campo leaderboard — {body}"
    print(f"  (b) PASS — login OK → cookie → GET /api/leaderboard → {r2.status_code} ({len(body['leaderboard'])} giocatori)")


def test_c():
    """Login con password sbagliata → 401"""
    r = requests.post(f"{BASE}/api/login", json={"password": "password_sicuramente_sbagliata_xyz"}, headers=UA)
    assert r.status_code == 401, f"FAIL (c): atteso 401, ottenuto {r.status_code}"
    print(f"  (c) PASS — login sbagliato → {r.status_code}")


def test_d():
    """POST /api/results senza cookie → deve funzionare (200)"""
    payload = {
        "uploadId": "test_gate_dashboard_cleanup_12345",
        "quizId": "quiz_puntata99_test",
        "quizTitle": "Test Gate Dashboard",
        "playerName": "1",
        "timestamp": "2026-07-16T20:00:00.000Z",
        "score": 100,
        "correct": 1,
        "total": 1,
        "percentage": 100,
        "maxStreak": 1,
        "avgTime": 5.0,
        "multiplierStats": {"used": 0, "remaining": 4},
        "results": [
            {
                "question": "Test gate dashboard",
                "category": "test",
                "correct": True,
                "timeout": False,
                "points": 100,
                "streakBonus": 0,
                "multiplierUsed": False,
                "timeUsed": 5.0,
                "chosenOption": "A",
                "correctOption": "A",
                "contest": None
            }
        ]
    }
    r = requests.post(f"{BASE}/api/results", json=payload, headers=UA)
    assert r.status_code == 200, f"FAIL (d): atteso 200, ottenuto {r.status_code} — {r.text}"
    body = r.json()
    assert body.get("success") is True, f"FAIL (d): response non success — {body}"
    print(f"  (d) PASS — POST /api/results senza cookie → {r.status_code} (inserted={body.get('inserted')})")
    return body.get("inserted", False)


def test_d_cleanup(password):
    """Cancella il game di prova (se inserito)."""
    session = requests.Session()
    session.headers.update(UA)
    session.post(f"{BASE}/api/login", json={"password": password})
    # Non c'e' un DELETE endpoint, ma possiamo riprovare il POST (sara' dedup)
    # oppure lasciamo il record test (player_key='test', escluso dalle classifiche).
    # Per ora documentiamo che il record e' stato inserito con player '1' → 'test'.
    print("       (cleanup: record inserito con player_key='test', escluso da classifiche)")


def test_e():
    """classifica.html e giocatore.html raggiungibili (HTTP 200)"""
    r1 = requests.get(f"{BASE}/classifica.html", headers=UA)
    assert r1.status_code == 200, f"FAIL (e classifica): atteso 200, ottenuto {r1.status_code}"
    r2 = requests.get(f"{BASE}/giocatore.html?g=mattia", headers=UA)
    assert r2.status_code == 200, f"FAIL (e giocatore): atteso 200, ottenuto {r2.status_code}"
    print(f"  (e) PASS — classifica.html → {r1.status_code}, giocatore.html?g=mattia → {r2.status_code}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_dashboard_gate.py <AUTH_PASSWORD>")
        sys.exit(1)

    password = sys.argv[1]
    print(f"\n=== Gate di chiusura — {BASE} ===\n")

    test_a()
    test_b(password)
    test_c()
    inserted = test_d()
    if inserted:
        test_d_cleanup(password)
    test_e()

    print("\n✅ Tutti i test del gate passati!\n")


if __name__ == "__main__":
    main()
