"""Elemento comune: tutte giuste (con normalizzazione), errore, tempo scaduto."""
from aiuti import Partita, CONFIG, DEMO

CFG = CONFIG["elemento"]
EL = DEMO["giochi"]["elemento"]
VOCI = EL["voci"]


def _attendi_domanda(p, i):
    p.page.wait_for_function("t => document.querySelector('#domanda')?.textContent === t", arg=VOCI[i]["definizione"])


def test_vittoria(browser, base):
    p = Partita(browser, base, "elemento")
    p.inizia("elemento")
    assert EL["elemento"].upper() in p.page.text_content("#elemento")
    for i, v in enumerate(VOCI):
        _attendi_domanda(p, i)
        testo = v["risposta"] if i else "  Il " + v["risposta"].upper() + " "   # articolo, maiuscole, spazi
        p.rispondi(testo)
        p.dopo_feedback()
    p.fase("fine")
    assert p.punti() == len(VOCI) * CFG["punti_corretta"]
    p.attendi_invio()
    righe = p.server.per_gioco("elemento")
    assert all(r["esito"] == "corretta" for r in righe)
    assert righe[0]["risposta_data"] == "  Il " + VOCI[0]["risposta"].upper() + " ", "il testo grezzo va salvato com'è"
    p.chiudi()


def test_errore_registrato_e_si_prosegue(browser, base):
    p = Partita(browser, base, "elemento")
    p.inizia("elemento")
    _attendi_domanda(p, 0)
    p.rispondi("televisore")
    p.page.wait_for_selector('.feedback[data-esito="sbagliata"]')
    p.dopo_feedback()
    _attendi_domanda(p, 1)                                  # la serie continua
    p.rispondi(VOCI[1]["risposta"])
    p.dopo_feedback()
    p.attendi_invio()
    righe = p.server.per_gioco("elemento")
    assert righe[0]["esito"] == "sbagliata" and righe[0]["risposta_data"] == "televisore"
    assert righe[0]["risposta_attesa"] == VOCI[0]["risposta"]
    assert righe[1]["esito"] == "corretta"
    p.chiudi()


def test_tempo_scaduto_e_timer_fermo_all_invio(browser, base):
    p = Partita(browser, base, "elemento")
    p.inizia("elemento")
    _attendi_domanda(p, 0)
    p.page.fill("#risposta", "tele")                         # digitare non ferma il tempo
    p.scadi()
    p.page.wait_for_selector('.feedback[data-esito="tempo_scaduto"]')
    p.dopo_feedback()
    _attendi_domanda(p, 1)
    p.avanza(3000)
    p.rispondi(VOCI[1]["risposta"])                          # invio a ~3 s
    p.page.wait_for_selector('.feedback[data-esito="corretta"]')
    p.avanza(5000)                                           # dopo l'invio il tempo non scorre più
    p.attendi_invio()
    righe = p.server.per_gioco("elemento")
    assert righe[0]["esito"] == "tempo_scaduto" and righe[0]["risposta_data"] is None
    assert 2900 <= righe[1]["tempo_ms"] <= 3500, righe[1]["tempo_ms"]
    p.chiudi()
