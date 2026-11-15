"""Pagina di tracciamento con API simulate: viste, filtri, risposte sbagliate ricorrenti."""
import json
from urllib.parse import urlparse, parse_qs

from aiuti import CONFIG

SESSIONI = [
    {"sessione_id": "11111111-1111-4111-8111-111111111111", "partita_id": "demo", "giocatore": "Ada", "gioco_avviato": "tutti",
     "ambiente": "production", "punti_json": '{"parole":40,"bocciato":55}', "secondi_ruota": 78, "avviata_at": "2026-11-15T20:00:00Z",
     "conclusa_at": "2026-11-15T20:20:00Z", "risposte": 3, "corrette": 1},
    {"sessione_id": "22222222-2222-4222-8222-222222222222", "partita_id": "demo", "giocatore": "Bea", "gioco_avviato": "ruota",
     "ambiente": "production", "punti_json": "{}", "secondi_ruota": 150, "avviata_at": "2026-11-15T21:00:00Z",
     "conclusa_at": None, "risposte": 1, "corrette": 0},
]
RISPOSTE = [
    {"id": "a1", "sessione_id": SESSIONI[0]["sessione_id"], "partita_id": "demo", "giocatore": "Ada", "gioco": "ruota", "domanda_id": "ru-A",
     "ordine": 1, "risposta_data": "Automobile", "risposta_attesa": "aereo", "esito": "sbagliata", "tempo_ms": 2100, "client_ts": "2026-11-15T20:15:00Z"},
    {"id": "a2", "sessione_id": SESSIONI[0]["sessione_id"], "partita_id": "demo", "giocatore": "Ada", "gioco": "ruota", "domanda_id": "ru-B",
     "ordine": 2, "risposta_data": None, "risposta_attesa": "banana", "esito": "passata", "tempo_ms": 900, "client_ts": "2026-11-15T20:15:05Z"},
]
DOMANDE = {
    "domande": [
        {"gioco": "ruota", "domanda_id": "ru-A", "risposta_attesa": "aereo", "totale": 4, "corrette": 1, "sbagliate": 3, "passate": 0, "scadute": 0},
        {"gioco": "titolo", "domanda_id": "ti-02", "risposta_attesa": "spericolata", "totale": 2, "corrette": 1, "sbagliate": 1, "passate": 0, "scadute": 0},
    ],
    "sbagliate": [
        {"gioco": "ruota", "domanda_id": "ru-A", "risposta_data": "Automobile", "volte": 1},
        {"gioco": "ruota", "domanda_id": "ru-A", "risposta_data": "l'automobile", "volte": 1},
        {"gioco": "ruota", "domanda_id": "ru-A", "risposta_data": "aeroporto", "volte": 1},
        {"gioco": "titolo", "domanda_id": "ti-02", "risposta_data": "spericolato", "volte": 1},
    ],
}


def _pagina(browser, base, query=""):
    ctx = browser.new_context()
    page = ctx.new_page()
    chiamate = []

    def gestisci(route):
        q = {k: v[0] for k, v in parse_qs(urlparse(route.request.url).query).items()}
        chiamate.append(q)
        v = q.get("vista")
        corpo = {
            "filtri": {"giocatori": ["Ada", "Bea"], "partite": ["demo"], "giochi": ["parole", "bocciato", "elemento", "titolo", "manolesta", "ruota"]},
            "partite": {"sessioni": SESSIONI},
            "partita": {"risposte": RISPOSTE},
            "giocatori": {"giocatori": [{"giocatore": "Ada", "gioco": "ruota", "totale": 2, "corrette": 1, "sbagliate": 1, "passate": 0, "scadute": 0, "tempo_medio_ms": 1500, "sessioni": 1}]},
            "domande": DOMANDE,
        }.get(v, {"errore": "?"})
        route.fulfill(status=200, content_type="application/json", body=json.dumps(corpo))

    page.route("**/api/giralettere/tracciamento**", gestisci)
    page.goto(f"{base}/giralettere/tracciamento/{query}")
    page.wait_for_function("() => document.body.dataset.stato === 'pronto'")
    return ctx, page, chiamate


def _attendi_vista(page, selettore):
    page.wait_for_selector(selettore)
    page.wait_for_function("() => document.body.dataset.stato === 'pronto'")


def test_elenco_partite_e_filtro_produzione_di_default(browser, base):
    ctx, page, chiamate = _pagina(browser, base)
    assert page.input_value("#f-ambiente") == "production"
    assert all(c.get("ambiente") == "production" for c in chiamate), chiamate
    assert page.locator("#vista-partite tr[data-sessione]").count() == 2
    assert "in corso" in page.text_content(f'tr[data-sessione="{SESSIONI[1]["sessione_id"]}"]')
    ctx.close()


def test_dettaglio_partita_in_ordine(browser, base):
    ctx, page, chiamate = _pagina(browser, base)
    page.click(f'tr[data-sessione="{SESSIONI[0]["sessione_id"]}"] a')
    _attendi_vista(page, "#vista-partita")
    assert chiamate[-1]["vista"] == "partita" and chiamate[-1]["partita"] == "demo" and chiamate[-1]["giocatore"] == "Ada"
    righe = page.locator("#vista-partita tbody tr")
    assert righe.count() == 2
    assert righe.nth(0).get_attribute("data-esito") == "sbagliata"
    assert righe.nth(0).locator(".risposta-data").text_content() == "Automobile"
    assert "vista=partita" in page.url and "giocatore=Ada" in page.url
    ctx.close()


def test_filtri_passati_all_api(browser, base):
    ctx, page, chiamate = _pagina(browser, base, "?vista=giocatori")
    _attendi_vista(page, "#vista-giocatori")
    page.select_option("#f-gioco", "ruota")
    page.wait_for_function("() => document.body.dataset.stato === 'pronto'")
    page.select_option("#f-ambiente", "tutti")
    page.wait_for_function("() => document.body.dataset.stato === 'pronto'")
    ultima = chiamate[-1]
    assert ultima["vista"] == "giocatori" and ultima["gioco"] == "ruota" and ultima["ambiente"] == "tutti", ultima
    assert page.text_content('tr[data-giocatore="Ada"] .pct') == "50%"
    ctx.close()


def test_vista_domande_evidenzia_sbagliate_ricorrenti(browser, base):
    ctx, page, _ = _pagina(browser, base, "?vista=domande")
    _attendi_vista(page, "#vista-domande")
    riga = page.locator('tr[data-domanda="ru-A"]')
    assert "ricorrente" in (riga.get_attribute("class") or "")
    voce = riga.locator('li[data-normalizzata="automobile"]')
    assert voce.get_attribute("data-volte") == "2", "Automobile e l'automobile sono la stessa risposta normalizzata"
    assert voce.get_attribute("data-ricorrente") == "true"
    assert CONFIG["tracciamento"]["soglia_ricorrente"] == 2
    assert riga.locator('li[data-normalizzata="aeroporto"]').get_attribute("data-ricorrente") == "false"
    assert "ricorrente" not in (page.locator('tr[data-domanda="ti-02"]').get_attribute("class") or "")
    prima = page.locator("#vista-domande tbody tr").first.get_attribute("data-domanda")
    assert prima == "ru-A", "le domande con sbagliate ricorrenti vanno in cima"
    ctx.close()
