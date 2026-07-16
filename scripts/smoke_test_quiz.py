#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smoke_test_quiz.py — Smoke test runtime per le puntate del Quizzone (livello 2).

Apre la puntata in Chromium headless e verifica ciò che la validazione statica
NON può garantire:
  1. Click su "inizia" → il quiz parte davvero (il DOM cambia)
  2. La BGM va in play senza errori (o almeno il tentativo parte dal click)
  3. Si attraversa il quiz simulando risposte fino alla fine
  4. Click su invio → parte una richiesta verso l'endpoint atteso,
     INTERCETTATA (non inviata davvero), con payload JSON valido e
     tutti i campi obbligatori (incluso `contest` NON null)
  5. Zero errori in console durante l'intero flusso

USO:
    python smoke_test_quiz.py path/alla/puntata.html [--config quizzone_validator_config.json]

EXIT CODE: 0 = PASS, 1 = FAIL, 2 = errore di esecuzione.

DIPENDENZE:
    pip install playwright
    playwright install chromium

NOTA PER KIRO: questo test è il GATE FINALE. Una puntata non è "pronta"
finché questo script non esce con 0. Non modificare il test per farlo
passare: se fallisce, il bug è nella puntata.
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERRORE: manca playwright. Installa con:\n"
          "  pip install playwright\n  playwright install chromium")
    sys.exit(2)


def primo_selettore(page, selettori, timeout=2000):
    """Ritorna il primo selettore della lista che matcha un elemento visibile."""
    if isinstance(selettori, str):
        selettori = [selettori]
    for sel in selettori:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                return sel
        except Exception:
            continue
    return None


def main():
    ap = argparse.ArgumentParser(description="Smoke test runtime puntate Quizzone")
    ap.add_argument("html", help="Path del file HTML della puntata")
    ap.add_argument("--config", default=None)
    ap.add_argument("--visibile", action="store_true",
                    help="Esegui con browser visibile (debug)")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"ERRORE: file non trovato: {html_path}")
        sys.exit(2)

    cfg_path = Path(args.config) if args.config else \
        Path(__file__).parent / "quizzone_validator_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    sel_cfg = cfg["selettori"]
    api_cfg = cfg["api"]
    smoke = cfg["smoke_test"]
    timeout = smoke.get("timeout_ms", 15000)
    headless = smoke.get("headless", True) and not args.visibile

    errori = []
    console_errors = []
    richieste_api = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        # --autoplay-policy per non far fallire il .play() in headless
        context = browser.new_context()
        page = context.new_page()

        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))

        # Intercetta OGNI richiesta verso gli endpoint API: la registra e la blocca
        pattern = smoke.get("pattern_endpoint_da_intercettare", "/api/")
        pattern_d1 = smoke.get("pattern_endpoint_d1", "skars-1.pages.dev/api/results")
        richieste_d1 = []

        def intercetta(route, request):
            if pattern in request.url:
                richieste_api.append({
                    "url": request.url,
                    "method": request.method,
                    "body": request.post_data,
                })
                route.fulfill(status=200, content_type="application/json",
                              body='{"success": true, "statsUpdated": true}')
            elif pattern_d1 in request.url:
                richieste_d1.append({
                    "url": request.url,
                    "method": request.method,
                    "body": request.post_data,
                })
                route.fulfill(status=200, content_type="application/json",
                              body='{"success": true, "inserted": true}')
            else:
                route.continue_()

        page.route("**/*", intercetta)

        print(f"\nSmoke test: {html_path.name}\n")
        page.goto(html_path.as_uri(), timeout=timeout)

        # ---- 0. Nome giocatore (se richiesto) --------------------------------
        nome_test = smoke.get("nome_giocatore_test", "TestBot")
        name_input = page.locator("#playerNameInput")
        if name_input.count() > 0 and name_input.is_visible():
            name_input.fill(nome_test)
            page.wait_for_timeout(300)
            print(f"  OK    NOME: inserito '{nome_test}' nel campo nome giocatore")

        # ---- 1. Tasto inizia -------------------------------------------------
        sel_start = primo_selettore(page, sel_cfg["tasto_inizia"])
        if not sel_start:
            errori.append("TASTO_INIZIA: bottone non trovato con i selettori del config")
        else:
            snapshot_prima = page.content()
            try:
                page.click(sel_start, timeout=5000)
                page.wait_for_timeout(800)
                if page.content() == snapshot_prima:
                    errori.append("TASTO_INIZIA: click eseguito ma il DOM non è cambiato "
                                  "→ il quiz non parte")
                else:
                    print("  OK    TASTO_INIZIA: click → il quiz parte (DOM cambiato)")
            except PWTimeout:
                errori.append("TASTO_INIZIA: bottone presente ma non cliccabile")

        # ---- 2. BGM ----------------------------------------------------------
        stato_audio = page.evaluate("""() => {
            const a = document.querySelector('audio');
            if (a) return {trovato: true, paused: a.paused, src: a.currentSrc || a.src};
            return {trovato: false};
        }""")
        if stato_audio.get("trovato"):
            if stato_audio.get("paused"):
                # in headless l'autoplay-policy può bloccare: warning, non errore
                print("  WARN  BGM: <audio> presente ma in pausa dopo lo start "
                      "(può essere la policy headless; verificare a mano una volta)")
            else:
                print("  OK    BGM: in riproduzione dopo il click su inizia")
        else:
            print("  WARN  BGM: nessun <audio> nel DOM (se la BGM usa new Audio() "
                  "il check è solo via console errors)")

        # ---- 3. Attraversa il quiz simulando risposte ------------------------
        # Il flusso reale: overlay intro (click) → opzioni visibili → click opzione
        # → confirmBtn → (contestazione su D23) → nextBtn → overlay intro → ripeti
        flusso_btns = smoke.get("flusso_risposta", ["#confirmBtn", "#nextBtn"])
        contest_domanda = 23  # contesta alla domanda 23 (metà quiz)
        contest_testo = "TEST_CONTESTAZIONE_SMOKE"
        contest_eseguita = False

        # Click primo overlay intro se presente (mostra la prima domanda)
        intro = page.locator(".intro-overlay:not(.hidden)")
        if intro.count() > 0 and intro.first.is_visible():
            try:
                intro.first.click(timeout=2000)
                page.wait_for_timeout(500)
            except Exception:
                pass

        sel_opzione = primo_selettore(page, sel_cfg["opzione_risposta"])
        risposte_date = 0
        if sel_opzione:
            max_iter = cfg.get("num_domande_attese", 45) + 10
            for _ in range(max_iter):
                # Se c'è un overlay intro, clicca per procedere
                intro = page.locator(".intro-overlay:not(.hidden)")
                if intro.count() > 0 and intro.first.is_visible():
                    try:
                        intro.first.click(timeout=2000)
                        page.wait_for_timeout(400)
                    except Exception:
                        pass

                opzioni = page.locator(sel_opzione)
                visibili = [i for i in range(opzioni.count())
                            if opzioni.nth(i).is_visible()]
                if not visibili:
                    break
                try:
                    opzioni.nth(visibili[0]).click(timeout=3000)
                    risposte_date += 1
                    page.wait_for_timeout(300)

                    # Click confirmBtn
                    confirm_loc = page.locator("#confirmBtn")
                    if confirm_loc.count() > 0 and confirm_loc.first.is_visible():
                        confirm_loc.first.click(timeout=2000)
                        page.wait_for_timeout(300)

                    # --- Percorso contestazione alla domanda target ---
                    if risposte_date == contest_domanda and not contest_eseguita:
                        contest_btn = page.locator("#contestBtn")
                        if contest_btn.count() > 0 and contest_btn.first.is_visible():
                            contest_btn.first.click(timeout=2000)
                            page.wait_for_timeout(300)
                            textarea = page.locator("#contestText")
                            if textarea.count() > 0 and textarea.first.is_visible():
                                textarea.first.fill(contest_testo)
                                page.wait_for_timeout(200)
                                save_btn = page.locator("#saveContestBtn")
                                if save_btn.count() > 0 and save_btn.first.is_visible():
                                    save_btn.first.click(timeout=2000)
                                    page.wait_for_timeout(200)
                                    contest_eseguita = True
                                    print(f"  OK    CONTEST: contestazione inserita alla D{contest_domanda}")

                    # Click nextBtn
                    next_loc = page.locator("#nextBtn")
                    if next_loc.count() > 0 and next_loc.first.is_visible():
                        next_loc.first.click(timeout=2000)
                        page.wait_for_timeout(300)
                except Exception:
                    break
            print(f"  INFO  ATTRAVERSAMENTO: {risposte_date} risposte simulate")
            if risposte_date == 0:
                errori.append("ATTRAVERSAMENTO: nessuna opzione cliccabile dopo lo start")
            if not contest_eseguita:
                errori.append("CONTEST: non è stato possibile eseguire la contestazione "
                              f"alla D{contest_domanda} (bottone non visibile o flusso bloccato)")
        else:
            errori.append("ATTRAVERSAMENTO: selettore opzioni non trovato — adattare il config")

        # ---- 4. Tasto invio + payload ----------------------------------------
        sel_invio = primo_selettore(page, sel_cfg["tasto_invio_risultati"])
        if sel_invio and page.locator(sel_invio).first.is_visible():
            try:
                page.click(sel_invio, timeout=5000)
                page.wait_for_timeout(1500)
            except PWTimeout:
                errori.append("TASTO_INVIO: presente ma non cliccabile")
        elif sel_invio:
            print("  WARN  TASTO_INVIO: bottone esiste ma non visibile a fine "
                  "attraversamento (il flusso potrebbe non essere arrivato in fondo)")
        else:
            errori.append("TASTO_INVIO: bottone non trovato con i selettori del config")

        if richieste_api:
            req = richieste_api[-1]
            print(f"  OK    API_WORKER: richiesta intercettata → {req['method']} {req['url']}")
            base = api_cfg["base_url_atteso"]
            if "TUODOMINIO" not in base and not req["url"].startswith(base):
                errori.append(f"API_WORKER: la richiesta punta a {req['url']}, atteso {base}")
            if req["body"]:
                try:
                    payload = json.loads(req["body"])
                    testo_payload = json.dumps(payload)
                    mancanti = [c for c in api_cfg["campi_payload_obbligatori"]
                                if c not in testo_payload]
                    if mancanti:
                        errori.append(f"API_PAYLOAD_WORKER: campi mancanti: {mancanti}")
                    else:
                        print("  OK    API_PAYLOAD_WORKER: tutti i campi obbligatori presenti")
                    # Verifica contestazione nel payload worker
                    if contest_eseguita and req["body"]:
                        inner = payload.get("payload", payload)
                        results_arr = inner.get("results", [])
                        if len(results_arr) >= contest_domanda:
                            contest_val = results_arr[contest_domanda - 1].get("contest")
                            if contest_val and contest_testo in str(contest_val):
                                print(f"  OK    CONTEST_WORKER: results[{contest_domanda - 1}].contest "
                                      f"= '{contest_val}' — valorizzato correttamente")
                            elif contest_val:
                                errori.append(f"CONTEST_WORKER: results[{contest_domanda - 1}].contest "
                                              f"= '{contest_val}' — presente ma testo diverso da atteso")
                            else:
                                errori.append(f"CONTEST_WORKER: results[{contest_domanda - 1}].contest "
                                              f"è null/vuoto — il flusso contestazione NON scrive "
                                              f"nel payload (bug client)")
                        else:
                            errori.append(f"CONTEST_WORKER: results ha solo {len(results_arr)} "
                                          f"elementi, attesi almeno {contest_domanda}")
                except json.JSONDecodeError:
                    errori.append("API_PAYLOAD_WORKER: il body della richiesta non è JSON valido")
            else:
                errori.append("API_PAYLOAD_WORKER: richiesta senza body")
        else:
            errori.append("API_WORKER: NESSUNA richiesta verso il worker intercettata dopo "
                          "il click su invio → i risultati non partono")

        # ---- 4b. Verifica richiesta D1 (dual-write) --------------------------
        if richieste_d1:
            req_d1 = richieste_d1[-1]
            print(f"  OK    API_D1: richiesta intercettata → {req_d1['method']} {req_d1['url']}")
            if req_d1["body"]:
                try:
                    payload_d1 = json.loads(req_d1["body"])
                    d1_campi = api_cfg.get("campi_payload_d1_obbligatori",
                                           ["uploadId", "quizId", "playerName", "timestamp",
                                            "score", "correct", "total", "results"])
                    mancanti_d1 = [c for c in d1_campi if c not in payload_d1]
                    if mancanti_d1:
                        errori.append(f"API_PAYLOAD_D1: campi mancanti: {mancanti_d1}")
                    else:
                        print("  OK    API_PAYLOAD_D1: tutti i campi obbligatori presenti "
                              f"(incluso uploadId='{payload_d1.get('uploadId','?')[:60]}')")
                    # uploadId non vuoto
                    uid = payload_d1.get("uploadId", "")
                    if not uid or not uid.strip():
                        errori.append("API_PAYLOAD_D1: uploadId è vuoto")
                    # Verifica contestazione nel payload D1
                    if contest_eseguita:
                        results_d1 = payload_d1.get("results", [])
                        if len(results_d1) >= contest_domanda:
                            contest_d1 = results_d1[contest_domanda - 1].get("contest")
                            if contest_d1 and contest_testo in str(contest_d1):
                                print(f"  OK    CONTEST_D1: results[{contest_domanda - 1}].contest "
                                      f"valorizzato correttamente")
                            else:
                                errori.append(f"CONTEST_D1: results[{contest_domanda - 1}].contest "
                                              f"= '{contest_d1}' — atteso '{contest_testo}'")
                except json.JSONDecodeError:
                    errori.append("API_PAYLOAD_D1: il body non è JSON valido")
            else:
                errori.append("API_PAYLOAD_D1: richiesta senza body")
        else:
            errori.append("API_D1: NESSUNA richiesta verso D1 intercettata dopo il click "
                          "su invio → dual-write non funziona")

        # ---- 5. Console errors ------------------------------------------------
        if console_errors:
            errori.append(f"CONSOLE: {len(console_errors)} errori in console; primo: "
                          f"{console_errors[0][:200]}")
        else:
            print("  OK    CONSOLE: zero errori JS durante l'intero flusso")

        browser.close()

    print("=" * 70)
    if errori:
        for e in errori:
            print(f"  FAIL  {e}")
        print("ESITO: FAIL")
        sys.exit(1)
    print("ESITO: PASS — la puntata supera lo smoke test")
    sys.exit(0)


if __name__ == "__main__":
    main()
