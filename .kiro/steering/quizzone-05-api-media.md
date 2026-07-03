---
inclusion: always
---

# Quizzone — API per domande con immagini (Arte e Cinema)

## API Arte — Met Museum Open Access

- **URL base**: `https://collectionapi.metmuseum.org/public/collection/v1/`
- **Auth**: Nessuna (completamente aperta)
- **Licenza**: Open Access (CC0 per le immagini public domain)
- **Endpoint principali**:
  - Cerca: `/search?q={query}&hasImages=true&isPublicDomain=true&departmentId=11`
    - `departmentId=11` = European Paintings
  - Dettaglio opera: `/objects/{id}`
    - Campo `primaryImageSmall` → URL immagine diretta scaricabile con curl
    - Campo `primaryImage` → versione ad alta risoluzione
  - Campi utili: `title`, `artistDisplayName`, `objectDate`, `medium`, `department`
- **Download**: `curl.exe -s -L -o file.jpg {primaryImageSmall_url}` (funziona direttamente)
- **Script progetto**: `scripts/download_art2.py`
- **Nota**: la search API non è sempre precisa. Se cerchi un quadro specifico, meglio navigare il sito del Met e prendere l'ID dall'URL (es. metmuseum.org/art/collection/search/436535 → ID 436535)

### Workflow per scaricare un quadro
1. Cerca l'opera su metmuseum.org, prendi l'ID numerico dall'URL
2. Chiama `/objects/{id}` → prendi `primaryImageSmall`
3. Scarica con curl, salva in `art_questions_images/da_usare/`
4. Converti in base64 (PIL, thumbnail 500px, quality 50)
5. Inserisci nel campo `"img"` della domanda

### Compressione per base64
```python
from PIL import Image
import base64, io
img = Image.open("percorso.jpg")
img.thumbnail((500, 500), Image.LANCZOS)
buf = io.BytesIO()
img.convert("RGB").save(buf, format="JPEG", quality=50, optimize=True)
b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
```

---

## API Cinema — TMDB (The Movie Database)

- **URL base**: `https://api.themoviedb.org/3/`
- **Auth**: API key (gratuita, registrarsi su themoviedb.org). Header: `Authorization: Bearer {token}` oppure query param `?api_key={key}`
- **Licenza**: Gratuita per uso non commerciale, richiede attribuzione "Data provided by TMDB"
- **Endpoint principali**:
  - Cerca film: `/search/movie?query={title}&language=it-IT`
  - Dettaglio film: `/movie/{id}?language=it-IT`
  - Immagini film: `/movie/{id}/images` (restituisce poster in più lingue)
- **URL immagine poster**: `https://image.tmdb.org/t/p/{size}/{poster_path}`
  - Sizes disponibili: `w92`, `w154`, `w185`, `w342`, `w500`, `w780`, `original`
  - Per il quiz usare `w342` o `w500` (buon bilanciamento qualità/peso)
- **Uso nel quiz**: Scaricare la locandina, **ritagliare il titolo** (crop la parte alta o bassa dove appare il testo del titolo), convertire in base64 e usare come domanda "Quale film è questo?"
- **API key**: DA CONFIGURARE — registrarsi su https://www.themoviedb.org/settings/api

### Workflow per domande cinema con locandina
1. Cerca il film su TMDB API → prendi `poster_path`
2. Scarica: `https://image.tmdb.org/t/p/w500/{poster_path}`
3. **Censura il testo** con `scripts/censor_poster.py` (OCR + blur automatico)
4. Comprimi e converti in base64
5. Domanda: "Quale film è rappresentato in questa locandina?" con 4 opzioni

### Censura automatica del testo (OCR + blur)
Lo script usa EasyOCR per rilevare automaticamente TUTTO il testo nella locandina (titolo, attori, tagline) e applica un blur forte (pixelation + gaussian) sulle zone rilevate.

```bash
# Blurra TUTTO il testo (consigliato per il quiz)
python scripts/censor_poster.py poster.jpg poster_notext.jpg

# Blurra solo il titolo (il testo piu' grande)
python scripts/censor_poster.py poster.jpg poster_notitle.jpg --title-only
```

Dipendenze: `easyocr` (installato), `Pillow`, `torch`.
Prima esecuzione scarica i modelli OCR (~50MB).

**IMPORTANTE**: Lo script è automatico, non serve specificare coordinate. Il blur rende illeggibile il testo ma preserva la composizione visiva della locandina.

---

## Lista artisti per domande d'arte

### Italia
- Caravaggio (Michelangelo Merisi) — Barocco
- Sandro Botticelli — Rinascimento
- Leonardo da Vinci — Rinascimento
- Raffaello Sanzio — Rinascimento
- Tiziano Vecellio — Rinascimento veneto
- Tintoretto — Manierismo/Rinascimento
- Amedeo Modigliani — Espressionismo/Scuola di Parigi
- Giorgio de Chirico — Metafisica
- Umberto Boccioni — Futurismo
- Giorgio Morandi — Natura morta del Novecento

### Paesi Bassi / Fiandre
- Rembrandt van Rijn — Barocco olandese
- Johannes Vermeer — Barocco olandese
- Hieronymus Bosch — Tardo gotico
- Pieter Bruegel il Vecchio — Rinascimento fiammingo
- Vincent van Gogh — Post-impressionismo
- Piet Mondrian — De Stijl / Astrattismo

### Spagna
- Diego Velázquez — Barocco
- Francisco Goya — Romanticismo
- El Greco (Doménikos Theotokópoulos) — Manierismo
- Pablo Picasso — Cubismo
- Joan Miró — Surrealismo
- Salvador Dalí — Surrealismo

### Francia
- Claude Monet — Impressionismo
- Pierre-Auguste Renoir — Impressionismo
- Edgar Degas — Impressionismo
- Paul Cézanne — Post-impressionismo
- Henri Matisse — Fauvismo
- Georges Seurat — Puntinismo
- Paul Gauguin — Post-impressionismo
- Eugène Delacroix — Romanticismo
- Auguste Rodin — Scultura moderna
- Marcel Duchamp — Dadaismo

### Germania / Austria
- Gustav Klimt — Art Nouveau/Secessione viennese
- Egon Schiele — Espressionismo
- Albrecht Dürer — Rinascimento tedesco
- Caspar David Friedrich — Romanticismo
- Paul Klee — Espressionismo/Astrattismo
- Wassily Kandinsky — Astrattismo (russo-tedesco)

### Norvegia / Scandinavia
- Edvard Munch — Espressionismo

### Regno Unito
- J.M.W. Turner — Romanticismo
- John Constable — Romanticismo/Paesaggismo
- William Turner — Pre-raffaelliti
- Francis Bacon — Arte contemporanea
- Banksy — Street art

### Russia
- Wassily Kandinsky — Astrattismo
- Kazimir Malevič — Suprematismo
- Marc Chagall — Modernismo

### Stati Uniti
- Edward Hopper — Realismo americano
- Jackson Pollock — Espressionismo astratto
- Andy Warhol — Pop Art
- Jean-Michel Basquiat — Neo-espressionismo
- Georgia O'Keeffe — Modernismo americano
- Mark Rothko — Espressionismo astratto (nato in Lettonia)

### Messico
- Frida Kahlo — Surrealismo/Realismo magico
- Diego Rivera — Muralismo

### Giappone
- Katsushika Hokusai — Ukiyo-e
- Utagawa Hiroshige — Ukiyo-e
- Yayoi Kusama — Arte contemporanea

### Cina
- Ai Weiwei — Arte contemporanea/Attivismo

### Colombia
- Fernando Botero — Figurativismo

### Svizzera
- Alberto Giacometti — Scultura surrealista/esistenzialista

### Belgio
- René Magritte — Surrealismo
- James Ensor — Espressionismo

### Grecia (antico/moderno)
- El Greco (vedi Spagna — greco di nascita)

---

## Piano immagini già disponibili

Vedi `art_questions_images/PIANO_ARTE_PUNTATE.md` per l'assegnazione alle puntate future.
