"""Supporto comune ai test Playwright di Giralettere.

- serve la root del repo in locale (le pagine usano percorsi relativi);
- intercetta POST /api/giralettere/sync e risponde come il server reale
  (accetta tutto, deduplica per id), registrando i payload;
- controlla il tempo con page.clock, così i timer si possono far scadere
  senza attese reali.
"""
import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

CARTELLA = Path(__file__).resolve().parent.parent          # giralettere/
ROOT = CARTELLA.parent                                     # root del repo
DEMO = json.loads((CARTELLA / "partite" / "demo.json").read_text(encoding="utf-8"))
CONFIG = json.loads((CARTELLA / "config.json").read_text(encoding="utf-8"))


class _Silenzioso(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def avvia_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Silenzioso, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


class FintoServer:
    """Simula /api/giralettere/sync. `fallimenti` = quante richieste far fallire prima."""

    def __init__(self, fallimenti=0):
        self.fallimenti = fallimenti
        self.richieste = []
        self.sessioni = {}
        self.risposte = {}

    def gestisci(self, route):
        req = route.request
        if req.method != "POST":
            return route.fulfill(status=404, body="")
        corpo = json.loads(req.post_data or "{}")
        self.richieste.append(corpo)
        if self.fallimenti > 0:
            self.fallimenti -= 1
            return route.fulfill(status=503, content_type="application/json", body='{"errore":"giu"}')
        acc = {"sessioni": [], "risposte": []}
        for s in corpo.get("sessioni", []):
            self.sessioni.setdefault(s["id"], {}).update({k: v for k, v in s.items() if v is not None})
            acc["sessioni"].append(s["id"])
        for r in corpo.get("risposte", []):
            self.risposte.setdefault(r["id"], r)
            acc["risposte"].append(r["id"])
        return route.fulfill(status=200, content_type="application/json",
                             body=json.dumps({"ambiente": "preview", "accettate": acc, "scartate": {"sessioni": [], "risposte": []}}))

    def per_gioco(self, gioco):
        return sorted((r for r in self.risposte.values() if r["gioco"] == gioco), key=lambda r: r["ordine"])


class Partita:
    """Una pagina di gioco pronta: clock installato, API simulate."""

    def __init__(self, browser, base, gioco, nick="TestBot", fallimenti=0):
        self.ctx = browser.new_context()
        self.page = self.ctx.new_page()
        self.server = FintoServer(fallimenti)
        self.errori_js = []
        self.page.on("pageerror", lambda e: self.errori_js.append(str(e)))
        self.page.route("**/api/giralettere/**", self.server.gestisci)
        self.page.clock.install()
        self.page.goto(f"{base}/giralettere/gioca/?partita=demo&gioco={gioco}&nick={nick}")

    def fase(self, valore, timeout=5000):
        self.page.wait_for_function("v => document.body.dataset.fase === v", arg=valore, timeout=timeout)

    def inizia(self, gioco):
        self.fase("intro:" + gioco)
        self.page.click("#btn-inizia")
        self.fase("gioco:" + gioco)

    def avanza(self, ms):
        self.page.clock.run_for(ms)

    def rispondi(self, testo):
        self.page.fill("#risposta", testo)
        self.page.click("#invia")

    def dopo_feedback(self):
        self.avanza(CONFIG["flusso"]["pausa_feedback_ms"] + 50)

    def attendi_invio(self, timeout=5000):
        self.page.wait_for_function(
            "() => document.querySelector('#stato-invio')?.dataset.inAttesa === '0'", timeout=timeout)

    def punti(self):
        return int(self.page.text_content("#punti"))

    def chiudi(self):
        assert not self.errori_js, f"errori JS: {self.errori_js}"
        self.ctx.close()


def voce(gioco, idx):
    g = DEMO["giochi"][gioco]
    return (g.get("voci") or g.get("domande"))[idx]
