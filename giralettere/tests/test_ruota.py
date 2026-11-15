"""Ruota finale: tutte le lettere con un giro di "passo", errore, tempo scaduto,
più la partita completa con conversione punti → secondi."""
from aiuti import Partita, CONFIG, DEMO

RCFG = CONFIG["ruota"]
VOCI = DEMO["giochi"]["ruota"]["voci"]
PER_LETTERA = {v["lettera"]: v for v in VOCI}


def _corrente(p):
    p.page.wait_for_function("() => document.querySelector('#risposta') && !document.querySelector('#risposta').disabled")
    return p.page.get_attribute("#regola-lettera", "data-lettera")


def _stato(p, lettera):
    return p.page.get_attribute(f'.ruota-svg g[data-lettera="{lettera}"]', "data-stato")


def test_vittoria_con_passo(browser, base):
    p = Partita(browser, base, "ruota")
    p.inizia("ruota")
    assert int(p.page.text_content("#ruota-tempo")) == RCFG["secondi_standalone"]
    passate = []
    for _ in range(len(VOCI)):                      # primo giro: passo su A e B, il resto giusto
        l = _corrente(p)
        if l in ("A", "B") and l not in passate:
            p.page.click("#passo"); passate.append(l)
        else:
            p.rispondi(PER_LETTERA[l]["risposta"])
        p.dopo_feedback()
    assert _stato(p, "A") == "passata" and _stato(p, "C") == "corretta"
    for _ in passate:                               # secondo giro: tornano A e B
        l = _corrente(p)
        assert l in passate
        p.rispondi(PER_LETTERA[l]["risposta"])
        p.dopo_feedback()
    p.fase("fine")
    assert "21 lettere" in p.page.text_content("#fine")
    p.attendi_invio()
    righe = p.server.per_gioco("ruota")
    assert [r["esito"] for r in righe].count("passata") == 2
    assert [r["esito"] for r in righe].count("corretta") == 21
    p.chiudi()


def test_errore_e_tempo_fermo_nel_feedback(browser, base):
    p = Partita(browser, base, "ruota")
    p.inizia("ruota")
    assert _corrente(p) == "A"
    p.rispondi("automobile")
    p.page.wait_for_selector('.feedback[data-esito="sbagliata"]')
    fermo = int(p.page.get_attribute("#ruota-tempo", "data-restante-ms"))
    p.avanza(800)                                   # durante il feedback il tempo non scende
    assert int(p.page.get_attribute("#ruota-tempo", "data-restante-ms")) == fermo
    assert _stato(p, "A") == "sbagliata"
    p.dopo_feedback()
    assert _corrente(p) == "B"
    p.attendi_invio()
    r = p.server.per_gioco("ruota")[0]
    assert r["esito"] == "sbagliata" and r["risposta_data"] == "automobile" and r["risposta_attesa"] == "aereo"
    p.chiudi()


def test_tempo_scaduto(browser, base):
    p = Partita(browser, base, "ruota")
    p.inizia("ruota")
    _corrente(p)
    p.rispondi("aereo")
    p.dopo_feedback()
    _corrente(p)
    restante = int(p.page.get_attribute("#ruota-tempo", "data-restante-ms"))
    p.avanza(restante + 200)
    p.fase("fine")
    p.attendi_invio()
    righe = p.server.per_gioco("ruota")
    assert [r["esito"] for r in righe] == ["corretta", "tempo_scaduto"], "la manche finisce allo zero"
    assert righe[1]["domanda_id"] == "ru-B" and righe[1]["risposta_data"] is None
    p.chiudi()


def test_partita_completa_converte_punti_in_secondi(browser, base):
    p = Partita(browser, base, "tutti")
    giochi = CONFIG["ordine_giochi"]
    for g in giochi:                                 # nessuna risposta: ogni manche finisce a tempo
        p.inizia(g)
        while p.page.evaluate("document.body.dataset.fase") == "gioco:" + g:
            if p.page.locator(".tempo").count():
                p.scadi()
            p.avanza(CONFIG["flusso"]["pausa_feedback_ms"] + 50)
        if g != "ruota":
            p.fase("riepilogo:" + g)
            p.page.click("#btn-avanti")
    p.fase("intro:ruota")
    atteso = max(RCFG["secondi_minimi"], min(RCFG["secondi_massimi"], RCFG["secondi_base"]))
    assert p.page.text_content("#secondi-ruota") == f"{atteso} secondi"
    p.page.click("#btn-inizia")
    p.fase("gioco:ruota")
    assert int(p.page.text_content("#ruota-tempo")) == atteso
    p.chiudi()
