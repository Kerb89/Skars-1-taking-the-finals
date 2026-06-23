---
inclusion: always
---

# Quizzone — Formato domande

## Struttura
- 30 domande numerate da 1 a 30.
- 4 opzioni per domanda, etichette `A)` `B)` `C)` `D)`.
- **Una sola risposta corretta** come regola.
- **Due risposte corrette: ammesse ma rare** — circa una domanda a doppia risposta ogni 2-3 quiz. Non è obbligatorio che il testo della domanda lo dica esplicitamente, fa parte della difficoltà. Entrambe le risposte devono essere inequivocabilmente corrette e verificabili.
- Mai 3 o più corrette.

## Categorie standard (modalità mista)
Geografia · Tecnologia · Scienze · Sport · Storia · Cibo e benessere · Attualità · Matematica · Musica · Cinema · Letteratura · Arte · Lingua italiana · Lingue straniere · Inglese · Anagrammi · Di tutto un po'.

"Di tutto un po'" è una categoria jolly, simile a quella del Trivial Pursuit: domande di cultura generale che non rientrano nettamente in nessuna delle altre categorie, oppure che ne attraversano più d'una.

Distribuzione equilibrata: circa 2 domande per categoria (30), evita di mettere più domande della stessa categoria di fila.

## Difficoltà
Mix indicativo: ~20% medie, ~30% difficili, ~50% molto difficili. Il quiz deve essere una sfida vera: evita domande banali o troppo scontate. Anche le domande "facili" devono richiedere un minimo di conoscenza specifica — niente roba che chiunque saprebbe senza pensarci. Niente domande che dipendono da un unico dettaglio oscuro e non verificabile, ma il livello generale deve restare alto.

## Qualità dei distrattori
- Le 3 opzioni sbagliate devono essere plausibili, stesso registro e lunghezza simile alla corretta.
- Niente opzioni-scherzo; niente "tutte le precedenti" / "nessuna delle precedenti" usate come riempitivo.
- La risposta corretta non deve essere sistematicamente la più lunga o l'unica "tecnica".
- Distribuisci la posizione della corretta in modo casuale tra A, B, C e D. Non seguire schemi o sequenze prevedibili, e assicurati che tutte e 4 le lettere vengano usate come corretta nel corso del quiz. La distribuzione non deve essere necessariamente omogenea: va benissimo se una lettera compare 6 volte e un'altra 11, purché il posizionamento sia genuinamente casuale e non segua pattern riconoscibili. Il minimo accettabile per qualsiasi lettera è 6 su 35 domande — nessuna lettera deve scendere sotto questo valore.

## Stile di scrittura
- **Mai parentesi** per descrizioni, nomi alternativi o traduzioni. Se serve un'informazione aggiuntiva, integrala nella frase o usa un inciso con virgole. Esempio: NO "Prosopopea (personificazione)" → SÌ "Prosopopea, detta anche personificazione".
- **Niente chiarimenti tra parentesi nemmeno nelle opzioni di risposta** — né nella corretta né nelle errate. Se un'opzione ha bisogno di contesto, riformulala come frase completa. Esempio: NO "Yangtze (Fiume Azzurro)" → SÌ "Fiume Azzurro, detto anche Yangtze".
- **Uniformità strutturale delle opzioni:** se la risposta corretta contiene una precisazione, un formato o una struttura particolare, tutte e 4 le opzioni devono seguire lo stesso formato. Se una risposta è "Al confine tra X e Y", anche le altre devono essere "Al confine tra W e Z". Se una risposta include un inciso con virgola, tutte devono includerlo. La risposta corretta non deve mai distinguersi dalle altre per struttura o livello di dettaglio.

## Note per categoria
- **Matematica:** risolvibili a mente o con calcolo semplice; notazione non ambigua. Varia i tipi: sommatorie con formula di Gauss, operazioni combinate tipo x+y−z×w, continua la sequenza numerica, radici quadrate/cubiche, potenze, percentuali. Non fare solo un tipo — alterna tra questi formati.
- **Inglese:** domanda in italiano; formati principali: completamento con il verbo/parola corretta, traduzione di una frase breve dall'italiano all'inglese o viceversa, scelta della traduzione/completamento corretto tra le 4 opzioni. Le opzioni possono essere in inglese.
- **Lingue straniere:** ruota tra francese, tedesco, spagnolo, portoghese e altre se chiesto. Il testo della domanda è in italiano, tranne la parola o espressione straniera di cui si chiede il significato. Indica sempre quale lingua è.
- **Lingua italiana:** grammatica, ortografia, etimologia, uso corretto.
- **Anagrammi:** si fornisce una parola o un nome e si chiede quale tra le 4 opzioni ne è l'anagramma. Verificare gli anagrammi usando https://www.dizy.com/it/anagrammi/ o il motore anagrammatico di Gaunt. Le parole devono essere comuni e riconoscibili, non termini oscuri. Possono anche essere nomi di celebrità, ma variare: non solo nomi propri, anche parole comuni.
- **Sport:** varia tra discipline diverse (tennis, basket, atletica, ciclismo, nuoto, rugby, F1, sci, boxe, ecc.) — non solo calcio. Alterna tra eventi recenti e storia dello sport (Olimpiadi passate, record storici, leggende).
- **Attualità · Sport (record) · Scienze (dati) · Geografia (capitali, popolazioni, classifiche) · Storia (date):** fatti che cambiano o si contestano → verifica obbligatoria (vedi `quizzone-02-fonti`).
- **In generale:** bilancia domande su fatti recenti con domande su fatti storici o consolidati. Obiettivo indicativo: circa il 30% delle domande può riguardare gli ultimi 10 anni, il restante 70% attinge a fatti storici, classici o consolidati. Non concentrarti solo sull'attualità recentissima.

## Formato di output (Markdown)

Intestazione:

```
# Quizzone — <tema o "Misto"> — <data>
```

Poi le 30 domande, ognuna così:

```
**1.** <testo della domanda>
A) ...
B) ...
C) ...
D) ...
```

In fondo, sezione soluzioni separata e ben staccata (il file serve sia da quiz sia da correttore):

```
---
## Soluzioni
1. C
2. A e D    ← se la domanda è a 2 corrette
...
```

Dove utile, aggiungi dopo ogni soluzione una riga di spiegazione brevissima (1 frase).

Non ripetere domande identiche nella stessa sessione; varia le formulazioni.

## Storico e ripetizioni
- **REGOLA FONDAMENTALE:** dopo aver generato o modificato un quiz, aggiornare SEMPRE `quiz_history.md` con il riassunto delle domande. Mai lasciare una puntata fuori dallo storico.
- Prima di generare un nuovo quiz, leggi SEMPRE i file `.md` dei quiz precedenti nella cartella di lavoro e il file `quiz_history.md` per evitare domande identiche o troppo simili (stesso argomento + stessa angolazione).
- **Fonti di backup se manca il `.md`:** se una puntata precedente non ha il file `.md` in `quiz_md/`, controlla:
  1. I file `.html` in `vecchie_puntate/` — il JSON delle domande è nel tag `<script>`.
  2. I file `quiz_stats_<nome>.md` dei giocatori — contengono le domande sbagliate/corrette con il testo.
  3. Il file `quiz_history.md` — contiene un riassunto breve di ogni domanda per puntata.
  Usali come fonti per ricostruire le domande già usate e evitare duplicati.
- Riproporre lo stesso *argomento* è ammesso se la domanda è formulata da un'angolazione diversa (es. la prima volta si chiedeva "chi ha dipinto X", la seconda "in che anno fu dipinto X"). Ma se argomento E angolazione coincidono, è un doppione e va scartato.
- Le statistiche giocatori (`quiz_stats.md`) servono per riproporre argomenti sbagliati, ma con formulazione diversa. Ignorarle finché non ci sono almeno 10 quiz nel sistema.
