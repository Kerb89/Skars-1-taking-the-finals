from collections import Counter

word = "precipitevolissimevolmente"
letters = Counter(word.lower())

def check_anagram(phrase, original_counter):
    clean = phrase.replace(" ", "").replace(",", "").replace("'", "").replace("!", "").replace(".", "").replace("—", "").replace("-", "").replace("?", "").replace(";", "").lower()
    phrase_letters = Counter(clean)
    if phrase_letters == original_counter:
        return True, {}
    else:
        missing = original_counter - phrase_letters
        extra = phrase_letters - original_counter
        return False, {"missing": dict(missing), "extra": dict(extra), "phrase_len": len(clean), "orig_len": sum(original_counter.values())}

# Le prove 11-15 hanno 0 lettere restanti, verifichiamo che siano anagrammi perfetti
# Ma devo controllare che le parole esistano davvero in italiano

# Prova 11: volte, permissive, poi, nel, cielo, miti
# "permissive" esiste, "volte" esiste, "poi" esiste, "nel" esiste, "cielo" esiste, "miti" esiste
# Frase: "Volte permissive poi nel cielo miti" - grammaticalmente debole ma tutte parole reali

# Prova 12: meno, prospettive, li, miscele, vivo  
# "prospettive" esiste, "meno" esiste, "li" esiste, "miscele" esiste, "vivo" esiste
# Frase: "Meno prospettive, li miscele vivo" - debole

# Prova 14: polverose, incivile, tempiste, molti
# "polverose" esiste, "incivile" esiste, "tempiste" - non standard, "molti" esiste

# Proviamo frasi più sensate
print("=== Verifica frasi sensate ===\n")

phrases = [
    "Volte permissive poi nel cielo miti",
    "Meno prospettive li miscele vivo",
    "Ci svelo le mie prospettive miti nel", 
    "le miti prospettive ci svelo nel vime",
    "nel cielo miti poi sveleresti vivismo e mp",  
    "mi evolvessi inomplete ipertesti lm",
    "nel complesso ritmivi le poesie più menti va",
]

for p in phrases:
    result, diff = check_anagram(p, letters)
    if result:
        print(f"✅ '{p}'")
    else:
        print(f"❌ '{p}' | diff: {diff}")

# Better approach: try building valid Italian phrases
print("\n=== Approccio sistematico ===\n")

def try_words(words, original_counter):
    remaining = original_counter.copy()
    for w in words:
        w_count = Counter(w.lower())
        remaining = remaining - w_count
        if any(v < 0 for v in remaining.values()):
            neg = {k: v for k, v in remaining.items() if v < 0}
            return None, f"❌ dopo '{w}': eccesso {neg}"
    remaining = +remaining
    left = sum(remaining.values())
    if left == 0:
        return True, "✅ PERFETTO!"
    else:
        return remaining, f"Restano {left} lettere: {dict(remaining)}"

# Let me try with real Italian words to build meaningful phrases
tests = [
    # "nel complesso" = nel complesso -> n,e,l,c,o,m,p,l,e,s,s,o = needs 2 o, 2 l, 2 s, 2 e -> ok
    ["nel", "complesso", "primitive", "misive", "it"],
    ["mi", "risolvete", "il", "complesso", "nevi", "piemonte"],  
    ["le", "miti", "prospettive", "miniscole", "evo"],
    ["il", "nome", "semplice", "si", "estrovertì", "poi", "vm"],
    ["mescolerei", "vistosità", "il", "pennello", "vip", "time", "ss"],
    # Try: "vive le più complessive tormentose ipi sin"
    ["nel", "vostri", "complessive", "imminente", "pile"],
    # Prova con parole comuni italiane
    ["volte", "mi", "perse", "il", "viso", "completine", "sm"],
    ["le", "mie", "volte", "precisi", "movimenti", "lops"],
    ["movimenti", "precisi", "svelo", "le", "più", "tant"],
    # Check: movimenti precisi svelo le pt
    ["movimenti", "precisi", "le", "svelo", "pt"],
    ["movimenti", "precisi", "le", "epos", "tv", "l"],
    ["movimenti", "precisi", "le", "volte", "ps"],
    ["movimenti", "precisi", "le", "stovl", "ep"],
    ["movimenti", "precisi", "svelto", "le", "pl"],
    ["movimenti", "precisi", "le", "svolte", "p"],
]

for t in tests:
    result, msg = try_words(t, letters)
    phrase = " ".join(t)
    print(f"  {phrase}: {msg}")

print("\n=== Da 'movimenti precisi le svolte p' ===")
# movimenti precisi uses: m,o,v,i,m,e,n,t,i,p,r,e,c,i,s,i = 16
# remaining from original 26 letters: p,e,e,e,t,v,o,l,l,s = 10
# "le svolte p" = l,e,s,v,o,l,t,e,p = 9 letters... need 10
# Let me recount
r = try_words(["movimenti", "precisi"], letters)
print(f"Dopo 'movimenti precisi': {r}")

# remaining: p,e,e,e,t,v,o,l,l,s = p1,e3,t1,v1,o1,l2,s1 = 10
# "svelto" = s,v,e,l,t,o = uses s1,v1,e1,l1,t1,o1 -> remaining: e2, l1, p1 = 4 letters: "elpe" "pele" "lep e"
r2 = try_words(["movimenti", "precisi", "svelto"], letters)
print(f"Dopo 'movimenti precisi svelto': {r2}")

# remaining e2, l1, p1 -> "pelle" no needs 2 l... "le pe" -> "le" + "pe"? 
# How about "le più"? le = l,e ; più = p,i,ù -> no, ù not available
# "pelle" = p,e,l,l,e -> p1,e2,l2 = 5 letters but I have p1,e2,l1 = 4... missing one l
# "elep" "peel" 

r3 = try_words(["movimenti", "precisi", "svelto", "le", "pe"], letters)
print(f"Dopo 'movimenti precisi svelto le pe': {r3}")

# pe isn't a word. Let's try different combos for those last 10 letters (p,e,e,e,t,v,o,l,l,s)
# "estoll" no, "stolle" no, "svelto" + "pelle" = s,v,e,l,t,o,p,e,l,l,e -> needs 2e extra and 1l extra
# "spolvete" = no  
# "le poste" + "lv" no
# "le volte" + "sp" no wait: l,e,v,o,l,t,e = 7, remaining s,p,e = 3
r4 = try_words(["movimenti", "precisi", "le", "volte", "spe"], letters)
print(f"Dopo 'movimenti precisi le volte spe': {r4}")

# "le volte" uses l,e,v,o,l,t,e = l2,e2,v1,o1,t1 = 7
# from 10 (p1,e3,t1,v1,o1,l2,s1): remaining p1,e1,s1 = 3 -> "pes" "sep" "spe"
# "le spot" + "ve" + ...
# "lo svelte" ? l,o,s,v,e,l,t,e = l2,o1,s1,v1,e2,t1 = 8, remaining p1,e1 = "pe" 
r5 = try_words(["movimenti", "precisi", "lo", "svelte", "pe"], letters)
print(f"Dopo 'movimenti precisi lo svelte pe': {r5}")

# Hmm "pe" isn't a word. Let's try "svelte" differently
# from the 10: p,e,e,e,t,v,o,l,l,s
# "pesto" = p,e,s,t,o = 5, remaining: e2,v1,l2 = "elle v" "velle" = 5 
r6 = try_words(["movimenti", "precisi", "pesto", "velle"], letters)
print(f"Dopo 'movimenti precisi pesto velle': {r6}")

# "velle" non è italiano standard. 
# "pesto" + "le" + "lev" ?  
# "evo" = e,v,o = 3, remaining p,e,e,t,l,l,s = 7: "pestelli" no too many, "stelline" no
# OK different track.

# Let me try: "le veloci semi improvviste penne it" no, rethink entirely

# Actually let me just try to find good combos from scratch
print("\n=== Ricerca frasi di senso compiuto ===\n")

# Available: p2, r1, e5, c1, i4, t2, v2, o2, l2, s2, m2, n1  (26 total)

good_tests = [
    # "sole" "complessive" "ipertimismo" "nv" 
    ["il", "mio", "sentire", "eccessivo", "plm", "prevlt"],
    ["vive", "le", "promesse", "siti", "collettivi", "minp"],
    ["me", "lo", "si", "promise", "il", "completive", "stivn"],
    ["promise", "il", "completive"], # check
    ["le", "televisioni", "compressive", "miti", "lop"],
    ["televisioni", "compressive"],  # check how many letters
    ["il", "televisore", "mi", "spinse", "completivo"],
    ["televisore", "completissimi", "ve", "pin"],
    ["semplicissime", "televisor"], # non esiste
    ["semplice", "televisori", "competitivi", "mn", "sol"],
    ["televisori", "semplice"],  # check  
    ["le", "televisioni", "semplici", "come", "per", "stivt"],
    ["me", "prossime", "le", "vite", "svolte", "completi", "in"],
    ["le", "mie", "prossime", "vite", "completino", "slv"],
    ["nel", "tempo", "rivisito", "semplice", "le", "mosse", "iv"],
    ["risolvete", "il", "mio", "complesso", "più", "intente"],
]

for t in good_tests:
    result, msg = try_words(t, letters)
    phrase = " ".join(t)
    print(f"  {phrase}: {msg}")
