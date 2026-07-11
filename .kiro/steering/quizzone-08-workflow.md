---
inclusion: always
---

# Quizzone — Workflow generazione puntata (macchina a stati)

Questo file definisce il processo OBBLIGATORIO per generare una puntata.
Le fasi si eseguono in ordine, ognuna ha una condizione di uscita verificabile.
Non si salta una fase, non se ne ripete una già chiusa.

REGOLA DI PROPRIETÀ: questo workflow governa la generazione FINO alla
scrittura del file .md. Tutto ciò che accade DOPO la scrittura (validazione
script, dedup, correzioni, verifica di completezza) è di proprietà ESCLUSIVA
dell'hook "Validazione unica post-creazione quiz". Non anticipare né duplicare
quei controlli qui: la ridondanza è la causa dei loop, non la cura.

---

## FASE 0 — Setup (nessuna generazione)

1. Esegui `python quiz_dedup.py index`.
2. Leggi `puntate/answers_index.txt` UNA volta con il tool.
3. Ogni voce dell'indice è una RISPOSTA CORRETTA VIETATA. Un argomento già
   usato è riutilizzabile solo con angolazione radicalmente diversa E
   risposta corretta diversa.
4. NON leggere i file quiz_history*.md per intero. L'indice li sostituisce.

USCITA: blacklist in contesto. Nessun file scritto.

## FASE 1 — Piano puntata (in chat, niente file)

1. Determina numero puntata (dal file più recente in puntate/) e formato
   (45 domande, vincoli da quizzone-01).
2. Componi la griglia: 18 categorie con i vincoli di distribuzione
   (min 2 per categoria, max 3; max 2 Matematica, max 2 Scienze; rotazione
   immagini e discipline sportive secondo quizzone-01).
3. Per ogni slot scegli un TEMA (non ancora la domanda) e verifica a mente
   che la risposta prevista non sia nella blacklist. Se lo è, cambia tema
   ORA: costa zero adesso, costa un ciclo di correzione dopo.
4. Pianifica la distribuzione delle lettere corrette (min 8 per lettera,
   max 2 consecutive uguali) PRIMA di scrivere le domande.

USCITA: griglia completa di 45 temi con lettera target. Mostrala all'utente
in forma compatta (categoria → tema, una riga per manche) e prosegui senza
attendere approvazione, salvo che l'utente abbia chiesto di rivedere i temi.

## FASE 2 — Generazione e scrittura (UN solo write)

1. Scrivi le 45 domande complete IN MEMORIA seguendo la griglia della Fase 1
   e le regole di stile di quizzone-01.
2. Verifica le risposte DURANTE la stesura secondo quizzone-02-fonti, che
   comanda su questo punto: double check su TUTTE le domande (almeno 1 fonte
   autorevole ciascuna; 2-3 fonti indipendenti per fatti contestabili,
   volatili o post-2023), URL annotati man mano nella sezione `## Fonti`.
   Fonti in conflitto = domanda scartata e sostituita, come da quizzone-02.

   **Delega ai fact-checker (parallela, 3-4 subagent):**
   Dopo aver scritto le 45 domande in memoria, dividi in 3-4 blocchi di
   11-12 domande ciascuno. Per ogni blocco invoca il subagent custom
   `fact-checker` (definito in `.kiro/agents/fact-checker.md` — ha accesso
   solo a web_search e web_fetch, non può scrivere file). Invoca i 3-4
   subagent IN PARALLELO (stessa chiamata). Integra i verdetti: sostituisci
   le domande bocciate (SMENTITA, CONFLITTO, NON VERIFICABILE) prima della
   passata anti-giveaway. Annota gli URL confermati nella sezione `## Fonti`.

   Per le domande di tipo anagramma: invoca il subagent custom
   `anagram-verifier` (definito in `.kiro/agents/anagram-verifier.md` — ha
   accesso solo a web_fetch). Passa tutte le domande anagramma in un'unica
   chiamata. Se un anagramma è FAIL, sostituisci prima di procedere.
3. **PASSATA ANTI-GIVEAWAY (obbligatoria, dopo stesura, prima di scrivere
   il file).** Scorri tutte le 45 domande una per una ed emetti in chat una
   tabella con esattamente 45 righe nel formato:

   | # | Termine sospetto | Verdetto | Azione |
   |---|------------------|----------|--------|

   Per ogni domanda:
   - Estrai ogni nome proprio / termine tecnico presente nel testo della
     domanda. Scrivilo nella colonna "Termine sospetto" SEMPRE — anche se
     il verdetto è PASS. Se non c'è nessun nome proprio, scrivi "nessun
     nome proprio". La colonna non può mai essere vuota: compilarla forza
     la scansione effettiva; il verdetto da solo no.
   - Confrontalo con la risposta corretta: match esatto, match radice,
     match traslitterazione → FAIL. Nessun match → PASS.
   - Valuta anche la deducibilità logica: "qualcuno che NON sa la risposta
     potrebbe indovinarla solo dagli indizi nel testo?" → FAIL.
   - Se FAIL: indica nella colonna "Azione" la riformulazione o la
     sostituzione. Applica la correzione IN MEMORIA prima di procedere.
   - Se PASS: colonna "Azione" = "—".

   La tabella va emessa in chat. Non è opzionale. Se una domanda è FAIL e
   non viene corretta, il file NON si scrive.

4. Scrivi il file `puntate/quiz_puntataN_*.md` con UNA SOLA operazione di
   scrittura, completo di tutte le sezioni (domande, soluzioni, fonti).
   Mai scrivere il file parziale e completarlo dopo: la creazione del file
   è l'evento che arma il gate di validazione, e deve trovare il contenuto
   integrale.

USCITA: file .md scritto una volta. Da questo momento sei sotto la
giurisdizione dell'hook di validazione: segui le sue istruzioni e SOLO quelle.

## FASE 3 — Post-validazione (di proprietà dell'hook)

Eseguita automaticamente dall'hook "Validazione unica post-creazione quiz":
script, eventuali sostituzioni chirurgiche, max 3 cicli, check semantico
unico, riepilogo all'utente. Questo workflow non aggiunge nulla qui.

USCITA: riepilogo presentato. ATTESA: approvazione esplicita del .md
da parte dell'utente. Non proporre l'HTML prima dell'approvazione.

## FASE 4 — Build HTML (solo dopo approvazione esplicita)

1. Segui quizzone-03-html: template come base, placeholder sostituiti,
   immagini di categoria ruotate rispetto alla puntata precedente.
2. La checklist tecnica pre-build vive nell'hook "Blocca HTML quiz senza
   approvazione". Se l'HTML viene scritto direttamente dall'agent, l'hook
   scatta da solo; se viene prodotto da uno script di build lanciato da
   shell, esegui la checklist dell'hook PRIMA di lanciare lo script,
   perché in quel caso il gate pre-write non scatta.
3. Dopo la consegna dell'HTML non si rientra in validazione del .md:
   quel gate è chiuso.

USCITA: HTML consegnato.

## FASE 5 — Chiusura (di proprietà dell'hook agentStop)

L'aggiornamento dello storico e la rigenerazione dell'indice avvengono
tramite l'hook "Aggiorna storico a fine puntata". Non farlo manualmente
a metà workflow.

---

## Regole trasversali

- Una fase chiusa non si riapre. Se l'utente chiede una modifica a puntata
  consegnata, è un EDIT puntuale: si tocca solo ciò che ha chiesto, si
  esegue `python quiz_dedup.py check <file>` una volta a fine edit, stop.
- Se uno script fallisce (file non trovato, errore Python), fermati e
  riporta l'errore all'utente. Non aggirare lo script con controlli manuali.
- In caso di conflitto tra questo workflow e un hook, vince l'hook per
  tutto ciò che segue la scrittura del file; vince il workflow per tutto
  ciò che la precede. In caso di conflitto su regole di verifica fonti,
  vince quizzone-02-fonti.
- **Mai editare file `.kiro/hooks/*.kiro.hook` senza approvazione esplicita
  dell'utente.** I hook sono il layer di enforcement — modificarli è
  equivalente a disabilitare un vincolo. Se un hook blocca un'operazione
  legittima, riporta il problema all'utente e chiedi come procedere.
  Non "sistemare" il gate per aggirare il blocco.
- **I subagent NON scrivono file gated.** I file `quiz_puntata*.md` e
  `quiz_puntata*.html` vanno scritti SOLO dal main agent, mai da un
  subagent. Motivo: gli hook `preToolUse` non scattano nei subagent —
  delegare la scrittura bypassa silenziosamente tutti i gate (anti-giveaway,
  validazione post-creazione, blocco HTML). Subagent = ricerca, verifica,
  elaborazione media, report compatti. Scritture gated = main agent.
