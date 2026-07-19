#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_quiz_html.py — Validatore statico esteso per le puntate del Quizzone.

USO:
    python validate_quiz_html.py path/alla/puntata.html [--config quizzone_validator_config.json]

EXIT CODE: 0 = PASS, 1 = FAIL (errori bloccanti), 2 = errore di esecuzione.

CHECK IMPLEMENTATI (livello 1, statico):
  [STRUTTURA]
   1. Conteggio domande == num_domande_attese (default 45)
   2. Numerazione domande senza buchi né duplicati
   3. Esattamente UNA risposta corretta per domanda; opzioni non vuote e in numero consistente
   4. Box spiegazione presente per OGNI domanda
   5. ID DOM univoci
  [INTERATTIVITÀ]
   6. Tasto "inizia" presente + handler agganciato + gli id usati dal JS esistono nel DOM
   7. Tasto invio risultati presente + handler
  [MEDIA]
   8. BGM presente, file esistente nel repo, NIENTE attributo autoplay,
      .play() dentro l'handler dello start (euristica)
   9. Domande audio: ogni domanda marcata audio ha la sua traccia, file esistente,
      nessuna traccia duplicata tra domande diverse
  10. Immagini: src non vuoto, file esistente, niente placeholder
  [API]
  11. La fetch di invio punta al base URL del contratto (quizzone-07)
  12. Payload: tutti i campi obbligatori presenti nel JS (incluso `contest`)
  13. Nessun riferimento a endpoint vietati (vecchio worker / api.github.com)
  [QUALITÀ CODICE]
  14. JS sintatticamente valido (node --check, se node disponibile)
  15. Encoding UTF-8 pulito, nessun mojibake su accentate

DIPENDENZE: beautifulsoup4  (pip install beautifulsoup4)
            node opzionale per il syntax check JS.

NOTA PER KIRO: i selettori sono in quizzone_validator_config.json. Se un check
FALLISCE per selettore sbagliato (non per bug reale), correggi il CONFIG, non
questo script. Non disattivare check per far passare la validazione.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERRORE: manca beautifulsoup4. Installa con: pip install beautifulsoup4")
    sys.exit(2)

# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------

MOJIBAKE_PATTERNS = ["Ã¨", "Ã©", "Ã ", "Ã¹", "Ã²", "Ã¬", "â€™", "â€œ", "â€\x9d", "Â°", "Ã¢"]


class Report:
    def __init__(self):
        self.errori = []
        self.warning = []
        self.ok = []

    def err(self, check, msg):
        self.errori.append(f"[{check}] {msg}")

    def warn(self, check, msg):
        self.warning.append(f"[{check}] {msg}")

    def passed(self, check, msg=""):
        self.ok.append(f"[{check}] {msg}".rstrip())

    def stampa(self):
        print("=" * 70)
        for r in self.ok:
            print(f"  OK    {r}")
        for w in self.warning:
            print(f"  WARN  {w}")
        for e in self.errori:
            print(f"  FAIL  {e}")
        print("=" * 70)
        tot = len(self.ok) + len(self.warning) + len(self.errori)
        print(f"Totale check: {tot} | OK: {len(self.ok)} | "
              f"WARN: {len(self.warning)} | FAIL: {len(self.errori)}")
        print("ESITO: " + ("PASS" if not self.errori else "FAIL"))


def primo_selettore_valido(soup, selettori):
    """Prova una lista di selettori CSS, ritorna (selettore, elementi) del primo che matcha."""
    if isinstance(selettori, str):
        selettori = [selettori]
    for sel in selettori:
        try:
            found = soup.select(sel)
        except Exception:
            continue
        if found:
            return sel, found
    return None, []


def estrai_js(soup, html_path):
    """Concatena tutto il JS inline + i file locali referenziati da <script src>."""
    blocchi = []
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            if src.startswith(("http://", "https://", "//")):
                continue  # CDN: non validabile localmente
            p = (html_path.parent / src).resolve()
            if p.exists():
                blocchi.append(p.read_text(encoding="utf-8", errors="replace"))
        elif script.string:
            blocchi.append(script.string)
    return "\n".join(blocchi)


def risolvi_media(src, html_path, root_repo):
    """Risolve il path di un media relativo al file HTML o alla root del repo."""
    if not src or src.startswith(("http://", "https://", "data:", "//")):
        return None  # remoto o inline: esistenza non verificabile su disco
    base = Path(root_repo) if root_repo else html_path.parent
    candidati = [base / src.lstrip("/"), html_path.parent / src]
    for c in candidati:
        if c.resolve().exists():
            return c.resolve()
    return False  # locale ma inesistente


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------

def check_encoding(raw_bytes, testo, rep):
    try:
        raw_bytes.decode("utf-8")
        rep.passed("ENCODING", "file UTF-8 valido")
    except UnicodeDecodeError as e:
        rep.err("ENCODING", f"il file non è UTF-8 valido: {e}")
        return
    trovati = [m for m in MOJIBAKE_PATTERNS if m in testo]
    if trovati:
        rep.err("ENCODING", f"probabile mojibake (doppia codifica): {trovati[:5]}")
    else:
        rep.passed("ENCODING", "nessun mojibake rilevato")


def check_domande(soup, cfg, rep):
    """Check DOM statico per domande — WARN se il quiz è JS-rendered
    (check di sostanza è delegato a check_questions_json sul JSON inline)."""
    sel, domande = primo_selettore_valido(soup, cfg["selettori"]["domanda"])
    if not domande:
        rep.warn("DOMANDE_DOM", "nessun elemento domanda nel DOM statico "
                 "(quiz JS-rendered: check di sostanza via JSON inline)")
        return []
    attese = cfg["num_domande_attese"]
    if len(domande) != attese:
        rep.warn("DOMANDE_DOM", f"trovate {len(domande)} elementi domanda nel DOM statico, "
                 f"attese {attese} — quiz probabilmente JS-rendered")
    else:
        rep.passed("DOMANDE_DOM", f"{attese} domande trovate nel DOM (selettore: {sel})")
    return domande


def check_risposte(domande, cfg, rep):
    """Check DOM opzioni — skip se quiz JS-rendered (coperto da check_questions_json)."""
    if not domande:
        return


def check_spiegazioni(domande, cfg, rep):
    """Check DOM spiegazioni — skip se quiz JS-rendered (coperto da check_questions_json)."""
    if not domande:
        return


def check_id_univoci(soup, rep):
    ids = [el["id"] for el in soup.find_all(attrs={"id": True})]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        rep.err("ID_DOM", f"id duplicati nel DOM (rompono i selettori JS in silenzio): {dup}")
    else:
        rep.passed("ID_DOM", f"{len(ids)} id, tutti univoci")


def check_bottone(soup, js, cfg, rep, chiave, nome):
    sel, btn = primo_selettore_valido(soup, cfg["selettori"][chiave])
    if not btn:
        rep.err(nome, f"bottone non trovato (selettori: {cfg['selettori'][chiave]})")
        return None
    b = btn[0]
    btn_id = b.get("id", "")
    ha_onclick = b.has_attr("onclick")
    # Cerca riferimenti all'id nel JS: getElementById, querySelector, o helper $('id')
    ha_listener = bool(btn_id and re.search(
        rf"getElementById\(\s*['\"]{re.escape(btn_id)}['\"]\s*\)|"
        rf"querySelector\(\s*['\"]#{re.escape(btn_id)}['\"]\s*\)|"
        rf"\$\(\s*['\"]{re.escape(btn_id)}['\"]\s*\)|"
        rf"\b{re.escape(btn_id)}\b", js))
    if ha_onclick or ha_listener:
        rep.passed(nome, f"trovato ({sel}), handler agganciato "
                         f"({'onclick' if ha_onclick else 'addEventListener/riferimento JS'})")
    else:
        rep.err(nome, f"bottone trovato ({sel}) ma NESSUN handler rilevato: "
                      "né onclick né riferimento all'id nel JS → tasto morto")
    return b


def check_id_referenziati(soup, js, rep):
    """Ogni getElementById/#querySelector nel JS deve puntare a un id esistente nel DOM.
    Nota: id creati dinamicamente dal JS (createElement) sono esclusi dal check."""
    ids_dom = {el["id"] for el in soup.find_all(attrs={"id": True})}
    usati = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)", js))
    usati |= set(re.findall(r"querySelector(?:All)?\(\s*['\"]#([A-Za-z0-9_\-]+)['\"]\s*\)", js))
    # Cattura anche il pattern helper $('id') comune nei quiz minificati
    usati |= set(re.findall(r"\$\(\s*['\"]([A-Za-z0-9_\-]+)['\"]\s*\)", js))
    # Escludi id che sono creati dinamicamente (createElement + id assignment)
    creati = set(re.findall(r"\.id\s*=\s*['\"]([^'\"]+)['\"]", js))
    usati -= creati
    # esclude id costruiti dinamicamente (template literal, concatenazioni): non rilevabili
    mancanti = sorted(usati - ids_dom)
    if mancanti:
        rep.err("ID_REFERENZIATI", f"il JS referenzia id inesistenti nel DOM: {mancanti} "
                                   "→ classica causa di start button rotto")
    else:
        rep.passed("ID_REFERENZIATI", f"{len(usati)} id referenziati dal JS, tutti presenti nel DOM")


def check_bgm(soup, js, html_path, cfg, rep):
    root = cfg["media"]["root_repo"]
    est_audio = tuple(cfg["media"]["estensioni_audio"])
    # Candidati BGM: <audio> non dentro una domanda audio, oppure new Audio(...) nel JS
    audio_tags = soup.find_all("audio")
    bgm_src = None
    bgm_inline = False
    for a in audio_tags:
        src = a.get("src") or (a.find("source").get("src") if a.find("source") else None)
        if src:
            bgm_src = src
            if a.has_attr("autoplay"):
                rep.err("BGM", f"attributo autoplay su <audio src='{src}'>: i browser lo bloccano, "
                               "la BGM deve partire dal click su 'inizia'")
            break
    if not bgm_src:
        m = re.search(r"new\s+Audio\(\s*['\"]([^'\"]+)['\"]\s*\)", js)
        if m:
            bgm_src = m.group(1)
    # Check for BGM via variable (e.g. const BGM_SRC = "data:audio/..."; new Audio(BGM_SRC))
    if not bgm_src:
        if re.search(r'const\s+BGM_SRC\s*=\s*["\']data:audio/', js) and re.search(r'new\s+Audio\(\s*BGM_SRC\s*\)', js):
            bgm_inline = True
            bgm_src = "inline-base64"
    if not bgm_src:
        rep.err("BGM", "nessuna BGM trovata (né <audio> né new Audio() nel JS)")
        return
    if bgm_inline:
        rep.passed("BGM", "BGM inline base64 via costante BGM_SRC")
    elif not bgm_src.lower().endswith(est_audio) and not bgm_src.startswith("http"):
        rep.warn("BGM", f"estensione inattesa per la BGM: {bgm_src}")
    else:
        esiste = risolvi_media(bgm_src, html_path, root)
        if esiste is False:
            rep.err("BGM", f"file BGM referenziato ma INESISTENTE nel repo: {bgm_src}")
        elif esiste is None:
            rep.warn("BGM", f"BGM remota ({bgm_src}): esistenza non verificabile su disco")
        else:
            rep.passed("BGM", f"file presente: {bgm_src}")
    if cfg["js"]["richiedi_play_dentro_handler_start"]:
        # Euristica: .play() deve comparire nel JS e NON esserci autoplay
        if ".play(" in js:
            rep.passed("BGM_PLAY", ".play() presente nel JS (avvio da interazione)")
        else:
            rep.warn("BGM_PLAY", "nessuna chiamata .play() trovata nel JS: "
                                 "verificare che la BGM parta dal tasto inizia")


def check_tracce_audio(domande, html_path, cfg, rep):
    """Check DOM tracce audio — skip se quiz JS-rendered (coperto da check_questions_json)."""
    if not domande:
        return


def _match_attr_selector(el, sel):
    try:
        return bool(el.parent and el in el.parent.select(sel)) or bool(el.select(sel))
    except Exception:
        return False


def check_immagini(soup, html_path, cfg, rep):
    root = cfg["media"]["root_repo"]
    placeholders = [p.lower() for p in cfg["media"]["placeholder_vietati"]]
    problemi = []
    imgs = soup.find_all("img")
    for img in imgs:
        src = (img.get("src") or "").strip()
        if not src:
            problemi.append("<img> con src vuoto")
            continue
        if any(p in src.lower() for p in placeholders):
            problemi.append(f"placeholder residuo: {src}")
            continue
        esiste = risolvi_media(src, html_path, root)
        if esiste is False:
            problemi.append(f"file immagine inesistente: {src}")
    if problemi:
        for p in problemi:
            rep.err("IMMAGINI", p)
    else:
        rep.passed("IMMAGINI", f"{len(imgs)} immagini, tutte valide" if imgs
                   else "nessuna immagine in questa puntata (check saltato)")


def check_api(js, testo_html, cfg, rep):
    api = cfg["api"]
    # Check placeholder residui nel file (template non compilato)
    placeholders_testo = [p for p in cfg.get("media", {}).get("placeholder_vietati", [])
                          if p.startswith("{{")]
    for ph in placeholders_testo:
        if ph in testo_html:
            rep.err("PLACEHOLDER", f"placeholder residuo trovato nell'HTML: '{ph}' — "
                    "il template non è stato compilato completamente")
    if placeholders_testo and not any("PLACEHOLDER" in e for e in rep.errori):
        rep.passed("PLACEHOLDER", "nessun placeholder di template residuo")

    # Endpoint vietati
    vietati = [v for v in api["endpoint_vietati"]
               if v and "INSERISCI" not in v and v in testo_html]
    if vietati:
        rep.err("API_VIETATI", f"riferimenti a endpoint vietati (vecchio worker): {vietati}")
    else:
        rep.passed("API_VIETATI", "nessun riferimento a endpoint vietati")

    # --- Check 1: Worker URL (fetch principale) ---
    base = api["base_url_atteso"]
    fetches = re.findall(r"fetch\(\s*[`'\"]([^`'\"]+)[`'\"]", js)
    fetch_vars = re.findall(r"fetch\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*[,)]", js)
    url_in_vars = base in testo_html
    if "TUODOMINIO" in base:
        rep.warn("API_BASEURL", "base_url_atteso non ancora configurato nel config "
                                "(placeholder TUODOMINIO): check disattivato")
    elif fetches:
        giuste = [f for f in fetches if f.startswith(base)]
        if giuste:
            rep.passed("API_BASEURL", f"fetch verso il worker URL corretto: {giuste}")
        elif fetch_vars and url_in_vars:
            rep.passed("API_BASEURL", f"fetch tramite variabile, URL {base} presente nel file")
        else:
            rep.err("API_BASEURL", f"nessuna fetch punta a {base}; trovate: {fetches[:5]}")
    elif fetch_vars and url_in_vars:
        rep.passed("API_BASEURL", f"fetch tramite variabile, URL {base} presente nel file")
    elif fetch_vars:
        rep.warn("API_BASEURL", f"fetch usa variabile ({fetch_vars[:3]}) ma l'URL "
                 f"atteso {base} non trovato nel file")
    else:
        rep.err("API_BASEURL", "nessuna fetch() trovata nel JS: il tasto invio non manda nulla")

    # --- Check 2: D1 URL (dual-write) ---
    d1_url = api.get("d1_url_atteso", "")
    if d1_url:
        d1_in_file = d1_url in testo_html
        d1_fetches = [f for f in fetches if d1_url in f]
        d1_var_match = any(d1_url in testo_html for _ in fetch_vars)
        if d1_fetches or d1_in_file:
            rep.passed("API_D1_URL", f"fetch verso D1 endpoint presente: {d1_url}")
        else:
            rep.err("API_D1_URL", f"dual-write: nessun riferimento a {d1_url} nel file "
                    "— la seconda fetch (D1) è obbligatoria dal passo 3")

    # --- Check 3: Campi payload worker ---
    mancanti = [c for c in api["campi_payload_obbligatori"] if not re.search(
        rf"['\"]?{re.escape(c)}['\"]?\s*:", js)]
    if mancanti:
        rep.err("API_PAYLOAD", f"campi obbligatori assenti dal payload JS: {mancanti} "
                               "(controllare in particolare `contest`)")
    else:
        rep.passed("API_PAYLOAD", "tutti i campi obbligatori presenti nel payload worker "
                                  f"({len(api['campi_payload_obbligatori'])} campi, incluso contest)")

    # --- Check 4: Campi payload D1 (uploadId obbligatorio) ---
    d1_campi = api.get("campi_payload_d1_obbligatori", [])
    if d1_campi:
        mancanti_d1 = [c for c in d1_campi if not re.search(
            rf"['\"]?{re.escape(c)}['\"]?\s*:", js)]
        if mancanti_d1:
            rep.err("API_PAYLOAD_D1", f"campi obbligatori assenti dal payload D1: {mancanti_d1}")
        else:
            rep.passed("API_PAYLOAD_D1", f"tutti i campi D1 presenti ({len(d1_campi)} campi, "
                       "incluso uploadId)")


# ---------------------------------------------------------------------------
# Check migrati dal vecchio validatore (validate_quiz_html_old.py)
# ---------------------------------------------------------------------------

# Anti-regalo: pattern formali che svelano la corretta per struttura
ENRICH_PATTERNS = [
    ("virgola/inciso",   re.compile(r",")),
    ("doppia lettura",   re.compile(
        r"\b(o|od|ovvero|oppure|ossia|cio[eè]|alias|anche dett[oa]"
        r"|dett[oa] anche|not[oa] come|not[oa] anche come)\b",
        re.IGNORECASE)),
    ("virgolette",       re.compile(r'["""«»]')),
    ("inciso con dash",  re.compile(r"\s[–—-]\s")),
]
LEN_RATIO_MAX = 1.5
LEN_DIFF_MAX = 15


def _enrichment_tags(text):
    return {name for name, rx in ENRICH_PATTERNS if rx.search(text)}


def _giveaway_check_single(idx, options, ans):
    """Ritorna lista di errori anti-regalo per una singola domanda."""
    problemi = []
    correct = options[ans]
    distr = [o for i, o in enumerate(options) if i != ans]

    distr_tags = set()
    for d in distr:
        distr_tags |= _enrichment_tags(d)
    for tag in _enrichment_tags(correct) - distr_tags:
        problemi.append(
            f"D{idx}: regalo formale — '{tag}' presente solo nella "
            f"risposta corretta e in nessun distrattore.")

    avg_d = sum(len(d) for d in distr) / max(len(distr), 1)
    if (len(correct) > max((len(d) for d in distr), default=0)
            and avg_d > 0
            and (len(correct) / avg_d >= LEN_RATIO_MAX
                 or len(correct) - avg_d >= LEN_DIFF_MAX)):
        problemi.append(
            f"D{idx}: regalo formale — corretta di {len(correct)} caratteri "
            f"contro media distrattori di {avg_d:.0f}.")
    return problemi


def check_questions_json(js, cfg, rep):
    """Estrae il JSON delle domande dal JS inline e valida: conteggio,
    opzioni, risposta corretta, spiegazioni, distribuzione, consecutive,
    anti-regalo, tracce audio e immagini."""
    m = re.search(r'const questions\s*=\s*(\[.*?\])\s*;', js, re.DOTALL)
    if not m:
        rep.err("QUESTIONS_JSON", "const questions non trovato nel JS — "
                "impossibile validare le domande")
        return
    try:
        questions = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        rep.err("QUESTIONS_JSON", f"questions JSON non valido: {e}")
        return

    attese = cfg.get("num_domande_attese", 45)
    if len(questions) != attese:
        rep.err("QUESTIONS_JSON", f"trovate {len(questions)} domande, attese {attese}")
    else:
        rep.passed("QUESTIONS_JSON", f"{attese} domande nel JSON")

    # Validazione opzioni e risposta corretta
    problemi_opts = []
    problemi_ans = []
    for i, q in enumerate(questions, start=1):
        opts = q.get("opts") or q.get("options") or q.get("answers") or q.get("choices")
        if not isinstance(opts, list) or len(opts) != 4:
            problemi_opts.append(i)
            continue
        if any(not str(o).strip() for o in opts):
            problemi_opts.append(i)
        ans_val = q.get("ans")
        # ans può essere int (singola) o lista (doppia risposta)
        if isinstance(ans_val, int):
            if not (0 <= ans_val <= 3):
                problemi_ans.append((i, ans_val))
        elif isinstance(ans_val, list):
            if not all(isinstance(a, int) and 0 <= a <= 3 for a in ans_val):
                problemi_ans.append((i, ans_val))
        else:
            problemi_ans.append((i, ans_val))

    if problemi_opts:
        rep.err("OPZIONI_JSON", f"domande con opzioni mancanti/vuote/non-4: {problemi_opts}")
    else:
        rep.passed("OPZIONI_JSON", "tutte le domande hanno 4 opzioni non vuote")
    # Risposte multiple (array): template corrente non le supporta
    domande_multi = [i for i, q in enumerate(questions, start=1)
                     if isinstance(q.get("ans"), list)]
    if domande_multi:
        rep.err("RISPOSTA_JSON",
                f"domande con ans array (risposte multiple): {domande_multi} — "
                "risposte multiple non supportate dal template corrente "
                "(bug processAnswer noto) — convertire a risposta singola "
                "o attendere il fix")
    elif problemi_ans:
        rep.err("RISPOSTA_JSON", f"domande con ans non valido: {problemi_ans[:10]}")
    else:
        rep.passed("RISPOSTA_JSON", "campo ans valido per tutte le domande")

    # Spiegazioni (campo expl)
    senza_expl = [i for i, q in enumerate(questions, start=1)
                  if not str(q.get("expl", "")).strip()]
    if senza_expl:
        rep.err("SPIEGAZIONI_JSON", f"domande senza campo expl (o vuoto): {senza_expl}")
    else:
        rep.passed("SPIEGAZIONI_JSON", "campo expl presente e non vuoto per tutte le domande")

    # Tracce audio: domande con campo audio devono averlo non vuoto e univoco
    tracce = {}
    problemi_audio = []
    for i, q in enumerate(questions, start=1):
        if "audio" in q:
            src = q["audio"]
            if not src or not str(src).strip():
                problemi_audio.append(f"D{i}: campo audio vuoto")
            elif src in tracce:
                problemi_audio.append(f"D{i}: traccia duplicata con D{tracce[src]}")
            else:
                tracce[src] = i
    if problemi_audio:
        for p in problemi_audio:
            rep.err("TRACCE_AUDIO_JSON", p)
    else:
        n_audio = len(tracce)
        rep.passed("TRACCE_AUDIO_JSON",
                   f"{n_audio} domande audio, tracce valide e univoche"
                   if n_audio else "nessuna domanda audio (check saltato)")

    # Immagini: domande con campo img devono averlo non vuoto e non placeholder
    placeholders = [p.lower() for p in cfg.get("media", {}).get("placeholder_vietati", [])]
    problemi_img = []
    n_img = 0
    for i, q in enumerate(questions, start=1):
        if "img" in q:
            src = q["img"]
            if not src or not str(src).strip():
                problemi_img.append(f"D{i}: campo img vuoto")
            elif any(p in str(src).lower() for p in placeholders):
                problemi_img.append(f"D{i}: placeholder residuo nel campo img")
            else:
                n_img += 1
    if problemi_img:
        for p in problemi_img:
            rep.err("IMMAGINI_JSON", p)
    else:
        rep.passed("IMMAGINI_JSON",
                   f"{n_img} domande con immagine, tutte valide"
                   if n_img else "nessuna domanda con immagine (check saltato)")

    # Distribuzione risposte (min 8 per lettera)
    ans_count = {0: 0, 1: 0, 2: 0, 3: 0}
    answers_seq = []
    for q in questions:
        a = q.get("ans")
        if isinstance(a, int) and 0 <= a <= 3:
            ans_count[a] += 1
            answers_seq.append(a)
        elif isinstance(a, list):
            # per domande a doppia risposta, conta la prima per la distribuzione
            if a and isinstance(a[0], int) and 0 <= a[0] <= 3:
                ans_count[a[0]] += 1
                answers_seq.append(a[0])

    labels = {0: "A", 1: "B", 2: "C", 3: "D"}
    errori_dist = []
    for k, v in ans_count.items():
        if v < 8:
            errori_dist.append(f"{labels[k]}={v}")
    if errori_dist:
        rep.err("DISTRIBUZIONE", f"lettere sotto il minimo di 8: {', '.join(errori_dist)} "
                f"(distribuzione: A={ans_count[0]} B={ans_count[1]} "
                f"C={ans_count[2]} D={ans_count[3]})")
    else:
        rep.passed("DISTRIBUZIONE",
                   f"A={ans_count[0]} B={ans_count[1]} C={ans_count[2]} D={ans_count[3]}")

    # Max 2 consecutive uguali
    consecutive = 1
    violazione_cons = False
    for i in range(1, len(answers_seq)):
        if answers_seq[i] == answers_seq[i - 1]:
            consecutive += 1
            if consecutive > 2:
                rep.err("CONSECUTIVE",
                        f"3+ risposte consecutive uguali ({labels[answers_seq[i]]}) "
                        f"intorno alla domanda {i + 1}")
                violazione_cons = True
                break
        else:
            consecutive = 1
    if not violazione_cons:
        rep.passed("CONSECUTIVE", "max 2 consecutive con la stessa lettera")

    # Anti-regalo: pattern formali e outlier di lunghezza
    tutti_problemi = []
    for i, q in enumerate(questions, start=1):
        opts = q.get("opts") or q.get("options") or q.get("answers") or q.get("choices")
        ans_val = q.get("ans")
        if not isinstance(opts, list) or len(opts) != 4:
            continue
        if isinstance(ans_val, int) and 0 <= ans_val <= 3:
            tutti_problemi.extend(_giveaway_check_single(i, opts, ans_val))
        elif isinstance(ans_val, list):
            for a in ans_val:
                if isinstance(a, int) and 0 <= a <= 3:
                    tutti_problemi.extend(_giveaway_check_single(i, opts, a))
    if tutti_problemi:
        for p in tutti_problemi[:10]:
            rep.warn("ANTI_REGALO", p)
        if len(tutti_problemi) > 10:
            rep.warn("ANTI_REGALO", f"... e altri {len(tutti_problemi) - 10} problemi")
    else:
        rep.passed("ANTI_REGALO", "nessun pattern strutturale regalo rilevato")


def check_cat_backgrounds(js, rep):
    """Verifica che catBackgrounds sia un JSON valido (check migrato dal vecchio)."""
    m = re.search(r'const catBackgrounds\s*=\s*(\{.*?\})\s*;', js, re.DOTALL)
    if not m:
        rep.warn("CAT_BACKGROUNDS", "catBackgrounds non trovato nel JS")
        return
    try:
        bg = json.loads(m.group(1))
        rep.passed("CAT_BACKGROUNDS", f"catBackgrounds valido ({len(bg)} categorie)")
    except json.JSONDecodeError as e:
        rep.err("CAT_BACKGROUNDS", f"catBackgrounds JSON non valido: {e}")


# ---------------------------------------------------------------------------

def check_js_sintassi(js, cfg, rep):
    if not cfg["js"]["node_syntax_check"]:
        return
    node = shutil.which("node")
    if not node:
        rep.warn("JS_SINTASSI", "node non trovato nel PATH: syntax check saltato")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as f:
        f.write(js)
        tmp = f.name
    try:
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            rep.passed("JS_SINTASSI", "JS sintatticamente valido (node --check)")
        else:
            rep.err("JS_SINTASSI", f"errore di sintassi JS: {r.stderr.strip().splitlines()[-1] if r.stderr else 'sconosciuto'}")
    except Exception as e:
        rep.warn("JS_SINTASSI", f"check non eseguibile: {e}")
    finally:
        Path(tmp).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Validatore statico puntate Quizzone")
    ap.add_argument("html", help="Path del file HTML della puntata")
    ap.add_argument("--config", default=None,
                    help="Path del config JSON (default: quizzone_validator_config.json "
                         "accanto a questo script)")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"ERRORE: file non trovato: {html_path}")
        sys.exit(2)

    cfg_path = Path(args.config) if args.config else \
        Path(__file__).parent / "quizzone_validator_config.json"
    if not cfg_path.exists():
        print(f"ERRORE: config non trovato: {cfg_path}")
        sys.exit(2)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    raw = html_path.read_bytes()
    testo = raw.decode("utf-8", errors="replace")
    soup = BeautifulSoup(testo, "html.parser")
    js = estrai_js(soup, html_path)

    rep = Report()
    print(f"\nValidazione: {html_path.name}\n")

    check_encoding(raw, testo, rep)
    domande = check_domande(soup, cfg, rep)
    check_risposte(domande, cfg, rep)
    check_spiegazioni(domande, cfg, rep)
    check_id_univoci(soup, rep)
    check_bottone(soup, js, cfg, rep, "tasto_inizia", "TASTO_INIZIA")
    check_bottone(soup, js, cfg, rep, "tasto_invio_risultati", "TASTO_INVIO")
    check_id_referenziati(soup, js, rep)
    check_bgm(soup, js, html_path, cfg, rep)
    check_tracce_audio(domande, html_path, cfg, rep)
    check_immagini(soup, html_path, cfg, rep)
    check_api(js, testo, cfg, rep)
    check_questions_json(js, cfg, rep)
    check_cat_backgrounds(js, rep)
    check_js_sintassi(js, cfg, rep)

    rep.stampa()
    sys.exit(0 if not rep.errori else 1)


if __name__ == "__main__":
    main()
