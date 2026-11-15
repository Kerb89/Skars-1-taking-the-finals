"""Parole impossibili: vittoria, errore (reset della sequenza), tempo scaduto."""
from aiuti import Partita, CONFIG, DEMO

CFG = CONFIG["parole"]
VOCI = DEMO["giochi"]["parole"]["voci"]


def _abbina(p, id_parola, id_def):
    p.page.click(f'.tessera[data-tipo=parola][data-id="{id_parola}"]')
    p.page.click(f'.tessera[data-tipo=definizione][data-id="{id_def}"]')


def test_vittoria(browser, base):
    p = Partita(browser, base, "parole")
    p.inizia("parole")
    for v in VOCI:
        _abbina(p, v["id"], v["id"])
    p.fase("fine")
    assert p.punti() == 8 * CFG["punti_per_abbinamento"] + CFG["bonus_completamento"]
    p.attendi_invio()
    righe = p.server.per_gioco("parole")
    assert len(righe) == 8 and all(r["esito"] == "corretta" for r in righe)
    p.chiudi()


def test_errore_azzera_la_sequenza(browser, base):
    p = Partita(browser, base, "parole")
    p.inizia("parole")
    _abbina(p, VOCI[0]["id"], VOCI[0]["id"])
    _abbina(p, VOCI[1]["id"], VOCI[1]["id"])
    assert p.page.get_attribute("#progresso", "data-abbinate") == "2"
    _abbina(p, VOCI[2]["id"], VOCI[3]["id"])          # sbagliato
    assert p.page.get_attribute("#progresso", "data-abbinate") == "0"
    assert p.page.locator(".tessera.abbinata").count() == 0
    p.attendi_invio()
    righe = p.server.per_gioco("parole")
    assert [r["esito"] for r in righe] == ["corretta", "corretta", "sbagliata"]
    assert righe[2]["risposta_data"] == VOCI[3]["definizione"]
    assert righe[2]["risposta_attesa"] == VOCI[2]["definizione"]
    p.chiudi()


def test_tempo_scaduto(browser, base):
    p = Partita(browser, base, "parole")
    p.inizia("parole")
    _abbina(p, VOCI[0]["id"], VOCI[0]["id"])
    p.avanza(CFG["durata_s"] * 1000 + 200)
    p.fase("fine")
    assert p.punti() == CFG["punti_per_abbinamento"]   # 1 abbinamento valido, niente bonus
    p.attendi_invio()
    righe = p.server.per_gioco("parole")
    assert sum(r["esito"] == "tempo_scaduto" for r in righe) == 7
    assert all(r["risposta_data"] is None for r in righe if r["esito"] == "tempo_scaduto")
    p.chiudi()
