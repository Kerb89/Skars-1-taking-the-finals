"""
Genera l'HTML finale di un quiz a partire dal template e dai dati.
Uso: python template/build_quiz_html.py <puntata_number>

Legge:
  - template/quiz_template.html
  - quiz_md/quiz_puntata{N}_misto.md (per estrarre le domande)
  - category_backgrounds/ (per le immagini)

Scrive:
  - vecchie_puntate/quiz_puntata{N}_misto.html
"""
import sys, os, json, re, base64, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

def parse_md_questions(md_path):
    """Parse questions from the .md quiz file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into questions section and solutions section
    parts = content.split('---\n## Soluzioni')
    questions_text = parts[0]
    solutions_text = parts[1] if len(parts) > 1 else ''
    
    # Parse solutions to get correct answers
    solutions = {}
    for line in solutions_text.split('\n'):
        line = line.strip()
        m = re.match(r'^(\d+)\.\s+([A-D])', line)
        if m:
            num = int(m.group(1))
            letter = m.group(2)
            solutions[num] = ord(letter) - ord('A')
    
    # Parse questions
    questions = []
    pattern = r'\*\*(\d+)\.\*\*\s+(.*?)\nA\)\s+(.*?)\nB\)\s+(.*?)\nC\)\s+(.*?)\nD\)\s+(.*?)(?=\n\n|\n\*\*|\Z)'
    for m in re.finditer(pattern, questions_text, re.DOTALL):
        num = int(m.group(1))
        q_text = m.group(2).strip()
        opts = [m.group(3).strip(), m.group(4).strip(), m.group(5).strip(), m.group(6).strip()]
        ans = solutions.get(num, 0)
        
        # Determine category based on content/position
        cat = guess_category(q_text, num)
        
        questions.append({
            'q': q_text,
            'opts': opts,
            'ans': ans,
            'cat': cat
        })
    
    return questions

def guess_category(q_text, num):
    """Simple category guesser based on keywords."""
    q_lower = q_text.lower()
    
    if 'anagramma' in q_lower:
        return 'anagrammi'
    if any(w in q_lower for w in ['film', 'regist', 'oscar', 'attore', 'attrice']):
        return 'cinema'
    if any(w in q_lower for w in ['canzone', 'testo della canzone', 'musicale', 'artista', 'brano']):
        return 'musica'
    if any(w in q_lower for w in ['in inglese', 'in english', 'verbale completa', 'grammaticalmente']):
        return 'inglese'
    if any(w in q_lower for w in ['in francese', 'in tedesco', 'in spagnolo', 'in giapponese', 'in portoghese', 'significa']):
        if any(w in q_lower for w in ['francese', 'tedesco', 'spagnolo', 'giapponese', 'portoghese']):
            return 'lingue'
    if any(w in q_lower for w in ['figura retorica', 'plurale', 'passato remoto', 'ortografi']):
        return 'lingua_italiana'
    if any(w in q_lower for w in ['dipinse', 'pittore', 'pittorica', 'corrente artistica', 'scultura']):
        return 'arte'
    if any(w in q_lower for w in ['romanzo', 'scrittore', 'scritto', 'autore', 'poeta', 'letteratura']):
        return 'letteratura'
    if any(w in q_lower for w in ['informatica', 'programmazione', 'algoritmo', 'struttura dati', 'protocollo', 'linguaggio di prog']):
        return 'tecnologia'
    if any(w in q_lower for w in ['risultato di', 'quanto fa', 'radice', 'somma', 'probabilità', 'formula']):
        return 'matematica'
    if any(w in q_lower for w in ['vinto', 'campion', 'olimpi', 'coppa', 'champions', 'mondiale', 'sport', 'ghiaccio']):
        return 'sport'
    if any(w in q_lower for w in ['paese', 'capitale', 'lago', 'monte', 'continente', 'stretto', 'confine', 'deserto']):
        return 'geografia'
    if any(w in q_lower for w in ['anno', 'trattato', 'guerra', 'impero', 'fondato', 'firmato', 'storia']):
        return 'storia'
    if any(w in q_lower for w in ['vitamina', 'enzima', 'spezia', 'alimento', 'calori', 'cibo']):
        return 'cibo'
    if any(w in q_lower for w in ['particella', 'formula chimica', 'elemento', 'neurotrasm', 'atomo', 'molecola']):
        return 'scienze'
    if any(w in q_lower for w in ['2024', '2025', '2026', 'recente']):
        return 'attualita'
    
    return 'dituttounpo'

def get_backgrounds(puntata):
    """Get category background images as base64."""
    bg_dir = os.path.join(BASE, 'category_backgrounds')
    categories = [
        "anagrammi", "arte", "attualita", "cibo", "cinema", "dituttounpo",
        "geografia", "inglese", "letteratura", "lingua_italiana", "lingue",
        "matematica", "musica", "scienze", "sport", "storia", "tecnologia"
    ]
    
    result = {}
    for cat in categories:
        folder = os.path.join(bg_dir, cat)
        if not os.path.isdir(folder):
            continue
        images = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if not images:
            continue
        idx = (puntata - 1) % len(images)
        filepath = os.path.join(folder, images[idx])
        
        img = Image.open(filepath)
        img.thumbnail((600, 600), Image.LANCZOS)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=55, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        result[cat] = f"data:image/jpeg;base64,{b64}"
    
    return result

def build_html(puntata):
    md_path = f'quiz_md/quiz_puntata{puntata}_misto.md'
    template_path = 'template/quiz_template.html'
    output_path = f'vecchie_puntate/quiz_puntata{puntata}_misto.html'
    
    if not os.path.exists(md_path):
        print(f'ERROR: {md_path} not found')
        return
    
    # Parse questions
    questions = parse_md_questions(md_path)
    print(f'Parsed {len(questions)} questions from {md_path}')
    
    # Get backgrounds
    backgrounds = get_backgrounds(puntata)
    print(f'Generated {len(backgrounds)} category backgrounds')
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Replace placeholders
    title = f'Puntata {puntata} — Misto'
    subtitle = f'Misto — {len(questions)} domande — 20s timer'
    filename = f'quiz_puntata{puntata}_misto'
    
    html = template.replace('{{PUNTATA_TITLE}}', title)
    html = html.replace('{{SUBTITLE}}', subtitle)
    html = html.replace('{{FILENAME}}', filename)
    html = html.replace('{{QUESTIONS_JSON}}', json.dumps(questions, ensure_ascii=False))
    html = html.replace('{{CATEGORY_BACKGROUNDS_JSON}}', json.dumps(backgrounds, ensure_ascii=True))
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    size_kb = os.path.getsize(output_path) // 1024
    print(f'Written {output_path} ({size_kb} KB)')

if __name__ == '__main__':
    puntata = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    build_html(puntata)
