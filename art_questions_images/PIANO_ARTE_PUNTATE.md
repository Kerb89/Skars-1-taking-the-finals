# Piano Domande d'Arte con Immagini — Puntate Future

## Fonte immagini
- **Met Museum Open Access API** (funziona, no auth necessaria)
  - Endpoint: `https://collectionapi.metmuseum.org/public/collection/v1/objects/{ID}`
  - Immagine: campo `primaryImageSmall` nella risposta JSON
  - Script: `scripts/download_art2.py`

## Immagini disponibili (già scaricate in `art_questions_images/da_usare/`)

| # | File | Artista | Opera | Anno |
|---|------|---------|-------|------|
| 1 | van_gogh_campo_grano_cipressi_1889.jpg | Vincent van Gogh | Wheat Field with Cypresses | 1889 |
| 2 | van_gogh_autoritratto_cappello_1887.jpg | Vincent van Gogh | Self-Portrait with Straw Hat | 1887 |
| 3 | van_gogh_LArlésienne_Madame_Joseph-Mi_1888-89.jpg | Vincent van Gogh | L'Arlésienne | 1888-89 |
| 4 | van_gogh_Shoes_1888.jpg | Vincent van Gogh | Shoes (Scarpe) | 1888 |
| 5 | caravaggio_The_Musicians_1597.jpg | Caravaggio | I Musicisti | 1597 |
| 6 | el_greco_vista_toledo_1600.jpg | El Greco | Vista di Toledo | ~1600 |
| 7 | vermeer_A_Maid_Asleep_ca.1656-57.jpg | Johannes Vermeer | A Maid Asleep | 1656-57 |
| 8 | gauguin_Ia_Orana_Maria_Hail_Mary_1891.jpg | Paul Gauguin | Ia Orana Maria | 1891 |
| 9 | rembrandt_self_portrait_1659.jpg | Rembrandt | Autoritratto | 1659 |
| 10 | the_scream_munch_1893.jpg | Edvard Munch | L'Urlo | 1893 |
| 11 | turner_venezia.jpg* | Rembrandt | Self-Portrait | (da verificare) |

*Nota: alcuni file scaricati dal Met avevano ID non corrispondenti ai titoli attesi. Verificare prima dell'uso.

## Quadri da scaricare per puntate future (ID Met Museum verificati)

Eseguire lo script `scripts/download_art2.py` per aggiornare il catalogo. ID utili:
- Cerca "Monet" departmentId=11 → ninfee, impressione
- Cerca "Degas" departmentId=11 → ballerine
- Cerca "Cezanne" departmentId=11 → nature morte, paesaggi
- Cerca "Renoir" departmentId=11 → ritratti, scene di vita

## Assegnazione quadri alle puntate

### Puntata 19 (FATTO ✓)
- Van Gogh — Autoritratto con cappello di paglia (1887) → "Chi ha dipinto questo?"
- Caravaggio — I Musicisti (1597) → "Chi ha dipinto questo?"
- El Greco — Vista di Toledo (~1600) → "Chi ha dipinto questo?"

### Puntata 20
- Rembrandt — Autoritratto 1659 (già in `art_questions_images/rembrandt_self_portrait_1659.jpg`)
- Van Gogh — Campo di grano con cipressi (1889) → "Quale opera di Van Gogh è questa?"
- Gauguin — Ia Orana Maria (1891) → "Chi ha dipinto questo? / In quale isola visse Gauguin?"

### Puntata 21
- Munch — L'Urlo (già in `art_questions_images/the_scream_munch_1893.jpg`)
- Vermeer — A Maid Asleep (1656-57) → "Chi ha dipinto questo?"
- Van Gogh — L'Arlésienne (1888-89) → "Come si chiama la donna ritratta?" / "Chi l'ha dipinto?"

### Puntata 22
- Van Gogh — Shoes (1888) → "Quale artista dipinse questa natura morta di scarpe?"
- [Da scaricare] Monet — Ninfee → "Chi ha dipinto questo? / Quale giardino?"
- [Da scaricare] Degas — Ballerine → "Chi ha dipinto questa scena?"

### Puntata 23+
- [Da scaricare] Klimt — (cercare su Met o altra fonte)
- [Da scaricare] Hokusai — Grande Onda (cercare su Met, dept Asian Art)
- [Da scaricare] Cézanne — Monte Sainte-Victoire
- [Da scaricare] Renoir — scena sociale

## Tipi di domande d'arte con immagine

1. **"Chi ha dipinto questo?"** — Mostra il quadro, 4 opzioni artista
2. **"Come si chiama quest'opera?"** — Mostra il quadro, 4 opzioni titolo
3. **"In quale anno è stata dipinta?"** — Mostra il quadro, 4 opzioni anno
4. **"A quale corrente artistica appartiene?"** — Mostra il quadro, 4 opzioni (Impressionismo, Barocco, etc.)
5. **"In quale museo si trova?"** — Mostra il quadro, 4 opzioni museo

## Workflow per aggiungere un nuovo quadro

1. Cercare l'opera su Met Museum API (o scaricare manualmente)
2. Salvare in `art_questions_images/da_usare/`
3. Convertire in base64 con PIL (thumbnail 500px, quality 50):
   ```python
   from PIL import Image
   import base64, io
   img = Image.open("percorso.jpg")
   img.thumbnail((500, 500), Image.LANCZOS)
   buf = io.BytesIO()
   img.convert("RGB").save(buf, format="JPEG", quality=50, optimize=True)
   b64 = base64.b64encode(buf.getvalue()).decode()
   ```
4. Inserire nel JSON domande come: `"img": "data:image/jpeg;base64,{b64}"`
