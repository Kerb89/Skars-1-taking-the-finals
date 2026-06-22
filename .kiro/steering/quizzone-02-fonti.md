---
inclusion: always
---

# Quizzone — Fonti e verifica

Questa è la parte non negoziabile: un quiz con una risposta sbagliata è un quiz rotto.

## Strumenti
Usa gli strumenti integrati di Kiro `web_search` e `web_fetch` per controllare i fatti. Devono essere abilitati (controlla in `/tools` o nelle impostazioni).

## Cosa verificare — calibrato, non cieco
Verificare 2 fonti per tutte e 30 le domande ogni volta è lento e spinge a barare. Calibra:
- **Verifica SEMPRE** (≥1 fonte autorevole, preferibilmente 2 se il dato è volatile o contestato): attualità, eventi recenti, record sportivi, statistiche, primati ("il più grande / alto / primo"), date precise, qualsiasi cosa posteriore al 2023.
- **Verifica al minimo dubbio:** dati scientifici, geografici, date storiche, attribuzioni.
- **Fatti da manuale, stabili, che conosci con certezza:** puoi usarli senza ricerca; ma se hai un dubbio, dichiaralo e verifica.

## Gerarchia delle fonti
Preferisci fonti primarie e ufficiali (enti, istituzioni, pubblicazioni di riferimento). Wikipedia va bene come punto di partenza, ma per i fatti critici risali alla fonte primaria citata. Evita forum, content farm, pagine generate da AI, siti senza fonti.

## Fonti in conflitto
Non scegliere in silenzio. Se due fonti autorevoli si contraddicono su un fatto, **scarta la domanda** e sostituiscila: una domanda con risposta contestabile è un difetto, non una sfida.

## Database locali (trivial_pursuit_clean/)
I file JSON in `trivial_pursuit_clean/` sono fonti di **spunti**, non di verità. Quando una domanda del quizzone è ispirata da una domanda del database locale:
- Verifica SEMPRE la risposta con almeno una ricerca web, anche se il fatto sembra banale.
- Il database è community-contributed, può contenere errori residui, dati obsoleti o imprecisioni.
- Non usare mai una domanda del database così com'è senza double check: riformulala, verifica la risposta, e adatta al formato del quizzone.

**Regola generale: il double check va fatto su TUTTE le domande del quiz, a prescindere dalla fonte.** Non importa se la domanda viene dal database, dall'API, o dalla mia conoscenza: ogni risposta va verificata con almeno una ricerca web. Per fatti contestabili, volatili o recenti, usare 2-3 fonti indipendenti. Non esiste un eccesso di verifica — meglio tre controlli di troppo che una risposta sbagliata.

## Anti-allucinazione
- Non inventare mai una fonte o un URL.
- Se non riesci a verificare un fatto critico, **sostituisci la domanda** con una verificabile. Non tirare a indovinare.
- Non copiare blocchi di testo dalle fonti: estrai e riformula il fatto con parole tue.

## Tracciabilità (appendice obbligatoria)
In fondo al `.md`, dopo le soluzioni, aggiungi una sezione **Fonti** che mappa numero domanda → URL, per ogni domanda verificata:

```
---
## Fonti
3. https://...
11. https://...
```

Se questa sezione è assente o vuota quando dovrebbe esserci, è il segnale che la verifica non è stata fatta.
