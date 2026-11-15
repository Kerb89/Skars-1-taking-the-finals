"""Mano lesta: serie completa, errore che chiude, finestra di 3 s scaduta, tempo di risposta scaduto."""
from aiuti import Partita, CONFIG, DEMO

CFG = CONFIG["manolesta"]
VOCI = DEMO["giochi"]["manolesta"]["voci"]


def _serie(n):
    return n * CFG["punti_primo_in_serie"] + CFG["incremento_serie"] * n * (n - 1) // 2


def _attendi(p, i):
    p.page.wait_for_function("t => document.querySelector('#domanda')?.textContent === t "
                             "&& !document.querySelector('#risposta').disabled", arg=VOCI[i]["domanda"])


def test_serie_completa(browser, base):
    p = Partita(browser, base, "manolesta")
    p.inizia("manolesta")
    for i, v in enumerate(VOCI):
        _attendi(p, i)
        assert p.page.text_content("#lettera") == v["lettera"]
        p.rispondi(v["risposta"])
        p.dopo_feedback()
    p.fase("fine")
    assert p.punti() == _serie(len(VOCI))
    p.attendi_invio()
    assert all(r["esito"] == "corretta" for r in p.server.per_gioco("manolesta"))
    p.chiudi()


def test_errore_chiude_la_manche(browser, base):
    p = Partita(browser, base, "manolesta")
    p.inizia("manolesta")
    _attendi(p, 0)
    p.rispondi(VOCI[0]["risposta"])
    p.dopo_feedback()
    _attendi(p, 1)
    p.rispondi("Elefantino")                      # sbagliata, anche se inizia con la lettera giusta
    p.dopo_feedback()
    p.fase("fine")
    assert p.punti() == _serie(1)
    p.attendi_invio()
    righe = p.server.per_gioco("manolesta")
    assert [r["esito"] for r in righe] == ["corretta", "sbagliata"]
    assert righe[1]["risposta_data"] == "Elefantino"
    p.chiudi()


def test_finestra_di_inizio_scaduta(browser, base):
    p = Partita(browser, base, "manolesta")
    p.inizia("manolesta")
    _attendi(p, 0)
    assert p.page.get_attribute("#fase-mano", "data-fase") == "inizio"
    p.scadi()                                     # nessun tasto nei primi 3 s
    p.dopo_feedback()
    p.fase("fine")
    p.attendi_invio()
    r = p.server.per_gioco("manolesta")
    assert len(r) == 1 and r[0]["esito"] == "tempo_scaduto" and r[0]["risposta_data"] is None
    assert p.punti() == 0
    p.chiudi()


def test_primo_tasto_avvia_tempo_risposta(browser, base):
    p = Partita(browser, base, "manolesta")
    p.inizia("manolesta")
    _attendi(p, 0)
    p.avanza(2000)
    p.page.type("#risposta", "Pa")                # primo tasto entro i 3 s
    assert p.page.get_attribute("#fase-mano", "data-fase") == "risposta"
    p.avanza(2000)                                # oltre i 3 s iniziali: si continua
    assert p.page.is_enabled("#risposta")
    p.scadi()                                     # ma il tempo di risposta scade
    p.dopo_feedback()
    p.fase("fine")
    p.attendi_invio()
    r = p.server.per_gioco("manolesta")[0]
    assert r["esito"] == "tempo_scaduto"
    p.chiudi()
