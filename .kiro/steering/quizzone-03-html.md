---
inclusion: always
---

# Quizzone — Generazione HTML

## Quando si attiva
Solo dopo approvazione esplicita del file `.md` da parte dell'utente.

## Requisiti
- L'HTML deve contenere **esattamente** le stesse 45 domande e risposte del file `.md` approvato, senza modifiche, aggiunte o rimozioni.
- Il file HTML è autonomo (single-file): tutto il CSS e il JS necessari sono inline.
- Nome file: stesso del `.md` ma con estensione `.html`.

## Template di base
Il file #[[file:template/quiz_template.html]] contiene l'HTML/CSS/JS completo e va usato come **base** per ogni nuova puntata. Non riscrivere il codice da zero: copiare il template e sostituire i placeholder. Miglioramenti incrementali (stile, UX) possono essere applicati sopra il template.

### Placeholder da sostituire

| Placeholder | Esempio |
|---|---|
| `{{PUNTATA_TITLE}}` | `Puntata 7 — Misto` |
| `{{SUBTITLE}}` | `Misto — 45 domande — 20s timer` |
| `{{FILENAME}}` | `quiz_puntata7_misto` |
| `{{QUESTIONS_JSON}}` | Array JSON delle domande |
| `{{CATEGORY_BACKGROUNDS_JSON}}` | Oggetto JSON con base64 per categoria |

### Formato domande (JSON)

```json
[
  {
    "q": "Testo della domanda",
    "opts": ["Opzione A", "Opzione B", "Opzione C", "Opzione D"],
    "ans": 2,
    "cat": "geografia",
    "audio": "data:audio/mp3;base64,... (opzionale, solo per domande musicali con audio)",
    "img": "data:image/jpeg;base64,... (opzionale, per domande con immagine es. arte)"
  }
]
```

- `ans`: indice 0-3 della risposta corretta
- `cat`: chiave categoria (vedi lista sotto)
- `audio`: (opzionale) stringa base64 dello spezzone MP3 — timer diventa 30s
- `img`: (opzionale) immagine base64 mostrata sopra le opzioni (quadri, mappe, ecc.)

### Formato sfondi categoria (JSON)

```json
{
  "geografia": "data:image/jpeg;base64,/9j/4AAQ...",
  "sport": "data:image/jpeg;base64,/9j/4AAQ...",
  "musica": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

Ogni puntata usa un'immagine diversa per ogni categoria, scelta dalla cartella `category_backgrounds/<categoria>/`.

### Immagini disponibili per categoria

| Categoria | Opzioni |
|---|---|
| anagrammi | alfabeto.jpg, scrabble.jpg |
| arte | galleria.jpg, museo.jpg, pennelli.jpg |
| attualita | giornali.jpg, notizie_2.jpg |
| cibo | frutta.jpg, piatto.jpg, spezie.jpg |
| cinema | ciak.jpg, pellicola.jpg, sala_cinema.jpg |
| dituttounpo | question_neon_1.jpg, question_neon_4.jpg |
| geografia | globo.jpg, mappa_antica.jpg, statua_greca.jpg, terra_spazio.jpg |
| inglese | big_ben.jpg, double_decker_2.jpg, tower_bridge.jpg |
| letteratura | biblioteca.jpg, libreria.jpg, libro_aperto.jpg |
| lingua_italiana | calligrafia.jpg, pagine_libro.jpg, penna_scrittura.jpg |
| lingue | bandiere_1.jpg, bandiere_2.jpg, bandiere_3.jpg |
| matematica | equazioni.jpg, formule.jpg, lavagna.jpg |
| musica | chitarra.jpg, concerto.jpg, vinile.jpg |
| scienze | dna.jpg, microscopio.jpg, provette.jpg |
| sport | calcio.jpg, ciclismo.jpg, corsa.jpg |
| storia | colosseo.jpg, piramidi.jpg, taj_mahal.jpg |
| tecnologia | circuiti.jpg, codice.jpg, laptop_luci.jpg |

### Categorie disponibili (chiavi)
geografia, tecnologia, scienze, sport, storia, cibo, attualita, matematica, musica, cinema, letteratura, arte, inglese, lingue, anagrammi, dituttounpo, lingua_italiana

### Workflow per generare una puntata
1. Generare il quiz .md (domande + soluzioni)
2. Dopo approvazione, convertire le domande in JSON
3. Scegliere un'immagine per ogni categoria (ruotare rispetto alla puntata precedente)
4. Convertire le immagini scelte in base64
5. Sostituire i placeholder nel template
6. Salvare come `quiz_puntataN_tema.html`

## Funzionalità richieste
1. **Visualizzazione domanda singola** — una domanda alla volta, con navigazione avanti/indietro.
2. **Timer di risposta** — countdown visivo di 20 secondi per ogni domanda. Se il tempo scade senza conferma, la risposta conta come sbagliata e si passa alla prossima.
3. **Selezione risposta** — click su un'opzione la evidenzia come selezionata.
4. **Conferma e feedback** — dopo la conferma, mostra se la risposta è corretta (verde) o sbagliata (rosso), con la corretta evidenziata.
5. **Sistema a punti** — basato su correttezza e velocità:
   - Risposta corretta: da +300 (risposta immediata) a +100 (al limite del tempo). Scala lineare: punti = 300 - (tempo_impiegato / 20 × 200), minimo +100.
   - Risposta sbagliata o tempo scaduto: penalità dinamica basata sul punteggio attuale. Più punti hai, più perdi; se sei in negativo, la penalità è minima ma mai zero. Formula: penalità = -25 se punteggio < 0; -75 se punteggio tra 0 e 1000; -150 se punteggio tra 1001 e 3000; -300 se punteggio > 3000. La penalità non è mai zero.
   - Il punteggio totale è visualizzato in tempo reale.
6. **Contesta domanda** — su ogni domanda, dopo aver risposto, un pulsante "Contesta domanda" apre un campo di testo in cui il giocatore può scrivere un commento/contestazione. La contestazione viene salvata e mostrata nel riepilogo finale.
7. **Riepilogo finale** — schermata con:
   - Punteggio totale a punti e risposte corrette su 45.
   - Lista completa delle risposte date vs. corrette, con tempo di risposta per ciascuna.
   - Tempo medio di risposta.
   - Eventuali contestazioni inserite durante il quiz.
   - Statistiche: percentuale corrette, tempo medio per domanda.
8. **Condivisione risultati** — pulsante "Condividi risultati" nel riepilogo che genera un testo formattato (con punteggio, errori, contestazioni, tempi medi) copiabile negli appunti o condivisibile via Web Share API (se disponibile nel browser).
   - All'inizio del quiz, prima delle domande, mostrare un campo "Nome giocatore" obbligatorio. Il nome inserito viene poi riportato nel testo di condivisione e nel file di esportazione. Il quiz non parte finché il nome non è compilato.
9. **Responsive** — funziona su mobile e desktop.
10. **Nessuna dipendenza esterna** — no CDN, no librerie esterne, tutto inline.

## Domande musicali con audio inline
Quando il quiz contiene domande musicali:
- L'audio è uno spezzone di 10-15 secondi codificato in base64, inserito inline nel tag `<audio>`.
- Il player mostra solo un pulsante ▶ e una barra di progresso, senza mostrare titolo o metadati.
- Il **timer per le domande musicali è di 30 secondi** e **parte solo quando il giocatore preme play**, non quando appare la domanda.
- Il calcolo dei punti per le domande musicali usa 30 come divisore nella formula: punti = 300 - (tempo_impiegato / 30 × 200).
- Categorie musicali previste: Musica italiana, Musica straniera, Hits.
- Le domande musicali possono essere di due tipi:
  - **Con audio:** "Chi canta questa canzone?" o "Qual è il titolo di questa canzone?" — il giocatore ascolta lo spezzone e risponde.
  - **Senza audio (testo del brano):** "Quale di queste frasi è presente ESATTAMENTE nel testo della canzone [titolo]?" — si dà il titolo e 4 opzioni di frasi, una sola è nel testo. Non richiede audio.
- Obiettivo: 3 domande con audio + 1 domanda testo brano = 4 domande musicali per quiz.
- Le domande musicali possono chiedere "Chi canta questa canzone?" OPPURE "Qual è il titolo di questa canzone?" — variare tra i due formati nei vari quiz. Scegliere il formato che rende la domanda più sfidante (se l'artista è più riconoscibile della canzone, chiedere il titolo e viceversa).
- L'utente fornisce gli spezzoni audio già tagliati; l'agente li converte e li inserisce nel template.

## Domande indovinelli
- Il **timer per le domande indovinelli è di 30 secondi** (richiedono più ragionamento).
- Il calcolo dei punti per gli indovinelli usa 30 come divisore nella formula: punti = 300 - (tempo_impiegato / 30 × 200).
- 1-2 indovinelli per quiz, pescati dal file `puntate/categoria_indovinelli.md`.

## Stile visivo
- Font sans-serif, leggibile.
- Sfondo pagina scuro, blu notte o nero morbido — meno affaticante per gli occhi.
- **Flusso a due step per ogni domanda:**
  1. **Schermata "intro"** — immagine di sfondo della categoria (da `category_backgrounds/`) con overlay scuro semi-trasparente, nome categoria + testo della domanda centrati. Click o tap per procedere. Il timer NON parte qui.
  2. **Schermata "risposta"** — testo della domanda in alto, sotto le 4 opzioni. Il timer parte qui.
- **Box risposte colorati per categoria** — i box delle opzioni usano un colore di sfondo coordinato con l'immagine di background della categoria. Testo sempre bianco (#fff) per leggibilità. Contrasto WCAG AA obbligatorio.
  - Geografia: `#1a3a5c` (blu oceano)
  - Tecnologia: `#0d3b2e` (verde circuito)
  - Scienze: `#1b4d5c` (azzurro lab)
  - Sport: `#5c2a0d` (arancio scuro)
  - Storia: `#4a3b1f` (dorato antico)
  - Cibo e benessere: `#5c1a1a` (rosso caldo)
  - Attualità: `#2a3545` (grigio blu)
  - Matematica: `#1a2a1a` (verde lavagna)
  - Musica: `#3d1a4a` (viola)
  - Cinema: `#3d0d0d` (rosso cinema)
  - Letteratura: `#3d2a1a` (marrone caldo)
  - Arte: `#2a2a4a` (indaco)
  - Inglese: `#1a1a4a` (blu scuro)
  - Lingue straniere: `#4a3a1a` (ambra)
  - Anagrammi: `#2a3d1a` (verde legno)
  - Indovinelli: `#3d3d0d` (giallo scuro/senape)
  - Di tutto un po': `#2a1a3d` (viola scuro)
- Opzioni come card/bottoni cliccabili con hover (schiarimento leggero al passaggio).
- Feedback con colori chiari: verde per corretto, rosso per sbagliato.
- Transizioni fluide tra domande.
- Design pulito e moderno, adatto a una serata tra amici.

## Accessibilità
- Navigazione da tastiera (Tab + Enter per selezionare).
- Contrasto sufficiente (WCAG AA).
- Aria-labels dove utile.
- Focus visibile sugli elementi interattivi.

## Musica di background
- Un loop audio leggero (30-60 secondi) codificato in base64, che parte all'inizio del quiz.
- Volume al 30-40% (0.3-0.4).
- Si mette in **pausa automaticamente** quando si arriva a una domanda musicale con audio.
- **Riprende** quando si passa alla domanda successiva (non musicale).
- L'utente fornisce la traccia; l'agente la converte e la inserisce inline.

## Sistema streak
- Quando il giocatore risponde correttamente a domande consecutive, si attiva una streak.
- **Indicatore visivo:** icona fiamma 🔥 che cresce con la streak:
  - 3 di fila: 🔥 piccola + bonus **+50 punti**
  - 5 di fila: 🔥🔥 media + bonus **+100 punti**
  - 7 di fila: 🔥🔥🔥 grande + bonus **+200 punti**
- I bonus sono fissi e si sommano al punteggio della risposta.
- La streak si resetta a zero alla prima risposta sbagliata o tempo scaduto.
- La fiamma è visibile accanto al punteggio, cresce progressivamente. Niente testi esagerati, solo la fiamma.

## Moltiplicatore x2
- Il giocatore ha a disposizione **4 moltiplicatori x2** per tutto il quiz.
- Prima di confermare la risposta, può attivare il moltiplicatore (pulsante dedicato).
- Se risponde **correttamente**: i punti guadagnati per quella domanda sono raddoppiati (x2).
- Se risponde **sbagliato** con moltiplicatore attivo: la penalità è moltiplicata per **x1.5**.
- I moltiplicatori rimanenti sono visualizzati (es. "⚡ x2 rimasti: 3/4").
- Una volta usato, il moltiplicatore è consumato anche se la risposta è sbagliata.
- Il moltiplicatore non si applica ai bonus streak (quelli restano fissi).

## Domande con immagine
- Le domande possono includere un'immagine (quadro, mappa, bandiera, ecc.) codificata in base64 inline.
- L'immagine è mostrata sopra le opzioni di risposta, centrata, con dimensione responsive (max-width 100%, max-height ~300px su mobile).
- **Domande di arte:** possono chiedere:
  - "Chi ha dipinto questo quadro?" (autore)
  - "A quale corrente artistica appartiene questo quadro?" (impressionismo, espressionismo, ecc.)
  - "In quale periodo è stato dipinto?" — opzioni come secolo o arco di anni (es. "1730-1780"), mai anno esatto.
- **Domande di geografia con mappa:** SVG inline con un paese evidenziato, chiedere "Quale paese è evidenziato?".
- Le immagini vanno salvate in `art_questions_images/` e convertite in base64 per l'inserimento nell'HTML.
