---
inclusion: always
---

# Quizzone — Errori di build noti (registro storico)

Questo file traccia gli errori fatti durante la generazione HTML, con contesto e soluzione, per evitarli in futuro. È un REGISTRO: la checklist operativa pre-build vive in un solo posto, l'hook "Blocca HTML quiz senza approvazione" (`.kiro/hooks/quiz-blocca-html-senza-approvazione.kiro.hook`). Non duplicarla qui né altrove: due copie della stessa checklist divergono sempre.

Per i vincoli di distribuzione delle risposte fa fede `quizzone-01-domande` §Qualità dei distrattori (min 8 per lettera su 45, max 2 consecutive con la stessa lettera).

## Errori risolti

### 1. Encoding "Attualità" — mismatch chiavi JS
- **Problema:** La chiave `"Attualit\u00e0"` nel dizionario `catBackgrounds` non matchava con la stessa chiave nelle domande perché PowerShell generava un encoding diverso (`Attualitu00e0` letterale vs `\u00e0` escape).
- **Soluzione adottata:** Usare chiavi ASCII pure per il backend JS (`attualita`, `cibo`, `dituttounpo`, `lingua_italiana`) e una mappa `catLabels` per il display frontend.
- **Regola:** MAI usare caratteri accentati o apostrofi nelle chiavi degli oggetti JS. Usare sempre chiavi ASCII semplici.

### 2. Ordine inserimento file nel build — quizData rotto
- **Problema:** Lo script di build inseriva `catBackgrounds` nel mezzo dell'array `quizData`, rompendo la sintassi JS.
- **Soluzione:** L'ordine corretto è: `top.html` (apre `const quizData = [`) → `questions.js` (items + `];`) → `backgrounds.js` (`const catBackgrounds = {...}`) → `bottom.html` (logica).
- **Regola:** Verificare sempre l'ordine: `quizData` prima, chiuso con `];`, poi tutto il resto.

### 3. Doppio apice nella chiave "dituttounpo"
- **Problema:** Il replace di `"Di tutto un po'"` (con apostrofo) in `"dituttounpo"` lasciava un `"` residuo: `"dituttounpo""`. Il doppio apice rompeva il parsing JS.
- **Soluzione:** Dopo ogni replace batch, verificare che non ci siano `""` o caratteri residui nelle chiavi.
- **Regola:** Dopo replace massivi, fare un check con regex su tutte le chiavi del dizionario.

### 4. Immagine sbagliata per "Lingua italiana"
- **Problema:** Usata l'immagine `inglese.jpg` (Londra!) come fallback per "Lingua italiana".
- **Soluzione:** Creata cartella dedicata `lingua_italiana/` con immagini appropriate (penna, calligrafia, pagine libro).
- **Regola:** Ogni categoria DEVE avere la sua immagine dedicata. Mai riusare immagini di altre categorie.

### 5. Distribuzione risposte corrette — troppi B di fila
- **Problema:** Nella prima bozza, le domande 30-34 avevano tutte risposta B — pattern evidente.
- **Soluzione:** Ridistribuire manualmente le posizioni della corretta.
- **Regola:** Vedi `quizzone-01-domande` §Qualità dei distrattori.

### 6. Anagrammi con più soluzioni valide
- **Problema:** PANTERA ha 4 anagrammi validi (PATERNA, RAPANTE, PARANTE, PRENATA). Usarne uno come distrattore crea 2 risposte corrette.
- **Soluzione:** Verificare su dizy.com TUTTI gli anagrammi della parola.
- **Regola:** Vedi `quizzone-01-domande` §Anagrammi.

### 7. Distrattori con numero lettere diverso
- **Problema:** "PARLANTE" (8 lettere) come distrattore di "PANTERA" (7 lettere) — troppo facile da scartare.
- **Soluzione:** Tutti i distrattori devono avere lo stesso numero di lettere della parola originale.
- **Regola:** Vedi `quizzone-01-domande` §Anagrammi.

### 8. Testo brano — articolo aggiunto
- **Problema:** Il testo originale è "Come pini di Roma" ma l'opzione diceva "Come **i** pini di Roma" — sbagliato per un quiz che chiede la frase ESATTA.
- **Soluzione:** Verificare il testo parola per parola dalla fonte.
- **Regola:** Per domande "testo esatto", copiare LETTERALMENTE dalla fonte, zero modifiche.

---

## Nota sul build

Se l'HTML viene generato tramite script (`build_puntataX.ps1`) invece che scritto direttamente dall'agent, la checklist dell'hook va eseguita PRIMA di lanciare lo script, perché l'hook pre-write scatta solo sulle scritture dirette dell'agent, non sui file prodotti da comandi shell.

## Verifica coerenza media pre-build

Prima di inserire media inline nell'HTML, verificare la coerenza tra il
contenuto del media e il claim della domanda:

### Immagini (campo `img`)
Per ogni domanda con immagine, l'agent identifica alla cieca il soggetto
dai pixel (descrizione visiva) e lo confronta con la risposta corretta.
Se l'immagine non corrisponde al claim (es. il base64 è di un Monet ma
la risposta dice Vermeer), la domanda va bloccata e segnalata all'utente.

### Audio (campo `audio`)
I modelli non possono ascoltare gli MP3. Il check è deterministico:
1. Eseguire `python scripts/check_audio_id3.py --check <file.mp3> <titolo> [artista]`
2. Se i tag ID3 sono presenti e matchano → OK.
3. Se i tag sono assenti (NO_TAGS) o in conflitto (MISMATCH) → flag
   all'utente per verifica manuale (play + confronto a orecchio).
L'accoppiamento sostanziale audio-domanda resta un check umano: 30 secondi
a puntata, premendo play sui 3 spezzoni. Non automatizzabile oltre i tag.
