"""
Rilevamento 'regali' (giveaway) lessicali per valida_quiz.py

Logica: una domanda 'si auto-risponde' quando un token discriminante
della risposta corretta compare NEL testo della domanda ma NON compare
in nessuno dei distrattori. E' il token che sta solo dalla parte giusta
a tradire il quiz.

Esempio bersaglio:
    D: "...ottenuto dalla spremitura dei semi di LINO..."
    Corretta:   "Olio di LINO"        -> token {olio, lino}
    Distrattori: canola / noce / canapa
    -> 'olio' e' in tutti i distrattori (rumore, si scarta)
    -> 'lino' e' SOLO nella corretta e compare nella domanda -> REGALO

Cosa NON prende (onesto): leak concettuali/etimologici senza overlap
lessicale. Es. 'acido alfa-linolenico' che punta a 'lino' via etimologia,
oppure 'bandiera con foglia rossa' -> Canada. Per quelli serve il pass LLM.
"""

import re
import unicodedata

# --- Normalizzazione (rimpiazza con la tua se ne hai gia' una piu' completa) ---

def _normalizza(testo: str) -> str:
    """minuscolo + rimozione diacritici (NFKD)."""
    testo = testo.lower()
    testo = unicodedata.normalize("NFKD", testo)
    return "".join(c for c in testo if not unicodedata.combining(c))


# Stopword + verbi definitori: gia' normalizzati (senza diacritici).
# I 'verbi definitori' sono il rumore tipico delle domande enciclopediche
# ("ottenuto", "considerato"...) che altrimenti sporcano il confronto.
_STOP = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
    "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
    "del", "dello", "della", "dei", "degli", "delle",
    "dal", "dallo", "dalla", "dai", "dagli", "dalle",
    "nel", "nello", "nella", "nei", "negli", "nelle",
    "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "al", "allo", "alla", "ai", "agli", "alle", "col", "coi",
    "e", "ed", "o", "od", "ma", "se", "che", "chi", "cui", "non",
    "come", "quale", "quali", "quanto", "quanti", "dove", "quando",
    "questo", "questa", "questi", "queste", "quello", "quella",
    "suo", "sua", "suoi", "sue", "loro", "piu", "meno", "molto",
    # verbi/participi definitori
    "e", "era", "sono", "essere", "stato", "viene", "vengono",
    "ottenuto", "ottenuta", "ottenuti", "ottenute",
    "considerato", "considerata", "considerati", "considerate",
    "chiamato", "chiamata", "detto", "detta", "noto", "nota",
    "prodotto", "prodotta", "definito", "definita",
}


def _stem(tok: str) -> str:
    """Troncamento grezzo: neutralizza genere/numero italiani comuni.
    Volutamente conservativo per non fondere parole diverse."""
    for suf in ("issimo", "issima", "mente", "zione", "sione", "amente"):
        if tok.endswith(suf) and len(tok) > len(suf) + 2:
            return tok[: -len(suf)]
    if len(tok) > 4 and tok[-1] in "aeiohl":
        return tok[:-1]
    return tok


def _token_contenuto(testo: str) -> set:
    grezzi = re.findall(r"[a-z0-9]+", _normalizza(testo))
    return {_stem(t) for t in grezzi if t not in _STOP and len(t) > 2}


def rileva_regalo(domanda: str, corretta: str, distrattori: list,
                  soglia_quota: float = 0.0) -> dict | None:
    """
    Ritorna None se la domanda e' pulita, oppure un dict con i dettagli
    del leak se e' un regalo.

    Parametri
    ---------
    domanda      : testo della domanda (senza le opzioni)
    corretta     : testo della risposta corretta (senza il prefisso "A) ")
    distrattori  : lista dei testi delle 3 risposte sbagliate
    soglia_quota : opzionale. Se > 0, flagga solo quando la quota di
                   risposta 'regalata' supera la soglia. Default 0.0 =
                   basta UN token discriminante per far scattare il flag.

    Dict di ritorno
    ---------------
    {
        "token_leak": ["lino"],   # i token traditori
        "quota":      0.5,        # frazione dei token della risposta rivelati
        "severita":   "ALTA"|"MEDIA"
    }
    """
    tok_corr = _token_contenuto(corretta)
    if not tok_corr:
        return None

    tok_dom = _token_contenuto(domanda)
    tok_distr = set()
    for d in distrattori:
        tok_distr |= _token_contenuto(d)

    # token della corretta presenti nella domanda...
    nella_domanda = tok_corr & tok_dom
    # ...ma assenti da TUTTI i distrattori -> sono il leak vero
    discriminanti = nella_domanda - tok_distr

    if not discriminanti:
        return None

    quota = len(discriminanti) / len(tok_corr)
    if quota < soglia_quota:
        return None

    return {
        "token_leak": sorted(discriminanti),
        "quota": round(quota, 2),
        "severita": "ALTA" if quota >= 0.5 else "MEDIA",
    }


# --- esempio d'uso / self-test ---------------------------------------------

if __name__ == "__main__":
    D = ("Quale olio vegetale, ottenuto dalla spremitura dei semi di lino, "
         "e' considerato la fonte vegetale piu' concentrata di acido "
         "alfa-linolenico, un omega-3?")
    corr = "Olio di lino"
    distr = ["Olio di canola", "Olio di noce", "Olio di canapa"]

    esito = rileva_regalo(D, corr, distr)
    print("Caso lino:", esito)
    # atteso -> {'token_leak': ['lino'], 'quota': 0.5, 'severita': 'ALTA'}

    # falso positivo da evitare: token condiviso coi distrattori
    D2 = "Quale squadra della citta' di Milano gioca a San Siro in blu e nero?"
    print("Caso Inter:", rileva_regalo(D2, "Inter", ["Milan", "Roma", "Napoli"]))
    # atteso -> None  (nessun token della risposta e' nella domanda)
