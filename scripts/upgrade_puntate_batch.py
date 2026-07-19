#!/usr/bin/env python3
"""
upgrade_puntate_batch.py — Aggiorna TUTTE le puntate HTML:
  a) Aggiunge tasto "Torna alla selezione delle puntate" nel recap
  b) Porta la sezione upload al dual-write (uploadId + D1 fetch)
  c) Rimuove i substring troncanti nelle domande (export/recap)

IDEMPOTENTE: rilanciarlo non duplica nulla (controlla prima di inserire).

Uso: python scripts/upgrade_puntate_batch.py [--dry-run]
"""

import re
import sys
import argparse
from pathlib import Path


def add_home_button(html):
    """Aggiunge il tasto 'Torna alla selezione' dopo uploadBtn/uploadMsg se non presente."""
    if '../index.html' in html:
        return html  # gia presente

    # Cerca il bottone upload o il div uploadMsg e aggiungi dopo
    patterns = [
        (r'(<div[^>]*id=["\']uploadMsg["\'][^>]*>.*?</div>)', 'after'),
        (r'(<button[^>]*id=["\']uploadBtn["\'][^>]*>.*?</button>)', 'after'),
    ]
    for pat, pos in patterns:
        m = re.search(pat, html)
        if m:
            btn = '\n            <a href="../index.html" class="share-btn" style="display:inline-block;margin-top:10px;text-align:center;text-decoration:none;">\U0001f3e0 Torna alla selezione delle puntate</a>'
            html = html[:m.end()] + btn + html[m.end():]
            return html

    return html


def fix_truncation(html):
    """Rimuove substring/slice che tronca il testo domanda nel recap e export."""
    # q.q.substring(0, 60) + (q.q.length > 60 ? '...' : '')  -> q.q
    html = re.sub(
        r"q\.q\.substring\(\s*0\s*,\s*\d+\s*\)\s*\+\s*\(q\.q\.length\s*>\s*\d+\s*\?\s*['\"][^'\"]*['\"]\s*:\s*['\"][^'\"]*['\"]\s*\)",
        "q.q",
        html
    )
    # q.q.substring(0, N) + '...' or + '\u2026'
    html = re.sub(
        r"q\.q\.substring\(\s*0\s*,\s*\d+\s*\)\s*\+\s*['\"][^'\"]*['\"]",
        "q.q",
        html
    )
    # standalone q.q.substring(0, N)
    html = re.sub(
        r"q\.q\.substring\(\s*0\s*,\s*\d+\s*\)",
        "q.q",
        html
    )
    # quizData[X].q.substring(0, N) + '...'
    html = re.sub(
        r"(quizData\[[^\]]+\]\.q)\.substring\(\s*0\s*,\s*\d+\s*\)\s*\+?\s*['\"\u2026.]*",
        r"\1",
        html
    )
    # questions[X].q.substring(0, N)
    html = re.sub(
        r"(questions\[[^\]]+\]\.q)\.substring\(\s*0\s*,\s*\d+\s*\)",
        r"\1",
        html
    )
    return html


def add_dual_write(html):
    """Aggiunge il dual-write D1 se non presente. Se la struttura è vecchia, sostituisce l'intero blocco upload."""
    if 'fetch(D1_URL' in html:
        return html  # dual-write gia completo

    if 'WORKER_URL' not in html:
        return html  # non ha nemmeno upload worker

    # Strategia: trova il blocco da WORKER_URL fino alla fine dell'auto-upload e sostituiscilo
    upload_block_pattern = re.compile(
        r"(?://[^\n]*(?:UPLOAD|upload)[^\n]*\n)?"
        r"const WORKER_URL=[^\n]+\n"
        r"(?:const D1_URL=[^\n]+\n)?"
        r"(.*?)"
        r"if\s*\(KNOWN_PLAYERS[^\n]+\{[^\n]*\}[^\n]*",
        re.DOTALL
    )

    m = upload_block_pattern.search(html)
    if not m:
        # Alternativa: cerca fino a includes(playerName e la riga dopo
        upload_block_pattern2 = re.compile(
            r"(?://[^\n]*(?:UPLOAD|upload)[^\n]*\n)?"
            r"const WORKER_URL=[^\n]+\n"
            r"(?:const D1_URL=[^\n]+\n)?"
            r"(.*?)"
            r"if\s*\(KNOWN_PLAYERS[^\n]+\{[^\}]*\}",
            re.DOTALL
        )
        m = upload_block_pattern2.search(html)

    if not m:
        return html

    new_block = """// ============================================================
// UPLOAD RISULTATI VIA CLOUDFLARE WORKER + D1 (dual-write)
const WORKER_URL='https://quiz-results.kerberozzo89.workers.dev';
const D1_URL='https://skars-1.pages.dev/api/results';
const KNOWN_PLAYERS=['mattia','matt','jacopo','manuel','tato','gunny','ronny'];
const uploadBtn=$('uploadBtn'),uploadMsg=$('uploadMsg');
let uploadDone=false;
function doUpload(){
  if(uploadDone)return;
  uploadBtn.disabled=true;uploadBtn.textContent='Caricamento...';
  uploadMsg.className='upload-msg';uploadMsg.textContent='';
  const corr=results.filter(r=>r.isCorrect).length;
  const avgTime=(results.reduce((s,r)=>s+(parseFloat(r.timeUsed)||parseFloat(r.time)||0),0)/results.length).toFixed(1);
  const now=new Date(),ts=now.toISOString();
  const dp=now.getFullYear()+('0'+(now.getMonth()+1)).slice(-2)+('0'+now.getDate()).slice(-2)+'_'+('0'+now.getHours()).slice(-2)+('0'+now.getMinutes()).slice(-2)+('0'+now.getSeconds()).slice(-2);
  const pName=playerName.trim().toLowerCase().replace(/[^a-z0-9]/g,'');
  const tsCompact=now.getUTCFullYear()+('0'+(now.getUTCMonth()+1)).slice(-2)+('0'+now.getUTCDate()).slice(-2)+'T'+('0'+now.getUTCHours()).slice(-2)+('0'+now.getUTCMinutes()).slice(-2)+('0'+now.getUTCSeconds()).slice(-2)+'Z';
  const uploadId=QUIZ_META.filename+'_'+pName+'_'+tsCompact;
  const resultsArr=results.map(function(r){var q=questions[r.index||r.qIdx||0]||{};var opts=r.options||q.opts||[];var corIdx=typeof r.correct!=='undefined'?r.correct:q.ans;var chIdx=r.chosen;return{question:r.question||q.q||'',category:r.category||q.cat||'',correct:r.isCorrect,timeout:r.isTimeout||(chIdx<0),points:r.points||0,streakBonus:r.streakBonus||0,multiplierUsed:r.multiplierUsed||false,timeUsed:parseFloat(r.timeUsed||r.time||0),chosenOption:chIdx>=0?opts[chIdx]:null,correctOption:Array.isArray(corIdx)?corIdx.map(function(c){return opts[c]}).join(' / '):opts[corIdx]||'',contest:r.contest||null}});
  const payload={quizId:QUIZ_META.filename,quizTitle:QUIZ_META.title,playerName:playerName,timestamp:ts,score:score,correct:corr,total:questions.length,percentage:Math.round(corr/questions.length*100),maxStreak:maxStreak,avgTime:parseFloat(avgTime),multiplierStats:{used:4-multiplierRemaining,remaining:multiplierRemaining},results:resultsArr};
  const filePath='stats/results/'+QUIZ_META.filename+'_'+pName+'_'+dp+'.json';
  // --- Invio 1: Worker GitHub ---
  fetch(WORKER_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filePath:filePath,payload:payload,commitMessage:'Risultati: '+playerName+' - '+QUIZ_META.title})}).then(function(r){return r.json()}).then(function(d){
    if(d.success){uploadDone=true;uploadMsg.textContent='Risultati caricati!';uploadMsg.className='upload-msg visible success';uploadBtn.textContent='Caricato';}
    else{throw new Error(d.error||'Errore')}
  }).catch(function(e){uploadMsg.textContent='Errore: '+e.message;uploadMsg.className='upload-msg visible error';uploadBtn.disabled=false;uploadBtn.textContent='Riprova';});
  // --- Invio 2: D1 (dual-write, fire-and-forget) ---
  try{fetch(D1_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({uploadId:uploadId,quizId:QUIZ_META.filename,quizTitle:QUIZ_META.title,playerName:playerName,timestamp:ts,score:score,correct:corr,total:questions.length,percentage:Math.round(corr/questions.length*100),maxStreak:maxStreak,avgTime:parseFloat(avgTime),multiplierStats:{used:4-multiplierRemaining,remaining:multiplierRemaining},results:resultsArr})}).then(function(r){return r.json()}).then(function(d){console.log('[D1 dual-write]',d)}).catch(function(e){console.warn('[D1 dual-write] fallito:',e.message)})}catch(e){console.warn('[D1 dual-write] errore:',e.message)}
}
uploadBtn.addEventListener('click',doUpload);
if(KNOWN_PLAYERS.indexOf(playerName.trim().toLowerCase())>=0){setTimeout(doUpload,500);}"""

    html = html[:m.start()] + new_block + html[m.end():]
    return html


def ensure_results_has_question(html):
    """Assicura che results.push contenga il campo question con il testo completo."""
    # Se ha gia 'question:' nel results.push, ok
    if re.search(r"results\.push\(\{[^}]*question\s*:", html):
        return html

    # Vecchio pattern: results.push({ qIdx: currentQ, chosen:..., correct:..., ...})
    # Aggiungi question e category
    html = re.sub(
        r"results\.push\(\{\s*qIdx:\s*currentQ\s*,\s*chosen",
        "results.push({ qIdx: currentQ, question: q.q, category: q.cat || '', options: q.opts, chosen",
        html
    )
    return html


def process_file(path, dry_run=False):
    """Processa una singola puntata. Ritorna (modified, changes)."""
    html = path.read_text(encoding='utf-8', errors='replace')
    original = html
    changes = []

    # a) Tasto home
    html_new = add_home_button(html)
    if html_new != html:
        changes.append('home_button')
        html = html_new

    # b) Fix truncation
    html_new = fix_truncation(html)
    if html_new != html:
        changes.append('fix_truncation')
        html = html_new

    # c) Ensure results has question field
    html_new = ensure_results_has_question(html)
    if html_new != html:
        changes.append('add_question_field')
        html = html_new

    # d) Dual-write D1
    html_new = add_dual_write(html)
    if html_new != html:
        changes.append('dual_write')
        html = html_new

    modified = html != original
    if modified and not dry_run:
        path.write_text(html, encoding='utf-8')

    return modified, changes


def main():
    parser = argparse.ArgumentParser(description="Upgrade batch puntate HTML")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    puntate_dir = Path("puntate")
    files = sorted(puntate_dir.glob("quiz_puntata*.html"),
                   key=lambda f: int(re.search(r'puntata(\d+)', f.name).group(1)))

    print(f"\n=== Upgrade batch -- {len(files)} puntate ===")
    if args.dry_run:
        print("*** DRY RUN ***\n")

    modified_count = 0
    for f in files:
        modified, changes = process_file(f, args.dry_run)
        status = "MODIFICATO" if modified else "OK (nessuna modifica)"
        detail = f" [{', '.join(changes)}]" if changes else ""
        print(f"  {f.name}: {status}{detail}")
        if modified:
            modified_count += 1

    print(f"\n=== Risultato: {modified_count}/{len(files)} puntate modificate ===\n")


if __name__ == "__main__":
    main()
