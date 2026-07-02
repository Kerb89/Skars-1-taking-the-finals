# Template Quiz HTML

## Come usarlo

Il file `quiz_template.html` è il template completo. Per generare un nuovo quiz HTML basta:

1. **Copiare** il template nel file di destinazione
2. **Sostituire i placeholder:**

| Placeholder | Esempio |
|---|---|
| `{{PUNTATA_TITLE}}` | `Puntata 7 — Misto` |
| `{{SUBTITLE}}` | `Misto — 35 domande — 20s timer` |
| `{{FILENAME}}` | `quiz_puntata7_misto` |
| `{{QUESTIONS_JSON}}` | Array JSON delle domande |
| `{{CATEGORY_BACKGROUNDS_JSON}}` | Oggetto JSON con base64 per categoria |

## Formato domande (JSON)

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

## Formato sfondi categoria (JSON)

```json
{
  "geografia": "data:image/jpeg;base64,/9j/4AAQ...",
  "sport": "data:image/jpeg;base64,/9j/4AAQ...",
  "musica": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

Ogni puntata usa un'immagine diversa per ogni categoria, scelta dalla cartella `category_backgrounds/<categoria>/`.

## Immagini disponibili per categoria

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

## Categorie disponibili (chiavi)

geografia, tecnologia, scienze, sport, storia, cibo, attualita, matematica, musica, cinema, letteratura, arte, inglese, lingue, anagrammi, dituttounpo, lingua_italiana

## Timer

- Default: 20 secondi
- Domande con audio: 30 secondi (parte quando si preme play)

## Workflow per generare una puntata

1. Generare il quiz .md (domande + soluzioni)
2. Dopo approvazione, convertire le domande in JSON
3. Scegliere un'immagine per ogni categoria (ruotare rispetto alla puntata precedente)
4. Convertire le immagini scelte in base64
5. Sostituire i placeholder nel template
6. Salvare come `quiz_puntataN_tema.html`
