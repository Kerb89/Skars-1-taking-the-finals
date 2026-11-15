"""Test del motore: normalizzazione, validazione contenuti, coda idempotente."""
import json

from aiuti import FintoServer, DEMO


def _pagina(browser, base, fallimenti=0):
    ctx = browser.new_context()
    page = ctx.new_page()
    srv = FintoServer(fallimenti)
    page.route("**/api/giralettere/**", srv.gestisci)
    page.goto(f"{base}/giralettere/")
    return ctx, page, srv


def test_normalizzazione(browser, base):
    ctx, page, _ = _pagina(browser, base)
    casi = page.evaluate("""async () => {
        const m = await import('./js/core/normalizza.js');
        const v = { risposta: 'aereo', varianti: ['aeroplano'] };
        return {
            articolo: m.normalizza("L'Aereo"), tipografico: m.normalizza('L’aereo'),
            accenti: m.normalizza('  PERCHÉ   è  '), il: m.normalizza('Il ragazzo della via Glück'),
            ok1: m.eAccettata(' AÈREO ', v), ok2: m.eAccettata('un aeroplano', v),
            plurale: m.eAccettata('aerei', v), vuota: m.eAccettata('', v), quasi: m.eAccettata('aerio', v),
        };
    }""")
    assert casi["articolo"] == "aereo" and casi["tipografico"] == "aereo", casi
    assert casi["accenti"] == "perche e", casi
    assert casi["il"] == "ragazzo della via gluck", casi
    assert casi["ok1"] and casi["ok2"], casi
    assert not casi["plurale"] and not casi["vuota"] and not casi["quasi"], "niente fuzzy matching"
    ctx.close()


def test_demo_rispetta_lo_schema(browser, base):
    ctx, page, _ = _pagina(browser, base)
    errori = page.evaluate("""async () => {
        const c = await import('./js/core/contenuto.js');
        const [cfg, p] = await Promise.all([c.caricaConfig(), c.caricaPartita('demo')]);
        return c.verificaPartita(p, cfg);
    }""")
    assert errori == [], errori
    assert DEMO["demo"] is True and "DEMO" in DEMO["titolo"]
    rotta = page.evaluate("""async () => {
        const c = await import('./js/core/contenuto.js');
        const cfg = await c.caricaConfig();
        const p = await c.caricaPartita('demo');
        p.giochi.parole.voci.pop();
        p.giochi.ruota.voci[0].risposta = 'zaino';
        return c.verificaPartita(p, cfg);
    }""")
    assert any("parole" in e for e in rotta) and any("ruota/ru-A" in e for e in rotta), rotta
    ctx.close()


def test_coda_retry_senza_duplicati(browser, base):
    ctx, page, srv = _pagina(browser, base, fallimenti=2)
    page.clock.install()
    page.evaluate("""async () => {
        const { CodaInvio } = await import('./js/core/coda-invio.js');
        const { Sessione } = await import('./js/core/stato.js');
        localStorage.clear();
        const coda = new CodaInvio({ endpoint: '/api/giralettere/sync', retryBaseMs: 1000, retryMaxMs: 4000 });
        const s = new Sessione({ coda, partitaId: 'demo', giocatore: 'Coda', giocoAvviato: 'bocciato' });
        for (let i = 0; i < 3; i++) s.registra({ gioco: 'bocciato', domanda_id: 'bo-0' + (i + 1),
            risposta_data: 'x', risposta_attesa: 'y', esito: 'sbagliata', tempo_ms: 100 });
        window.__coda = coda;
    }""")
    page.wait_for_function("() => window.__coda && window.__coda.tentativi >= 1")
    assert page.evaluate("JSON.parse(localStorage.getItem('giralettere.coda.v1')).risposte") != {}
    page.clock.run_for(10_000)
    page.wait_for_function("() => window.__coda.inAttesa() === 0")
    ids_inviati = [r["id"] for c in srv.richieste for r in c.get("risposte", [])]
    assert len(srv.risposte) == 3, srv.risposte
    assert set(ids_inviati) == set(srv.risposte), "i reinvii devono riusare gli stessi id"
    assert len(srv.richieste) >= 3, "attesi almeno due fallimenti e un invio riuscito"
    ctx.close()


def test_partita_inesistente(browser, base):
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(f"{base}/giralettere/gioca/?partita=nonesiste&gioco=tutti&nick=X")
    page.wait_for_selector("#errore")
    assert "non trovata" in page.text_content("#errore")
    ctx.close()
