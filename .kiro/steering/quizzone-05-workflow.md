# Quizzone — Workflow generazione puntata (macchina a stati)

Questo file definisce il processo OBBLIGATORIO per generare una puntata.
Le fasi si eseguono in ordine, ognuna ha una condizione di uscita verificabile.
Non si salta una fase, non se ne ripete una già chiusa.

REGOLA DI PROPRIETÀ: questo workflow governa la generazione FINO alla
scrittura del file .md. Tutto ciò che accade DOPO la scrittura (validazione
script, dedup, correzioni, verifica fatti) è di proprietà ESCLUSIVA dell'hook
"Validazione unica post-creazione quiz". Non anticipare né duplicare quei
controlli qui: la ridondanza è la causa dei loop, non la cura.

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
   (45 domande, vincoli da quizzone-01/02).
2. Componi la griglia: 18 categorie con i vincoli di distribuzione
   (min 2 per categoria, max 3; max 2 Matematica, max 2 Scienze).
3. Per ogni slot scegli un TEMA (non ancora la domanda) e verifica a mente
   che la risposta prevista non sia nella blacklist. Se lo è, cambia tema
   ORA: costa zero adesso, costa un ciclo di correzione dopo.
4. Pianifica la distribuzione delle lettere corrette (min 8 per lettera,
   max 2 consecutive uguali) PRIMA di scrivere le domande.

USCITA: griglia completa di 45 temi con lettera target. Mostrala all'utente
in forma compatta (categoria → tema, una riga per manche) e prosegui senza
attendere approvazione, salvo che l'utente abbia chiesto di rivedere i temi.

## FASE 2 — Generazione e scrittura (UN solo write)

1. Scrivi le 45 domande complete IN MEMORIA seguendo la griglia della Fase 1.
2. Per fatti contestabili, recenti o post-2023: verifica web DURANTE la
   stesura e annota gli URL nella sezione `## Fonti`. (Questa è l'unica
   verifica fatti che fai tu: il controllo di completezza delle fonti a
   valle spetta all'hook.)
3. Scrivi il file `puntate/quiz_puntataN_*.md` con UNA SOLA operazione di
   scrittura, completo di tutte le sezioni. Mai scrivere il file parziale
   e completarlo dopo: la creazione del file è l'evento che arma il gate
   di validazione, e deve trovare il contenuto integrale.

USCITA: file .md scritto una volta. Da questo momento sei sotto la
giurisdizione dell'hook di validazione: segui le sue istruzioni e SOLO quelle.

## FASE 3 — Post-validazione (di proprietà dell'hook)

Eseguita automaticamente dall'hook "Validazione unica post-creazione quiz":
script, eventuali sostituzioni chirurgiche, max 3 cicli, check semantico
unico, riepilogo all'utente. Questo workflow non aggiunge nulla qui.

USCITA: riepilogo presentato. ATTESA: approvazione esplicita del .md
da parte dell'utente. Non proporre l'HTML prima dell'approvazione.

## FASE 4 — Build HTML (solo dopo approvazione esplicita)

1. L'hook pre-write verifica approvazione e checklist tecnica. Componi
   l'HTML completo in memoria e scrivilo in un'unica operazione.
2. Dopo la scrittura dell'HTML non si rientra in validazione del .md:
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
  ciò che la precede.
