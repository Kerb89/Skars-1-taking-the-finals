---
inclusion: always
---

# Quizzone — Errori di build noti (checklist)

Questo file traccia gli errori fatti durante la generazione HTML, per evitarli in futuro.

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

## Checklist pre-build

Prima di eseguire `build_puntataX.ps1`:

1. [ ] Chiavi JS tutte in ASCII (no accenti, no apostrofi)
2. [ ] Ordine file: top → questions (con `];`) → backgrounds → bottom
3. [ ] Nessun doppio apice `""` nelle chiavi dopo i replace
4. [ ] Ogni categoria ha la sua immagine (non riusare da altre)
5. [ ] Distribuzione risposte: max 2 consecutive stessa lettera, min 6 per lettera su 35
6. [ ] Anagrammi: distrattori verificati NON essere anagrammi validi
7. [ ] Testi brano: verificati parola per parola
8. [ ] Test nel browser: "Inizia il quiz" funziona, tutte le categorie mostrano sfondo
