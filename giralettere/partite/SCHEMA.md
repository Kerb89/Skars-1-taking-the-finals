# Giralettere — schema di una partita

Ogni partita è un file JSON in `giralettere/partite/`, registrato in
`partite/index.json`. Il motore non contiene contenuti: legge solo questi file.
Lo schema formale (JSON Schema draft 2020-12) è in `partita.schema.json`;
i vincoli che JSON Schema non esprime sono verificati dal motore all'avvio
(`js/core/contenuto.js`): se uno fallisce la partita non parte e l'errore
viene mostrato a schermo.

## Radice

| Campo | Tipo | Note |
|---|---|---|
| `id` | stringa | univoco, `[a-z0-9-]+`; finisce nel database come `partita_id` |
| `titolo` | stringa | mostrato in home |
| `demo` | booleano | `true` solo per partite di prova |
| `versione` | intero | da incrementare a ogni modifica di contenuto |
| `giochi` | oggetto | una chiave per gioco; un gioco assente non viene giocato |

Ogni **voce** ha un `id` stabile (es. `pi-01`): è la chiave con cui il
tracciamento aggrega le risposte nel tempo. Non riusare un id per una voce
diversa; se cambi la risposta di una voce, cambia anche l'id.

## Risposte a testo libero

Nei giochi `elemento`, `titolo`, `manolesta`, `ruota` ogni voce ha
`risposta` (forma canonica, salvata come "risposta attesa") e `varianti`
(altre forme accettate). Una risposta data è corretta solo se, normalizzata,
coincide con la normalizzazione di `risposta` o di una variante. Nessun
fuzzy matching.

Normalizzazione (`js/core/normalizza.js`), applicata a entrambi i lati:
1. minuscole;
2. rimozione degli accenti (NFD);
3. apostrofi tipografici → `'`;
4. rimozione di un articolo iniziale: `il lo la i gli le uno una un l' un'`;
5. punteggiatura e apostrofi → spazio, spazi multipli collassati, trim.

Quindi `"L'Aereo"`, `"aereo"` e `" AÈREO "` sono equivalenti; `"aerei"` no.
Per accettare `aerei` va aggiunto a `varianti`. La vista "per domanda" del
tracciamento elenca le risposte sbagliate ricorrenti proprio per questo.

## Giochi

### `parole` — Parole impossibili
`voci`: esattamente **8** oggetti `{ id, parola, definizione }`.

### `bocciato` — Bocciato
`domande`: esattamente **12** oggetti `{ id, testo, opzioni: [a, b], corretta: 0|1 }`.

### `elemento` — Elemento comune
`{ elemento, tipo: "prefisso"|"suffisso", voci: [{ id, definizione, risposta, varianti }] }`.
Almeno 1 voce. Vincolo: `risposta` e ogni variante iniziano (prefisso) o
finiscono (suffisso) con `elemento`, dopo normalizzazione.

### `titolo` — Completa il titolo
`voci: [{ id, artista, titolo_mascherato, risposta, varianti }]`.
`titolo_mascherato` contiene `___` dove va la parte mancante; `risposta` è
solo la parte mancante.

### `manolesta` — Mano lesta
`voci: [{ id, domanda, lettera, risposta, varianti }]`. Vincolo: `risposta`
e ogni variante iniziano con `lettera`.

### `ruota` — Ruota finale
`voci`: esattamente **21** oggetti `{ id, lettera, regola: "inizia"|"contiene", definizione, risposta, varianti }`,
una per ciascuna lettera di `config.json → ruota.lettere`, nello stesso
ordine. Vincolo: `risposta` e ogni variante iniziano con (o contengono, se
`regola` è `contiene`) la lettera.

## Esempio minimo

Vedi `demo.json` (partita marcata `"demo": true`, contenuti non definitivi).
