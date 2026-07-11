---
inclusion: fileMatch
fileMatchPattern: "art_questions_images/**"
---

# Quizzone — Validazione immagini d'arte

## Pipeline di verifica (obbligatoria quando si scaricano/aggiungono immagini)

Ogni volta che si scaricano nuove immagini d'arte dall'API o da qualsiasi fonte, applicare questa pipeline **prima** di usarle nel quiz.

### 1. Deduplica (hash MD5 — deterministico, zero AI)

```python
import hashlib, os
from collections import defaultdict

hashes = defaultdict(list)
for f in os.listdir(directory):
    if f.endswith('.jpg'):
        h = hashlib.md5(open(os.path.join(directory, f), 'rb').read()).hexdigest()
        hashes[h].append(f)

# Hash identico = stessa immagine. Due nomi diversi sullo stesso hash = almeno un titolo è falso.
for h, files in hashes.items():
    if len(files) > 1:
        print(f"DOPPIONE: {files}")
```

**Regola:** hash identico con nomi diversi → almeno un nome è sbagliato. Eliminare il doppione e indagare quale nome è corretto.

### 2. Riconoscimento visivo "alla cieca" (richiede modello multimodale con vision)

- **NON** usare il nome file come input per l'identificazione (bias da ancoraggio).
- Identificare l'opera esclusivamente dai pixel: "Cos'è questo quadro?" — mai "Questo è X?".
- Le opere del Met Open Access hanno un aspetto riconoscibile: fondo neutro, cornice inclusa.
- Solo DOPO l'identificazione alla cieca, confrontare col nome file per decidere conferma/rinomina.

**Se non si ha accesso vision:** flaggare l'immagine per verifica umana.

### 3. Validatore ratio/palette (deterministico — smaschera incoerenze)

```python
from PIL import Image

img = Image.open(filepath)
w, h = img.size
ratio = w / h  # >1 = orizzontale, <1 = verticale

# Confrontare con dimensioni reali da catalogo (metmuseum.org, Wikipedia)
# Esempio: La Grande Onda è ~1.47 (orizzontale)
#          Se il file "hokusai_grande_onda" ha ratio 0.70 → FALSO
```

**Regola:** non dice cos'è il quadro, dice cosa NON PUÒ essere. Gate che boccia le allucinazioni.

### 4. Soglia di confidenza

- Se vision + metadati convergono → confidence alta → rinomina/conferma automatica
- Se divergono (riproduzione scura, ratio non perfetto) → confidence bassa → flaggare per verifica umana
- **Mai committare una rinomina a bassa confidenza senza approvazione esplicita**

## Regola d'oro

> Il nome file è un **claim**, non un dato. Non va mai usato come input per l'identificazione.
> Si identifica alla cieca dai pixel, e solo dopo si confronta col nome per decidere conferma/rinomina.

## Workflow pratico per scaricare nuove opere

1. Trova l'ID numerico preciso dal sito metmuseum.org (non dalla search API)
2. Chiama `/objects/{id}` → verifica che `title` e `artistDisplayName` corrispondano
3. Scarica `primaryImageSmall`
4. Applica step 1 (hash) e step 3 (ratio) come validazione automatica
5. Nomina il file come: `{artista}_{titolo_abbreviato}_{anno}.jpg`
6. Se possibile, verifica visivamente (step 2) prima di usare nel quiz
