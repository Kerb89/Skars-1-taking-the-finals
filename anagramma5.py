from collections import Counter

word = "precipitevolissimevolmente"
target = Counter(word.lower())

def is_perfect_anagram(words):
    combined = "".join(w.lower() for w in words)
    return Counter(combined) == target

# From the 180 results, the best Italian phrases that make grammatical sense:
best = [
    "Noi semplice impreviste volte",        # "Noi, semplice impreviste volte"
    "Le primitive complessive note",         # "Le primitive, complessive note"
    "Me complessive ripetitivo nel",         # weak
    "Mie impreviste sconvolte pile",         # "Mie impreviste sconvolte pile"
    "Ne implicito permessive volte",         # "Ne implicito, permessive volte"
    "Le complessive primitive note",         # "Le complessive, primitive note"
]

print("=== VERIFICA MIGLIORI FRASI ===\n")
for b in best:
    words = b.lower().split()
    print(f"  '{b}': {is_perfect_anagram(words)}")

# The best one grammatically is "Le primitive complessive note"
# meaning "The primitive, comprehensive notes" - it's valid Italian!

# But let me search for even better ones in the full 180 results
# by looking at the ones with "impreviste" or meaningful long words

# Let me also try 5-word combos with more meaningful structure
print("\n=== RICERCA FRASI CON SENSO ===\n")

def remaining_after(words):
    used = Counter("".join(w.lower() for w in words))
    r = target - used
    extra = used - target
    if extra:
        return None
    return +r

# Try building phrases that actually mean something in Italian
meaningful_attempts = [
    # "impreviste sconvolte" + something
    ["le", "mie", "impreviste", "sconvolte", "pile"],  # pile not great
    ["le", "mie", "impreviste", "sconvolte", "vite", "mopl"],
    # Checking "noi semplice impreviste volte"
    ["noi", "semplice", "impreviste", "volte"],
    # "le complessive primitive note" 
    ["le", "complessive", "primitive", "note"],
    # "imprevisto sconvolte pile lime e"
    ["imprevisto", "le", "semplice", "mie", "volte", "svn"],
    # Let me try with "percepimento" (14 letters!)
    # percepimento = p,e,r,c,e,p,i,m,e,n,t,o = p2,e3,r1,c1,i1,m1,n1,t1,o1 = 12 letters
    ["percepimento"],
    # remaining: e2,i3,t1,v2,o1,l2,s2,m1 = 14
    ["percepimento", "missili", "volte", "sve"],
    ["percepimento", "lo", "svesti", "missive", "li"],
    ["percepimento", "missive", "il", "volte", "si"],
    ["percepimento", "svestito", "le", "missili", "v"],
    # Try "primitivismo" = p,r,i,m,i,t,i,v,i,s,m,o = p1,r1,i4,m2,t1,v1,s1,o1 = 12 letters
    ["primitivismo"],
    # remaining: p1,e5,c1,t1,v1,o1,l2,s1,n1 = 13
    ["primitivismo", "le", "sconvolte", "pie"],  # sconvolte=s,c,o,n,v,o,l,t,e needs o2!
    ["primitivismo", "nel", "complesse", "vite"],
    # "complesse" = c,o,m,p,l,e,s,s,e = c1,o1,m1,p1,l1,e2,s2 = 9 
    # But after primitivismo: remaining p1,e5,c1,t1,v1,o1,l2,s1,n1
    # "complesse" needs s2 but only s1 left! no
    ["primitivismo", "svelto", "le", "piene", "c"],
    ["primitivismo", "le", "poesie", "svelton", "c"],
    ["primitivismo", "le", "esplicite", "svn", "oe"],
    # Let me check "completissime" = c,o,m,p,l,e,t,i,s,s,i,m,e = 13
    ["completissime"],
    # remaining: p1,r1,e2,i2,t1,v2,o1,l1,n1 = 11
    ["completissime", "le", "improvvise", "nto"],
    # "improvvise" needs v2,i2... after completissime: i2,v2 available!
    # improvvise = i,m,p,r,o,v,v,i,s,e = i2,m1,p1,r1,o1,v2,s1,e1 = 10
    # but after completissime remaining is: p1,r1,e2,i2,t1,v2,o1,l1,n1 = 11
    # improvvise needs m1 but m already used in completissime (m2 in target, m1 in completissime)
    # wait: completissime uses m2? c,o,m,p,l,e,t,i,s,s,i,m,e = m appears twice? no:
    # c-o-m-p-l-e-t-i-s-s-i-m-e = m appears at pos 3 and pos 12 = m2! 
    # So target m2 - completissime m2 = m0 left. improvvise needs m1. FAIL.
    ["completissime", "ripetitive", "l", "von"],
    # ripetitive = r,i,p,e,t,i,t,i,v,e = r1,i3,p1,e2,t2,v1 = 10
    # remaining after completissime: p1,r1,e2,i2,t1,v2,o1,l1,n1
    # ripetitive needs i3 but only i2 left! FAIL
    ["completissime", "primitive", "nel", "ov"],
    # primitive = p1,r1,i2,m1,t1,v1,e1 = 7... needs m1 but m0 left! FAIL
]

for t in meaningful_attempts:
    r = remaining_after(t)
    phrase = " ".join(t)
    if r is not None:
        left = sum(r.values())
        if left == 0:
            print(f"  ✅ {phrase}")
        elif left <= 5:
            print(f"  ~  {phrase} | restano {left}: {dict(r)}")

# The verified working ones from earlier search:
print("\n=== RISULTATI FINALI VERIFICATI ===\n")
finals = [
    "Le primitive complessive note",
    "Le complessive primitive note", 
    "Noi semplice impreviste volte",
    "Mie impreviste sconvolte pile",
]
for f in finals:
    words = f.split()
    print(f"  ✅ '{f}' = {is_perfect_anagram([w.lower() for w in words])}")
    # Count letters
    clean = f.replace(" ","").lower()
    print(f"     Lettere: {len(clean)} (target: 26)")
