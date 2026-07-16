"""
check_steering.py — Verifica integrità strutturale della directory .kiro/steering.

Controlla:
1. Esattamente UN file *workflow* nella steering
2. Tutti i cross-ref citati nei file steering e hook risolvono a file esistenti
3. Frontmatter 'inclusion' presente in tutti i file steering
4. Nessun file di conflitto OneDrive (Copia, conflict, Copy)

Exit code 0 = tutto ok, 1 = errori trovati.
Eseguire a inizio sessione e dopo ogni intervento sulla struttura.
"""

import os
import re
import sys

KIRO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".kiro")
STEERING_DIR = os.path.join(KIRO_DIR, "steering")
HOOKS_DIR = os.path.join(KIRO_DIR, "hooks")
AGENTS_DIR = os.path.join(KIRO_DIR, "agents")

errors = []


def check_single_workflow():
    """Esattamente un file workflow nella steering."""
    workflow_files = [f for f in os.listdir(STEERING_DIR) if "workflow" in f.lower()]
    if len(workflow_files) == 0:
        errors.append("ERRORE: nessun file workflow trovato in steering/")
    elif len(workflow_files) > 1:
        errors.append(f"ERRORE: {len(workflow_files)} file workflow trovati (deve essere 1): {workflow_files}")
    else:
        print(f"  OK: workflow unico -> {workflow_files[0]}")


def check_cross_refs():
    """Tutti i riferimenti a file quizzone-XX-* nei file steering e hook risolvono."""
    # Pattern: quizzone-NN-nome (con o senza estensione)
    ref_pattern = re.compile(r'quizzone-\d+-[\w-]+')

    # Mappa dei file steering esistenti (senza estensione)
    existing_stems = set()
    for f in os.listdir(STEERING_DIR):
        if f.endswith(".md"):
            existing_stems.add(f.replace(".md", ""))

    # Cerca cross-ref in steering
    dirs_to_check = []
    if os.path.isdir(STEERING_DIR):
        dirs_to_check.append(("steering", STEERING_DIR, "*.md"))
    if os.path.isdir(HOOKS_DIR):
        dirs_to_check.append(("hooks", HOOKS_DIR, "*.hook"))

    for label, directory, _ in dirs_to_check:
        for fname in os.listdir(directory):
            fpath = os.path.join(directory, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                content = open(fpath, "r", encoding="utf-8").read()
            except Exception:
                continue
            refs = ref_pattern.findall(content)
            for ref in refs:
                # Normalizza: rimuovi eventuale .md finale
                ref_clean = ref.replace(".md", "")
                if ref_clean not in existing_stems:
                    errors.append(f"ERRORE: {label}/{fname} cita '{ref}' ma il file non esiste in steering/")


def check_frontmatter():
    """Ogni file steering deve avere frontmatter con 'inclusion'."""
    for fname in os.listdir(STEERING_DIR):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(STEERING_DIR, fname)
        try:
            content = open(fpath, "r", encoding="utf-8").read()
        except Exception:
            continue
        if not content.startswith("---"):
            errors.append(f"ERRORE: {fname} manca il frontmatter (deve iniziare con ---)")
        elif "inclusion:" not in content.split("---")[1] if content.count("---") >= 2 else "":
            errors.append(f"ERRORE: {fname} manca 'inclusion:' nel frontmatter")


def check_conflict_files():
    """Nessun file di conflitto OneDrive/sync."""
    conflict_pattern = re.compile(r'(Copia|conflict|Copy|\(\d+\))', re.IGNORECASE)
    for root, dirs, files in os.walk(KIRO_DIR):
        # Skip .git
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if conflict_pattern.search(f):
                errors.append(f"ERRORE: file di conflitto trovato: {os.path.join(root, f)}")


def main():
    print("=== check_steering.py ===\n")

    if not os.path.isdir(STEERING_DIR):
        print(f"FATALE: directory {STEERING_DIR} non trovata")
        sys.exit(1)

    print("[1] Workflow unico:")
    check_single_workflow()

    print("\n[2] Cross-ref:")
    check_cross_refs()

    print("\n[3] Frontmatter:")
    check_frontmatter()

    print("\n[4] File di conflitto:")
    check_conflict_files()

    print("\n" + "=" * 40)
    if errors:
        print(f"\n{len(errors)} ERRORI TROVATI:\n")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("\nTutto OK.")
        sys.exit(0)


if __name__ == "__main__":
    main()
