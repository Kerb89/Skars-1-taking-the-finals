---
inclusion: always
---

# Quizzone — Spiegazioni delle risposte

## FASE TESTO (.md)
Ogni domanda del `.md` include, subito dopo la risposta corretta, una riga:

```
> Spiegazione: ...
```

Regole:
- **Massimo 2-3 righe (~40 parole).** Se serve di più, la domanda è mal posta: riformulala.
- La spiegazione **aggiunge un fatto**, non ripete la risposta. Vietato "La risposta è B perché è B".
  - ❌ `> Spiegazione: La capitale dell'Australia è Canberra.`
  - ✅ `> Spiegazione: Canberra fu costruita apposta nel 1913 come compromesso tra Sydney e Melbourne, che si contendevano il ruolo.`
- La spiegazione segue le stesse regole di verifica della domanda (vedi `quizzone-02-fonti`): un fatto non verificabile non entra né nella domanda né nella spiegazione.
- Niente spiegazione = campo assente, non riga vuota.

## FASE HTML
Quando il giocatore **conferma** la risposta:
1. Appare il feedback ✓/✗ come già previsto.
2. Sotto il feedback appare una **casella spiegazione**, sempre — sia con risposta giusta che sbagliata.
3. Se la domanda non ha il campo `spiegazione` (quiz vecchi), la casella **non viene renderizzata**. Mai casella vuota, mai placeholder.

La casella è informativa, visivamente distinta dal feedback ✓/✗: bordo laterale, sfondo leggermente rialzato, testo piccolo. Non deve competere col verde/rosso del feedback.

### Snippet di riferimento
Dati: ogni oggetto domanda ha un campo opzionale `expl`.

```js
// dentro la funzione di conferma, dopo il feedback:
if (q.expl) {
  const box = document.createElement('div');
  box.className = 'explanation';
  box.textContent = q.expl;
  fb.insertAdjacentElement('afterend', box);
}
```

```css
.explanation {
  margin-top: 8px;
  padding: 10px 14px;
  border-left: 3px solid var(--accent, #888);
  background: rgba(255,255,255,0.04);
  font-size: 0.85em;
  line-height: 1.45;
  opacity: 0;
  animation: explFade .3s ease forwards;
}
@keyframes explFade { to { opacity: 1; } }
```

Adattare colori e variabili al tema dell'episodio, mantenendo la gerarchia: feedback prima, spiegazione sotto, più discreta.
