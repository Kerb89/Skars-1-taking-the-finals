"""E2E sulla preview reale: gioca l'intera partita DEMO (timer veri, API e D1
veri) e verifica che ogni risposta compaia nel tracciamento con ambiente
"preview", e non nella vista di default (produzione).

Uso:
    python giralettere/tests/test_preview.py https://feat-giralettere.skars-1.pages.dev [--headed]
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aiuti import DEMO, CONFIG  # noqa: E402

UA = "Mozilla/5.0 (GiralettereTest/1.0)"   # Bot Fight Mode blocca gli UA nudi di Python
G = DEMO["giochi"]


def api(base, **q):
    url = f"{base}/api/giralettere/tracciamento?" + "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in q.items())
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def attendi_input(page, selettore_testo, testo):
    page.wait_for_function(
        "([s, t]) => document.querySelector(s)?.textContent === t && document.querySelector('#risposta') && !document.querySelector('#risposta').disabled",
        arg=[selettore_testo, testo], timeout=15000)


def manche(page, gioco):
    page.wait_for_function("g => document.body.dataset.fase === 'intro:' + g", arg=gioco, timeout=20000)
    page.click("#btn-inizia")
    page.wait_for_function("g => document.body.dataset.fase === 'gioco:' + g", arg=gioco)


def avanti(page, gioco):
    page.wait_for_function("g => document.body.dataset.fase === 'riepilogo:' + g", arg=gioco, timeout=20000)
    page.click("#btn-avanti")


def gioca_demo(page):
    manche(page, "parole")
    v = G["parole"]["voci"]
    page.click(f'.tessera[data-tipo=parola][data-id="{v[0]["id"]}"]')
    page.click(f'.tessera[data-tipo=definizione][data-id="{v[1]["id"]}"]')          # errore voluto
    for x in v:
        page.click(f'.tessera[data-tipo=parola][data-id="{x["id"]}"]')
        page.click(f'.tessera[data-tipo=definizione][data-id="{x["id"]}"]')
    avanti(page, "parole")

    manche(page, "bocciato")
    for i, d in enumerate(G["bocciato"]["domande"]):
        page.wait_for_function("t => document.querySelector('#domanda')?.textContent === t && !document.querySelector('.opzione').disabled", arg=d["testo"], timeout=15000)
        scelta = d["corretta"] if i != 3 else 1 - d["corretta"]                       # un errore tollerato
        page.click(f'.opzione[data-indice="{scelta}"]')
    avanti(page, "bocciato")

    manche(page, "elemento")
    for i, x in enumerate(G["elemento"]["voci"]):
        attendi_input(page, "#domanda", x["definizione"])
        page.fill("#risposta", "televisore" if i == 0 else x["risposta"])
        page.click("#invia")
    avanti(page, "elemento")

    manche(page, "titolo")
    for x in G["titolo"]["voci"]:
        attendi_input(page, "#artista", x["artista"])
        page.fill("#risposta", x["risposta"])
        page.click("#invia")
    avanti(page, "titolo")

    manche(page, "manolesta")
    voci = G["manolesta"]["voci"]
    for x in voci[:3]:
        attendi_input(page, "#domanda", x["domanda"])
        page.fill("#risposta", x["risposta"])
        page.click("#invia")
    attendi_input(page, "#domanda", voci[3]["domanda"])
    page.fill("#risposta", "Frittata")                                                # errore: chiude la manche
    page.click("#invia")
    avanti(page, "manolesta")

    manche(page, "ruota")
    per_lettera = {x["lettera"]: x for x in G["ruota"]["voci"]}
    passata = False
    while page.evaluate("document.body.dataset.fase") == "gioco:ruota":
        try:
            page.wait_for_function("() => document.body.dataset.fase !== 'gioco:ruota' || (document.querySelector('#risposta') && !document.querySelector('#risposta').disabled)", timeout=15000)
        except Exception:
            break
        if page.evaluate("document.body.dataset.fase") != "gioco:ruota":
            break
        l = page.get_attribute("#regola-lettera", "data-lettera")
        if l == "B" and not passata:
            passata = True
            page.click("#passo")
        else:
            page.fill("#risposta", "automobile" if l == "A" else per_lettera[l]["risposta"])
            page.click("#invia")
        # dopo il feedback compare la lettera successiva, oppure la partita finisce
        page.wait_for_function("l => document.body.dataset.fase !== 'gioco:ruota' || document.querySelector('#regola-lettera')?.dataset.lettera !== l", arg=l, timeout=15000)
    page.wait_for_function("() => document.body.dataset.fase === 'fine'", timeout=20000)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base = sys.argv[1].rstrip("/")
    nick = f"e2e-{int(time.time())}"
    errori = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless="--headed" not in sys.argv)
        ctx = browser.new_context(user_agent=UA)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errori.append(str(e)))
        page.goto(f"{base}/giralettere/gioca/?partita=demo&gioco=tutti&nick={nick}")
        gioca_demo(page)
        page.wait_for_function("() => document.querySelector('#stato-invio')?.dataset.inAttesa === '0'", timeout=60000)
        log = page.evaluate("window.__giralettere.sessione.log")
        sid = page.evaluate("window.__giralettere.sessione.id")
        print(f"  partita giocata: nick={nick} sessione={sid} risposte={len(log)}")

        dati = api(base, vista="partita", partita="demo", giocatore=nick, ambiente="preview")["risposte"]
        per_id = {r["id"]: r for r in dati}
        assert len(dati) == len(log), f"tracciamento: {len(dati)} righe, giocate {len(log)}"
        for r in log:
            t = per_id.get(r["id"])
            assert t, f"risposta {r['id']} ({r['gioco']}/{r['domanda_id']}) assente nel tracciamento"
            for k in ("gioco", "domanda_id", "esito", "risposta_data", "risposta_attesa", "ordine"):
                assert t[k] == r[k], f"{r['id']} campo {k}: tracciamento={t[k]!r} giocata={r[k]!r}"
            assert t["ambiente"] == "preview", "ambiente deciso dal server sulla preview"
        assert [r["ordine"] for r in dati] == sorted(r["ordine"] for r in dati), "dettaglio in ordine"
        esiti = {e: sum(r["esito"] == e for r in log) for e in ("corretta", "sbagliata", "passata", "tempo_scaduto")}
        assert esiti["sbagliata"] >= 4 and esiti["passata"] == 1, esiti

        prod = api(base, vista="partite", giocatore=nick)["sessioni"]
        assert prod == [], "di default (produzione) la sessione di preview non deve comparire"
        sess = api(base, vista="partite", giocatore=nick, ambiente="preview")["sessioni"]
        assert len(sess) == 1 and sess[0]["sessione_id"] == sid and sess[0]["conclusa_at"], sess

        dom = api(base, vista="domande", partita="demo", giocatore=nick, ambiente="preview")
        assert any(x["domanda_id"] == "ru-A" and x["risposta_data"] == "automobile" for x in dom["sbagliate"]), "sbagliata ru-A nella vista per domanda"

        page.goto(f"{base}/giralettere/tracciamento/?vista=partita&partita=demo&giocatore={nick}&ambiente=preview")
        page.wait_for_function("() => document.body.dataset.stato === 'pronto'", timeout=20000)
        righe = page.locator("#vista-partita tbody tr").count()
        assert righe == len(log), f"pagina tracciamento: {righe} righe, attese {len(log)}"
        assert not errori, errori
        print(f"  OK: {len(log)} risposte DEMO presenti nel tracciamento (esiti {esiti}), assenti dalla vista produzione")
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("  FAIL:", e)
        sys.exit(1)
