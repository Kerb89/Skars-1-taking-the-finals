import { caricaJSON } from './core/contenuto.js';
import { el } from './core/ui.js';

const GIOCHI = [
  ['tutti', 'Partita completa'], ['parole', 'Parole impossibili'], ['bocciato', 'Bocciato'],
  ['elemento', 'Elemento comune'], ['titolo', 'Completa il titolo'], ['manolesta', 'Mano lesta'],
  ['ruota', 'Ruota finale'],
];

const form = document.getElementById('form-avvio');
const nick = document.getElementById('nick');
const sel = document.getElementById('partita');
const scelte = document.getElementById('scelte');
const errore = document.getElementById('errore-avvio');

try { nick.value = localStorage.getItem('giralettere.nick') || ''; } catch (_) {}

GIOCHI.forEach(([id, nome], i) => {
  scelte.append(el('label', { class: 'scelta' },
    el('input', { type: 'radio', name: 'gioco', value: id, checked: i === 0 || null }), nome));
});

caricaJSON('partite/index.json').then(({ partite }) => {
  const richiesta = new URLSearchParams(location.search).get('partita');
  partite.forEach((p) => sel.append(el('option', { value: p.id, selected: p.id === richiesta || null }, p.titolo)));
}).catch((e) => { errore.hidden = false; errore.textContent = e.message; });

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const n = nick.value.trim();
  if (!n) { errore.hidden = false; errore.textContent = 'Scegli un nickname per iniziare.'; nick.focus(); return; }
  try { localStorage.setItem('giralettere.nick', n); } catch (_) {}
  const gioco = form.querySelector('input[name=gioco]:checked')?.value || 'tutti';
  const q = new URLSearchParams({ partita: sel.value, gioco, nick: n });
  location.href = 'gioca/?' + q.toString();
});
