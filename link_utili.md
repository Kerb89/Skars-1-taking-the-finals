# Quizzone — Link utili

## Repository del progetto
- [Skars-1-taking-the-finals (GitHub)](https://github.com/Kerb89/Skars-1-taking-the-finals)

## Scaricare audio da YouTube
- **yt-dlp** (terminale, il più affidabile): `winget install yt-dlp` poi `yt-dlp -x --audio-format mp3 "URL"`
- [y2mate.nu](https://y2mate.nu) — sito web, scarica MP3 da YouTube
- [9convert.com](https://9convert.com) — alternativa
- [ytmp3.la](https://ytmp3.la) — alternativa

## Tagliare spezzoni audio
- [mp3cut.net](https://mp3cut.net) — taglia MP3 online, seleziona i secondi esatti

## Convertire in base64 (se serve manualmente)
- [base64.guru/converter/encode/file](https://base64.guru/converter/encode/file) — carica file, ottieni base64
- Oppure da terminale Windows: `certutil -encode file.mp3 output.txt`
- Oppure con lo script `convert_b64.ps1` nella cartella del progetto

## Banche dati domande trivia
- [Open Trivia Database (opentdb.com)](https://opentdb.com/api_config.php) — API gratuita, senza API key. 5.000+ domande verificate in 24 categorie, 3 livelli di difficoltà, formato JSON. Licenza CC BY-SA 4.0. Endpoint: `https://opentdb.com/api.php?amount=10&category=9&difficulty=hard&type=multiple`
- [triviaJSON (GitHub)](https://github.com/itmmckernan/triviaJSON) — repository clonato in `trivial_pursuit/`. File JSON divisi per categoria (geography, history, music, sports, ecc.).
- [OpenTriviaQA (GitHub)](https://github.com/uberspot/OpenTriviaQA) — dataset Creative Commons con ~50.000 domande trivia in formato testo. Domande tendenzialmente facili ma utili come spunto.
- [Open-trivia-database (GitHub)](https://github.com/el-cms/Open-trivia-database) — altro database open di domande e risposte.
- [briansunter/TriviaQuestions (GitHub)](https://github.com/briansunter/TriviaQuestions) — database di domande trivia varie.
- [Reddit r/trivia — thread con risorse](https://www.reddit.com/r/trivia/comments/3wzpvt/free_database_of_50000_trivia_questions/) — raccolta di link a database gratuiti.
- [Jeopardy Questions (Google Drive)](https://drive.google.com/file/d/0Bzs-xvR-5hQ3WktpWVA2RmROY1U/view?resourcekey=0-u03CutV7Ye9rxiuUE8c_UQ) — database domande stile Jeopardy.
- [Trivia Database (Google Drive)](https://drive.google.com/file/d/0Bzs-xvR-5hQ3SGdxNXpWVHFNWG8/view?resourcekey=0-5QvXBiHQPm_KmkhXP9RO8g) — altro file con domande trivia.

## Immagini per domande di arte
- [WikiArt](https://www.wikiart.org/) — enciclopedia di arti visive, immagini di quadri in alta qualità. Fonte per domande di arte con immagine.
- Le immagini scaricate vanno nella cartella `art_questions_images/`.
- Per le domande con immagine: scaricare il quadro, inserirlo in base64 nell'HTML (come per l'audio), mostrare l'immagine e chiedere autore, titolo o periodo.

## Workflow completo per domande musicali
1. Scarica il brano da YouTube (yt-dlp o sito)
2. Taglia lo spezzone 10-15 secondi su mp3cut.net
3. Salva il file MP3 nella cartella `canzoni/`
4. Dimmi il nome file e la canzone — faccio tutto io (conversione + inserimento nell'HTML)
