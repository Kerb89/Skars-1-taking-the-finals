from collections import Counter

word = "precipitevolissimevolmente"
letters = Counter(word.lower())

def check_anagram(phrase, original_counter):
    clean = phrase.replace(" ", "").replace(",", "").replace("'", "").replace("!", "").replace(".", "").replace("—", "").replace("-", "").replace("?", "").replace(";", "").replace("è", "e").replace("ì", "i").replace("ò", "o").lower()
    phrase_letters = Counter(clean)
    if phrase_letters == original_counter:
        return True, {}
    else:
        missing = original_counter - phrase_letters
        extra = phrase_letters - original_counter
        return False, {"missing": dict(missing), "extra": dict(extra), "phrase_len": len(clean), "orig_len": sum(original_counter.values())}

# Best candidates to verify and refine:
# 1. "il televisore mi spinse completivo" - "completivo" non è standard
# 2. "me prossime le vite svolte completi in" - troppo frammentata
# 3. "le televisioni compressive miti lop" - "lop" non è italiano

# Let me try to build really good phrases
print("=== FRASI CANDIDATE MIGLIORI ===\n")

def try_words(words, original_counter):
    remaining = original_counter.copy()
    for w in words:
        clean_w = w.replace("'", "").replace(",", "").replace("!", "").replace(".", "").lower()
        w_count = Counter(clean_w)
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

# Let me think about this more carefully
# p2, r1, e5, c1, i4, t2, v2, o2, l2, s2, m2, n1

# "il televisore" = i,l,t,e,l,e,v,i,s,o,r,e = i2,l2,t1,e3,v1,s1,o1,r1 = 12 lettere
# remaining: p2, e2, c1, i2, t1, v1, o1, s1, m2, n1 = 13 lettere

# "il televisore" + "mi" = remaining: p2, e2, c1, i1, t1, v1, o1, s1, m1, n1 = 11
# "il televisore mi" + "componesti" = c,o,m,p,o,n,e,s,t,i = c1,o2,m1,p1,n1,e1,s1,t1,i1 = 10
# remaining: p1, e1, v1 = 3 lettere: "pev" "vep"... not great

# "il televisore mi" + "compiste" = c,o,m,p,i,s,t,e = 8 
# remaining: p1, e1, i0... wait "compiste" non esiste

# Let's try "il televisore mi scompone" = ...
# "scompone" = s,c,o,m,p,o,n,e = s1,c1,o2,m1,p1,n1,e1 = 8
# remaining after "il televisore mi scompone": p1, e1, i1, t1, v1 = 5: "pivet" "vipet"... 
# "vipet" non funziona

# "il televisore mi" + "coinvolse" = c,o,i,n,v,o,l,s,e... wait needs 2 o and I only have 1 o left
# After "il televisore mi": p2, e2, c1, i1, t1, v1, o1, s1, m1, n1

# "il televisore mi" + "sconvesti" = s,c,o,n,v,e,s,t,i = needs s2 but only s1 left... no

# "il televisore mi" + "competitivi" = needs 2 i but only 1 left... hmm
# c,o,m,p,e,t,i,t,i,v,i = c1,o1,m1,p1,e1,t2,i3,v1 = needs i3 but only i1 left

# Try different start
# "il mio televisore" = i,l,m,i,o,t,e,l,e,v,i,s,o,r,e = i3,l2,m1,o2,t1,e3,v1,s1,r1 = 15
# remaining: p2, e2, c1, i1, t1, v1, s1, m1, n1 = 10

# "il mio televisore" + "increspò" - no accento, and needs ò
# "il mio televisore" + "semplici" = s,e,m,p,l,i,c,i = s1,e1,m1,p1,l1,i2,c1 = 8
# needs l1 but I have l0 left! (l2 used in "televisore" + "il")
# Wait: "il" = i,l and "televisore" = t,e,l,e,v,i,s,o,r,e has l1
# so "il televisore" uses l2, "mio" uses m1,i1,o1
# Total "il mio televisore" = i(2+1)=3, l2, m1, o(1+1)=2, t1, e3, v1, s1, r1
# remaining from p2,r1,e5,c1,i4,t2,v2,o2,l2,s2,m2,n1:
#   p2, r0, e2, c1, i1, t1, v1, o0, l0, s1, m1, n1 = 10

# OK this approach is getting complex. Let me just try more combinations programmatically

tests = [
    # Frasi che hanno senso in italiano (o quasi)
    ("il televisore mi scompisse le volte pn", ["il", "televisore", "mi", "scompisse", "le", "volte", "pn"]),
    ("miti lo svelino le promesse eccessive", ["miti", "lo", "svelino", "le", "promesse", "eccessive"]),
    ("mi si rivelo nei complessi movimenti pelte", ["mi", "si", "rivelo", "nei", "complessi", "movimenti", "pelte"]),
    ("è il mio testo; prevelsivo semicomplessive", ["e", "il", "mio", "testo", "prevelsivo", "semicomplessive"]),
]

for desc, words in tests:
    result, msg = try_words(words, letters)
    print(f"  {desc}: {msg}")

# Let me try with a more systematic approach
# I'll pick phrases that actually make sense
print("\n=== Tentativi con senso ===\n")

sense_tests = [
    ["movimenti", "precisi", "le", "svolte", "pe"],  # 26 ✓ but "pe" not word
    ["movimenti", "precisi", "pe", "le", "svolte"],  # same
    ["mi", "risolvete", "il", "complesso", "intime", "pev"],
    ["svelti", "movimenti", "percepisco", "il", "seme"],  # 
    ["il", "percepimento", "si", "svolse", "mite", "lvi"],
    ["percepimento", "si", "svolse", "mite", "il", "lv"],
    ["le", "mie", "poesie", "svelte", "ritmico", "pn", "lsv"],
    ["percepisco", "il", "sentimento", "svelo", "le", "miv"],
    ["le", "mie", "vesti", "complessivo", "impertinente"],  # might be too many
    ["svelti", "come", "missili", "le", "note", "previste", "ipo"],
    ["le", "mie", "viste", "complessivo", "pert", "menti"],
    ["le", "prospettive", "me", "si", "coinvolgimenti"],  # 
    ["movimenti", "svelti", "per", "le", "poesie", "cosm"],
    ["nel", "mio", "percepirle", "vistose", "smile", "tv"],  # 
    ["il", "percepirle", "vistose", "nel", "mio", "stemm"],
    ["il", "percepimento", "rivissole", "svolte", "lemm"],
    ["il", "sentimento", "mi", "svelò", "precise", "volte"],  # svelò needs ò
    # without accents:
    ["il", "sentimento", "mi", "svelino", "precise", "volte", "m"],
    ["semplice", "il", "mio", "sentire", "volte", "vispe", "mn"],
    ["svelto", "me", "il", "percepimento", "si", "sveli", "no"],
    # This might work well as a phrase if letters match
    ["me", "le", "promesse", "vili", "coi", "sentimenti", "pv"],
]

for t in sense_tests:
    result, msg = try_words(t, letters)
    phrase = " ".join(t)
    if "PERFETTO" in msg or "Restano" in msg:
        print(f"  {phrase}: {msg}")

# Final approach - verified working combos from before, make them into real phrases
print("\n=== Verifica combo funzionanti ===\n")

# From earlier: "volte permissive poi nel cielo miti" was marked perfect by try_words
# Let me double check these against the actual check_anagram function

final_checks = [
    "volte permissive poi nel cielo miti",
    "mi risolvete il complesso nevi piemonte", 
    "le miti prospettive miniscole evo",
    "il televisore mi spinse completivo",
    "nel tempo rivisito semplice le mosse iv",
    "me prossime le vite svolte completi in",
]

for f in final_checks:
    result, diff = check_anagram(f, letters)
    if result:
        print(f"  ✅ '{f}' - ANAGRAMMA PERFETTO")
    else:
        print(f"  ❌ '{f}' - {diff}")

# Now let me also try to find Italian-sounding phrases
print("\n=== Combo buone da rifinire ===\n")

# "il televisore mi spinse completivo" - 
# "completivo" potrebbe non essere standard, proviamo varianti
# After "il televisore mi spinse": 
r, msg = try_words(["il", "televisore", "mi", "spinse"], letters)
print(f"Dopo 'il televisore mi spinse': {msg}")
# completivo = c,o,m,p,l,e,t,i,v,o

# After "il televisore mi": p2, e2, c1, i1, t1, v1, o1, s1, m1, n1
r, msg = try_words(["il", "televisore", "mi"], letters)
print(f"Dopo 'il televisore mi': {msg}")

# 11 letters: p2, e2, c1, i1, t1, v1, o1, s1, m1, n1
# "sconvesti" doesn't exist... "competitivi" needs too many i
# "coinvolse" needs 2 o... "sconpite" no... 
# "investì" needs ì... 
# "scompensi" = s,c,o,m,p,e,n,s,i = needs s2, only s1 left
# "coinvesti" = c,o,i,n,v,e,s,t,i = c1,o1,i1,n1,v1,e1,s1,t1,i1 = uses i2 but only i1!
# Hmm... 
# "mi" already used 1 i, so remaining: i1
# "competì" = c,o,m,p,e,t,i (with ì but we treat as i) = 7
# remaining: p1, e1, s1, v1, n1 = 5: "svpen" "pensv"... no

# Let me try "il mio televisore"
r, msg = try_words(["il", "mio", "televisore"], letters)
print(f"Dopo 'il mio televisore': {msg}")
# remaining: p2, e2, c1, i1, t1, v1, s1, m1, n1 = 10

# "in" + "competitivi" -> no, needs too many i
# "smentisce" = s,m,e,n,t,i,s,c,e = s2,m1,e2,n1,t1,i1,c1 = 9 
# remaining: p2, v1 = 3: "pvv" no, only v1... "pv" = 2 letters but remaining is p2,v1 = 3
# wait: p2,e2,c1,i1,t1,v1,s1,m1,n1 = 10
# "smentisce" uses s2(need s1 only have s1)... nope

# "mi coinvolse" = m,i,c,o,i,n,v,o,l,s,e... needs o2 but 0 left after "il mio televisore"

# OK let me try with simpler, common words
# "le" "spie" "visive" "contempli" "mescolino" "stri"

# Actually, from the earlier results, these work:
# "volte permissive poi nel cielo miti" - all real words! Let me verify sense
# volte=times, permissive=permissive, poi=then, nel=in the, cielo=sky, miti=myths/mild
# "Volte permissive, poi nel cielo miti" = "Permissive times, then in the sky myths" - poetic!

# "mi risolvete il complesso nevi piemonte" - hmm "nevi" is ok but "piemonte" might not fit
# Actually wait - earlier this was marked PERFETTO. But is "piemonte" valid?
# It's a proper noun (region). The phrase would be "mi risolvete il complesso nevi Piemonte"
# = "solve me the complex snows Piemonte" - not great

# Let me verify the best one
print("\n=== VERIFICA FINALE ===\n")
result, diff = check_anagram("Volte permissive poi nel cielo miti", letters)
print(f"'Volte permissive, poi nel cielo miti': {'✅' if result else '❌'} {diff}")

# Hmm wait - first script said 30 letters for this phrase. Let me recount
test_phrase = "voltepermissiveipoinelcielomiti"
print(f"Lettere nella frase: {len(test_phrase)}")
# That's 30... but try_words said it was perfect. There's a bug - try_words uses subtraction
# which can go negative! Let me fix this.

# Actually Counter subtraction: Counter({'a':3}) - Counter({'a':5}) = Counter() (drops negative)
# So try_words could show "0 remaining" even if phrase has MORE letters than original!
# That's the bug. Let me fix and re-verify.

def try_words_strict(words, original_counter):
    """Strict version that also checks total letter count"""
    phrase = "".join(words).lower()
    phrase_counter = Counter(phrase)
    if phrase_counter == original_counter:
        return True, "✅ PERFETTO!"
    else:
        missing = original_counter - phrase_counter
        extra = phrase_counter - original_counter
        return False, f"Mancano: {dict(missing)}, Extra: {dict(extra)}"

print("\n=== RE-VERIFICA STRETTA ===\n")
recheck = [
    ["volte", "permissive", "poi", "nel", "cielo", "miti"],
    ["mi", "risolvete", "il", "complesso", "nevi", "piemonte"],
    ["le", "miti", "prospettive", "miniscole", "evo"],
    ["il", "televisore", "mi", "spinse", "completivo"],
    ["nel", "tempo", "rivisito", "semplice", "le", "mosse", "iv"],
    ["me", "prossime", "le", "vite", "svolte", "completi", "in"],
    ["movimenti", "precisi", "le", "svolte", "pe"],
    ["semplice", "televisori", "competitivi", "mn", "sol"],
]

for t in recheck:
    result, msg = try_words_strict(t, letters)
    phrase = " ".join(t)
    print(f"  {phrase}: {msg}")
