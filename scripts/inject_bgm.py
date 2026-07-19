"""Inject BGM base64 into quiz HTML files, replacing {{BGM_BASE64}} placeholder."""
import sys
import os

def inject(html_path, b64_path):
    with open(b64_path, 'r') as f:
        bgm_b64 = f.read().strip()

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    placeholder = '"{{BGM_BASE64}}"'
    if placeholder not in content:
        print(f'SKIP: placeholder non trovato in {html_path}')
        return False

    content = content.replace(placeholder, '"' + bgm_b64 + '"')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'OK: BGM iniettata in {os.path.basename(html_path)} ({len(bgm_b64)} chars)')
    return True

if __name__ == '__main__':
    b64_file = r'background_music\trivia_tension_b64.txt'
    targets = sys.argv[1:] if len(sys.argv) > 1 else [r'puntate\quiz_puntata31_misto.html']
    for t in targets:
        inject(t, b64_file)
