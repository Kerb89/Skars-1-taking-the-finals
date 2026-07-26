#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_anagram_distrattori.py — Verifica che nessun distrattore di una domanda
anagrammi sia esso stesso un anagramma valido della parola sorgente.

Due modalità:
  1. CLI standalone:
       python check_anagram_distrattori.py SORGENTE DISTRATTORE1 DISTRATTORE2 DISTRATTORE3
     Exit 0 = PASS (nessun distrattore è anagramma della sorgente)
     Exit 1 = FAIL (almeno un distrattore è anagramma della sorgente)

  2. Importato come modulo da validate_quiz_html.py:
       from check_anagram_distrattori import check_anagram_distrattori
       risultati = check_anagram_distrattori(sorgente, distrattori)
       # risultati: lista di (distrattore, is_anagram: bool)

Logica: due stringhe sono anagrammi se, normalizzate (lowercase, spazi rimossi),
hanno esattamente le stesse lettere (stessa multiset di caratteri). Non serve
un dizionario: il problema è strutturale — se le lettere coincidono, la parola
È un anagramma della sorgente indipendentemente dal fatto che sia un lemma
attestato. Il quiz richiede che i distrattori NON siano anagrammi.
"""

import sys
import unicodedata


def _normalize(word: str) -> str:
    """Normalizza: lowercase, rimuovi spazi, normalizza Unicode (NFC)."""
    return unicodedata.normalize("NFC", word.replace(" ", "").lower())


def is_anagram(source: str, candidate: str) -> bool:
    """Ritorna True se candidate è un anagramma di source (stesse lettere)."""
    s = _normalize(source)
    c = _normalize(candidate)
    if len(s) != len(c):
        return False
    return sorted(s) == sorted(c)


def check_anagram_distrattori(sorgente: str, distrattori: list[str]) -> list[tuple[str, bool]]:
    """
    Controlla ogni distrattore contro la sorgente.
    Ritorna lista di tuple (distrattore, is_anagram).
    """
    risultati = []
    for d in distrattori:
        risultati.append((d, is_anagram(sorgente, d)))
    return risultati


def main():
    if len(sys.argv) < 3:
        print("Uso: python check_anagram_distrattori.py SORGENTE DISTRATTORE1 [DISTRATTORE2] [DISTRATTORE3]")
        print("Exit 0 = PASS, Exit 1 = FAIL (distrattore è anagramma della sorgente)")
        sys.exit(2)

    sorgente = sys.argv[1]
    distrattori = sys.argv[2:]

    risultati = check_anagram_distrattori(sorgente, distrattori)

    fail = False
    for d, is_anag in risultati:
        if is_anag:
            print(f"  FAIL: \"{d}\" è un anagramma di \"{sorgente}\" "
                  f"(lettere: {sorted(_normalize(sorgente))})")
            fail = True
        else:
            print(f"  OK:   \"{d}\" NON è un anagramma di \"{sorgente}\"")

    if fail:
        print(f"\nRISULTATO: FAIL — almeno un distrattore è anagramma di \"{sorgente}\"")
        sys.exit(1)
    else:
        print(f"\nRISULTATO: PASS — nessun distrattore è anagramma di \"{sorgente}\"")
        sys.exit(0)


if __name__ == "__main__":
    main()
