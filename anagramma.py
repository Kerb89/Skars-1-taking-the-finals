from itertools import permutations
from collections import Counter

word = "precipitevolissimevolmente"
letters = Counter(word.replace(" ", "").lower())
print(f"Lettere in '{word}': {len(word)}")
print(f"Conteggio: {dict(letters)}")
print(f"Totale lettere: {sum(letters.values())}")

# Let's try to find anagram phrases manually by checking letter counts
# First, let's verify some candidate phrases

candidates = [
    "il mio speciale tormento si svelerà più vivo e mente",
    "vivo le mie estati più serene col mio sentimento pl",
    "completivist e impersonale me stesso ivi le nevi",
    "le mie poesie svelte ritmico in volto pensile ampi ve",
    "movimenti precisi le note più svelte a semicolpevoli",
    "semplicissimo le vetrine e poi le miti volteaven",
]

def check_anagram(phrase, original_counter):
    phrase_letters = Counter(phrase.replace(" ", "").replace(",", "").replace("'", "").replace("!", "").replace(".", "").replace("—", "").replace("-", "").lower())
    if phrase_letters == original_counter:
        return True, {}
    else:
        missing = original_counter - phrase_letters  # in original but not in phrase
        extra = phrase_letters - original_counter    # in phrase but not in original
        return False, {"missing": dict(missing), "extra": dict(extra)}

for c in candidates:
    result, diff = check_anagram(c, letters)
    if result:
        print(f"\n✅ ANAGRAMMA VALIDO: '{c}'")
    else:
        print(f"\n❌ '{c[:50]}...'")
        print(f"   Mancano: {diff['missing']}")
        print(f"   In più:  {diff['extra']}")

# Let's try a different approach - build phrases from the available letters
print("\n\n=== Tentativo manuale ===")
print(f"Lettere disponibili: {dict(letters)}")

# Try specific words and see what's left
def try_words(words, original_counter):
    remaining = original_counter.copy()
    for w in words:
        w_count = Counter(w.lower())
        remaining = remaining - w_count
        if any(v < 0 for v in remaining.values()):
            neg = {k: v for k, v in remaining.items() if v < 0}
            print(f"  ❌ Dopo '{w}': lettere mancanti {neg}")
            return None
    remaining = +remaining  # remove zero entries
    print(f"  Dopo {words}: restano {dict(remaining)} ({sum(remaining.values())} lettere)")
    return remaining

print("\nProva 1:")
try_words(["complessive", "impersonative"], letters)

print("\nProva 2:")
try_words(["semplicissime"], letters)

print("\nProva 3:")
try_words(["moltissime"], letters)

print("\nProva 4:")
try_words(["espressivo"], letters)

print("\nProva 5:")
try_words(["improvvise"], letters)

print("\nProva 6:")
try_words(["movimenti", "precisi"], letters)

print("\nProva 7:")
try_words(["televisione", "personale"], letters)

print("\nProva 8:")
try_words(["permissive", "completino"], letters)

print("\nProva 9:")
try_words(["televisione", "complessivi"], letters)

print("\nProva 10:")
try_words(["pellicoviste", "semprevivo"], letters)

print("\nProva 11:")
try_words(["volte", "permissive", "poi", "nel", "cielo", "miti"], letters)

print("\nProva 12:")
try_words(["meno", "prospettive", "li", "miscele", "vivo"], letters)

print("\nProva 13:")
try_words(["le", "mie", "prospettive", "sconvolgimenti"], letters)

print("\nProva 14:")
try_words(["polverose", "incivile", "tempiste", "molti"], letters)

print("\nProva 15:")
try_words(["vostri", "complessive", "imminente", "pile"], letters)
