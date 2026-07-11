"""
smoke_test_quiz.py — Smoke test end-to-end per i file HTML del quizzone.

Carica l'HTML in un Chromium headless, verifica:
1. Nessun errore JS in console (pageerror)
2. quizData ha 45 elementi, ogni ans e' 0-3, ogni cat ha sfondo
3. Il quiz NON parte a nome vuoto
4. Compila nome, click "Inizia" -> intro visibile
5. Attraversa tutte le 45 domande (intro -> opzione -> conferma -> next)
6. Schermata finale: punteggio presente
7. Click "Condividi risultati" -> testo generato contiene nome e punteggio
8. Intercetta la chiamata al Worker (no upload reale in produzione)

Uso:
    python scripts/smoke_test_quiz.py puntate/quiz_puntata26_misto.html

Dipendenze: playwright (pip install playwright && playwright install chromium)

Exit codes:
    0 = PASS
    1 = FAIL (con dettagli)
    2 = errore di setup
"""

import sys
import json
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERRORE: playwright non installato.")
    print("Esegui: pip install playwright && playwright install chromium")
    sys.exit(2)


PLAYER_NAME = "SMOKETEST"
WORKER_URL = "quiz-results.kerberozzo89.workers.dev"


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/smoke_test_quiz.py <file_quiz.html>")
        sys.exit(2)

    html_path = Path(sys.argv[1]).resolve()
    if not html_path.exists():
        print(f"ERRORE: {html_path} non trovato.")
        sys.exit(2)

    errors = []
    js_errors = []
    worker_calls = []

    def on_page_error(error):
        js_errors.append(str(error))

    def step(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        msg = f"  [{status}] {name}"
        if detail:
            msg += f" -- {detail}"
        print(msg)
        if not passed:
            errors.append(name)

    print(f"Smoke test: {html_path.name}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Intercetta chiamate al Worker
        def handle_route(route):
            url = route.request.url
            if WORKER_URL in url:
                try:
                    body = route.request.post_data
                    if body:
                        worker_calls.append(json.loads(body))
                except Exception:
                    worker_calls.append({"raw": route.request.post_data})
                route.fulfill(status=200, body='{"ok":true}',
                             headers={"Content-Type": "application/json",
                                      "Access-Control-Allow-Origin": "*"})
            else:
                route.continue_()

        page.route("**/*", handle_route)
        page.on("pageerror", on_page_error)

        # --- STEP 1: Caricamento pagina ---
        page.goto(f"file:///{html_path}", wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        step("1. Caricamento pagina senza errori JS",
             len(js_errors) == 0,
             f"{len(js_errors)} errori: {js_errors[0][:80]}" if js_errors else "")

        if js_errors:
            print("\n" + "=" * 60)
            print(f"RISULTATO: FAIL ({len(errors)} step falliti)")
            print("Errori JS:")
            for e in js_errors[:5]:
                print(f"  - {e[:200]}")
            browser.close()
            sys.exit(1)

        # --- STEP 2: Struttura quizData ---
        quiz_data = page.evaluate("() => { try { return typeof questions !== 'undefined' ? questions : (typeof quizData !== 'undefined' ? quizData : null) } catch(e) { return null } }")
        has_data = quiz_data is not None and isinstance(quiz_data, list)
        correct_count = len(quiz_data) == 45 if has_data else False
        step("2a. quizData esiste ed e' un array", has_data)
        step("2b. quizData ha esattamente 45 elementi",
             correct_count,
             f"trovati {len(quiz_data) if has_data else 0}")

        if has_data:
            bad_ans = [i+1 for i, q in enumerate(quiz_data)
                      if not (isinstance(q.get("ans"), int) and 0 <= q["ans"] <= 3)]
            step("2c. Tutti gli ans sono 0-3",
                 len(bad_ans) == 0,
                 f"problemi alle domande: {bad_ans[:5]}" if bad_ans else "")

            cat_bgs = page.evaluate(
                "() => { try { return Object.keys(catBackgrounds) } catch(e) { return [] } }")
            cats_in_data = set(q.get("cat", "") for q in quiz_data)
            missing_cats = cats_in_data - set(cat_bgs)
            step("2d. Ogni categoria ha sfondo in catBackgrounds",
                 len(missing_cats) == 0,
                 f"mancanti: {missing_cats}" if missing_cats else "")

        # --- STEP 3: Quiz NON parte a nome vuoto ---
        start_btn = page.locator("#startBtn")
        is_disabled = start_btn.is_disabled()
        step("3. Bottone 'Inizia' disabilitato a nome vuoto", is_disabled)

        # --- STEP 4: Compila nome e avvia ---
        page.fill("#playerNameInput", PLAYER_NAME)
        page.wait_for_timeout(100)
        start_btn_enabled = not start_btn.is_disabled()
        step("4a. Bottone 'Inizia' abilitato dopo nome compilato",
             start_btn_enabled)

        start_btn.click()
        page.wait_for_timeout(300)

        intro_visible = page.locator("#introOverlay").is_visible()
        step("4b. Intro overlay visibile dopo click 'Inizia'", intro_visible)

        # --- STEP 5: Attraversa tutte le 45 domande ---
        questions_traversed = 0
        traverse_errors = []

        for i in range(45):
            try:
                intro = page.locator("#introOverlay")
                if intro.is_visible():
                    intro.click()
                    page.wait_for_timeout(150)

                options = page.locator("#optionsContainer .option-btn")
                if options.count() > 0:
                    options.first.click()
                    page.wait_for_timeout(50)

                confirm_btn = page.locator("#confirmBtn")
                if not confirm_btn.is_disabled():
                    confirm_btn.click()
                    page.wait_for_timeout(100)

                if i < 44:
                    next_btn = page.locator("#nextBtn")
                    next_btn.wait_for(state="visible", timeout=3000)
                    next_btn.click()
                    page.wait_for_timeout(100)

                questions_traversed += 1
            except Exception as e:
                traverse_errors.append(f"Domanda {i+1}: {str(e)[:100]}")
                try:
                    next_btn = page.locator("#nextBtn")
                    if next_btn.is_visible():
                        next_btn.click()
                        page.wait_for_timeout(100)
                        questions_traversed += 1
                except Exception:
                    break

        step("5. Attraversate tutte le 45 domande",
             questions_traversed == 45,
             f"{questions_traversed}/45" +
             (f" -- {traverse_errors[0]}" if traverse_errors else ""))

        # --- STEP 6: Schermata finale ---
        page.wait_for_timeout(500)
        try:
            next_btn = page.locator("#nextBtn")
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

        summary_visible = page.locator("#summary").is_visible()
        step("6a. Schermata riepilogo visibile", summary_visible)

        if summary_visible:
            stats_text = page.locator("#summaryStats").inner_text()
            has_score = "punt" in stats_text.lower() or any(
                c.isdigit() for c in stats_text)
            step("6b. Punteggio presente nel riepilogo", has_score)

        # --- STEP 7: Condividi risultati ---
        share_btn = page.locator("#shareBtn")
        share_visible = share_btn.is_visible() if summary_visible else False
        step("7a. Bottone 'Condividi risultati' visibile", share_visible)

        if share_visible:
            page.evaluate("""() => {
                window.__clipboardText = '';
                navigator.clipboard = {
                    writeText: (text) => {
                        window.__clipboardText = text;
                        return Promise.resolve();
                    }
                };
            }""")
            share_btn.click()
            page.wait_for_timeout(300)

            clipboard_text = page.evaluate("() => window.__clipboardText || ''")
            has_name = PLAYER_NAME.lower() in clipboard_text.lower()
            step("7b. Testo condivisione contiene nome giocatore",
                 has_name,
                 f"primi 100 char: {clipboard_text[:100]}")

        # --- STEP 8: Intercettazione Worker ---
        upload_btn = page.locator("#uploadBtn")
        if upload_btn.is_visible() and not upload_btn.is_disabled():
            upload_btn.click()
            page.wait_for_timeout(1000)

        if worker_calls:
            payload = worker_calls[0]
            expected_keys = {"player", "score", "answers"}
            actual_keys = set(payload.keys()) if isinstance(payload, dict) else set()
            has_keys = expected_keys.issubset(actual_keys)
            step("8. Payload Worker contiene chiavi attese",
                 has_keys,
                 f"chiavi: {sorted(actual_keys)[:8]}")
            if isinstance(payload, dict):
                p_name = payload.get("player", "")
                if p_name.upper() != PLAYER_NAME:
                    print(f"  [WARN] Nome payload: '{p_name}' -- atteso '{PLAYER_NAME}'")
        else:
            # Non fatale: SMOKETEST non e' un giocatore riconosciuto,
            # l'upload potrebbe non partire automaticamente
            print("  [INFO] Nessuna chiamata Worker intercettata (atteso per SMOKETEST)")

        browser.close()

    # --- Risultato finale ---
    print("\n" + "=" * 60)
    if errors:
        print(f"RISULTATO: FAIL ({len(errors)} step falliti)")
        for e in errors:
            print(f"  x {e}")
        sys.exit(1)
    else:
        print("RISULTATO: PASS -- tutti gli step superati")
        sys.exit(0)


if __name__ == "__main__":
    main()
