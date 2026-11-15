"""Bocciato: promozione, bocciatura al secondo errore, tempo scaduto come errore."""
from aiuti import Partita, CONFIG, DEMO

CFG = CONFIG["bocciato"]
DOM = DEMO["giochi"]["bocciato"]["domande"]


def _clicca(p, i, giusta=True):
    d = DOM[i]
    scelta = d["corretta"] if giusta else 1 - d["corretta"]
    p.page.wait_for_function("t => document.querySelector('#domanda')?.textContent === t", arg=d["testo"])
    p.page.click(f'.opzione[data-indice="{scelta}"]')
    p.dopo_feedback()


def test_vittoria_con_un_errore_tollerato(browser, base):
    p = Partita(browser, base, "bocciato")
    p.inizia("bocciato")
    for i in range(12):
        _clicca(p, i, giusta=(i != 4))               # un solo errore: tollerato
    p.fase("fine")
    assert p.punti() == 11 * CFG["punti_corretta"]
    p.attendi_invio()
    righe = p.server.per_gioco("bocciato")
    assert len(righe) == 12 and [r["esito"] for r in righe].count("sbagliata") == 1
    p.chiudi()


def test_secondo_errore_boccia(browser, base):
    p = Partita(browser, base, "bocciato")
    p.inizia("bocciato")
    _clicca(p, 0, giusta=True)
    _clicca(p, 1, giusta=False)
    p.page.wait_for_function("t => document.querySelector('#domanda')?.textContent === t", arg=DOM[2]["testo"])
    p.page.click(f'.opzione[data-indice="{1 - DOM[2]["corretta"]}"]')
    p.page.wait_for_selector("#bocciato")
    p.dopo_feedback()
    p.fase("fine")
    assert p.punti() == CFG["punti_corretta"]
    p.attendi_invio()
    righe = p.server.per_gioco("bocciato")
    assert [r["esito"] for r in righe] == ["corretta", "sbagliata", "sbagliata"], "nessuna domanda dopo la bocciatura"
    assert righe[1]["risposta_data"] == DOM[1]["opzioni"][1 - DOM[1]["corretta"]]
    p.chiudi()


def test_tempo_scaduto_conta_come_errore(browser, base):
    p = Partita(browser, base, "bocciato")
    p.inizia("bocciato")
    p.scadi()    # scade la 1
    p.dopo_feedback()
    assert p.page.get_attribute("#errori", "data-errori") == "1"
    p.scadi()    # scade la 2 → bocciato
    p.dopo_feedback()
    p.fase("fine")
    p.attendi_invio()
    righe = p.server.per_gioco("bocciato")
    assert [r["esito"] for r in righe] == ["tempo_scaduto", "tempo_scaduto"]
    assert all(r["risposta_data"] is None for r in righe)
    assert p.punti() == 0
    p.chiudi()
