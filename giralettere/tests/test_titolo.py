"""Completa il titolo: tutte giuste (anche con variante), errore, tempo scaduto."""
from aiuti import Partita, CONFIG, DEMO

CFG = CONFIG["titolo"]
VOCI = DEMO["giochi"]["titolo"]["voci"]


def _attendi(p, i):
    p.page.wait_for_function("a => document.querySelector('#artista')?.textContent === a "
                             "&& document.querySelector('#risposta') && !document.querySelector('#risposta').disabled",
                             arg=VOCI[i]["artista"])


def test_vittoria(browser, base):
    p = Partita(browser, base, "titolo")
    p.inizia("titolo")
    for i, v in enumerate(VOCI):
        _attendi(p, i)
        p.rispondi(v["varianti"][0] if v["varianti"] else v["risposta"])   # Glück vale come variante
        p.dopo_feedback()
    p.fase("fine")
    assert p.punti() == len(VOCI) * CFG["punti_corretta"]
    p.attendi_invio()
    assert all(r["esito"] == "corretta" for r in p.server.per_gioco("titolo"))
    p.chiudi()


def test_errore(browser, base):
    p = Partita(browser, base, "titolo")
    p.inizia("titolo")
    _attendi(p, 0)
    p.rispondi("rosso")
    p.page.wait_for_selector('.feedback[data-esito="sbagliata"]')
    assert VOCI[0]["risposta"] in p.page.text_content(".feedback")
    p.dopo_feedback()
    _attendi(p, 1)
    p.attendi_invio()
    r = p.server.per_gioco("titolo")[0]
    assert r["esito"] == "sbagliata" and r["risposta_data"] == "rosso" and r["risposta_attesa"] == VOCI[0]["risposta"]
    p.chiudi()


def test_tempo_scaduto(browser, base):
    p = Partita(browser, base, "titolo")
    p.inizia("titolo")
    for i in range(len(VOCI)):
        _attendi(p, i)
        p.scadi()
        p.page.wait_for_selector('.feedback[data-esito="tempo_scaduto"]')
        p.dopo_feedback()
    p.fase("fine")
    assert p.punti() == 0
    p.attendi_invio()
    righe = p.server.per_gioco("titolo")
    assert len(righe) == len(VOCI) and all(r["esito"] == "tempo_scaduto" for r in righe)
    p.chiudi()
