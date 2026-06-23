from collections import Counter
from itertools import combinations

word = "precipitevolissimevolmente"
target = Counter(word.lower())
target_total = sum(target.values())  # 26

def is_perfect_anagram(words):
    combined = "".join(w.lower() for w in words)
    return Counter(combined) == target

def remaining_after(words):
    used = Counter("".join(w.lower() for w in words))
    r = target - used
    extra = used - target
    if extra:
        return None  # exceeded
    return +r

# Italian word list - common real words that use our available letters
# Available: p2, r1, e5, c1, i4, t2, v2, o2, l2, s2, m2, n1

# Build from known-good combo: "movimenti precisi le svolte pe"
# Need to replace "pe" with something using p,e that's a real word
# There's no 2-letter Italian word "pe"... 
# But we can restructure: instead of "svolte" use "svelte" and have "po" left? 
# "svelte" = s,v,e,l,t,e needs e2 but after movimenti+precisi we have e3,l2,p1,t1,v1,o1,s1
# "svelte" uses s1,v1,e2,l1,t1 = ok! remaining: e1,l1,p1,o1 = "pole" or "pelo"!

test1 = ["movimenti", "precisi", "svelte", "polo", "e"]
# wait: polo = p,o,l,o needs o2 but only o1 left

# After movimenti,precisi: p1,e3,t1,v1,o1,l2,s1 = 10
# "le svolte" = l,e,s,v,o,l,t,e uses l2,e2,s1,v1,o1,t1 = 8, remaining: p1,e1 = "pe" ugh
# "svelte" = s,v,e,l,t,e uses s1,v1,e2,l1,t1 = 6, remaining: p1,e1,o1,l1 = "pole" "pelo" "olpe"
# "pelo" = p,e,l,o = 4! That works!

test2 = ["movimenti", "precisi", "svelte", "pelo"]
print("Test 'movimenti precisi svelte pelo':", is_perfect_anagram(test2))

# "pelo" is a real Italian word (hair/fur)! 
# "Movimenti precisi, svelte pelo" - doesn't make great sense but all words are real

# Let's try more meaningful combos
# After movimenti,precisi: p1,e3,t1,v1,o1,l2,s1 = 10
# "le poste" = l,e,p,o,s,t,e = 7, remaining: v1,e1,l1 = "vel" - not a word
# "lo stile" = l,o,s,t,i,l,e - needs i1 but 0 left! no
# "le volte" = l,e,v,o,l,t,e = l2,e2,v1,o1,t1 = 7, remaining: p1,e1,s1 = "pes" "sep" "spe"
# "lo svelo" = l,o,s,v,e,l,o needs o2 but only o1

# Try different base words
# "semplici" = s,e,m,p,l,i,c,i = s1,e1,m1,p1,l1,i2,c1 = 8
# remaining from target: p1,r1,e4,i2,t2,v2,o2,l1,s1,m1,n1 = 16

# "semplici movimenti" = adds m,o,v,i,m,e,n,t,i = 9
# remaining: p1,r1,e3,i0... wait i: target has i4, semplici uses i2, movimenti uses i2 = i4 ok
# remaining: p1,r1,e3,t1,v1,o1,l1,s1 = 10

# "semplici movimenti" + "le svolte" needs l2 but only l1
# + "perverts" no
# + "lo sverte" no
# + "le sorte" = l,e,s,o,r,t,e = 7, remaining: p1,e1,v1,l0... needs l0 wait
# After "semplici movimenti": p1,r1,e3,t1,v1,o1,l1,s1 = 10
# "le sorte" = l1,e2,s1,o1,r1,t1 = 7 letters using l1,e2,s1,o1,r1,t1
# remaining: p1,e1,v1 = 3: "pev" "vep"... 

# "semplici movimenti" + "per" = p1,e1,r1 = 3, remaining: e2,t1,v1,o1,l1,s1 = 7
# + "le svolte" needs l2, only l1... 
# + "svelte" = s1,v1,e2,l1,t1 = 6, remaining: o1 = "o" (valid Italian word! = "or/oh")
# "semplici movimenti per svelte o" - hmm "o" alone is weird

# Actually: "o" is a valid Italian conjunction meaning "or"
test3 = ["semplici", "movimenti", "per", "svelte", "o"]
print("Test 'semplici movimenti per svelte o':", is_perfect_anagram(test3))
# Phrase: "Semplici movimenti per svelte o..." - not great

# Try yet another approach with longer words
# "complessivo" = c,o,m,p,l,e,s,s,i,v,o = c1,o2,m1,p1,l1,e1,s2,i1,v1 = 11
# remaining: p1,r1,e4,i3,t2,v1,l1,m1,n1 = 15

# "complessivo" + "imperitive" - not standard
# "complessivo" + "intermetipi" - no
# "complessivo" + "ripetimenti" = r1,i3,p1,e2,t2,m1,n1 = 11... 
# Check: r1+i3+p1+e2+t2+m1+n1+l0 = 11, but remaining is 15 and has l1 left
# So remaining after "complessivo ripetimenti" = e2,l1,v1 = 4: "velle" needs 2 l... "elve" "leve"
# "leve" = l1,e2,v1 = 4! "leve" = levers/light (adjective plural) - valid!

test4 = ["complessivo", "ripetimenti", "leve"]
print("Test 'complessivo ripetimenti leve':", is_perfect_anagram(test4))
# But is "ripetimenti" a real word? Not standard - "ripetizioni" is.

# "complessivi" = c,o,m,p,l,e,s,s,i,v,i = c1,o1,m1,p1,l1,e1,s2,i2,v1 = 11
# remaining: p1,r1,e4,i2,t2,v1,o1,l1,m1,n1 = 14

# "complessivi" + "e" + "ripetitivo" = r1,i3,p1,e2,t2,v1,o1 = 11
# Hmm i: need i3 but only i2 left... nope

# "espressivi" - needs r1,s2 - wait s: target has s2, but "complessivi" already uses s2
# So no more s available after complessivi

# Let me try: "improvvise" - no, needs 2 v... wait target has v2
# "improvvise" = i,m,p,r,o,v,v,i,s,e = i2,m1,p1,r1,o1,v2,s1,e1 = 10
# remaining: p1,e4,c1,i2,t2,o1,l2,s1,m1,n1 = 15
# That's a lot of letters left but at least "improvvise" uses v2

# "improvvise" + "completi" = c1,o1,m1,p1,l1,e1,t1,i1 = 8
# remaining: e3,i1,t1,l1,s1,n1 = 8

# "improvvise completi" + "instille" = i1,n1,s1,t1,i1,l1,l1,e1 needs i2 but only i1!
# + "le stile" needs i1... 
# + "sentile" = s1,e1,n1,t1,i1,l1,e1 = 7 uses e2... remaining: e1 = "e" 
# "improvvise completi sentile e" - "sentile" isn't standard

# OK let me try a totally different approach - use a word list
print("\n=== APPROCCIO CON PAROLE VERIFICATE ===\n")

# Real Italian words I can form from subsets of p2,r1,e5,c1,i4,t2,v2,o2,l2,s2,m2,n1:
good_words = [
    "movimenti",   # m1,o1,v1,i2,e1,n1,t1 = 7 unique, 9 letters
    "semplice",    # s1,e2,m1,p1,l1,i1,c1 = 8 letters  
    "complessive", # c1,o1,m1,p1,l1,e2,s2,i1,v1 = 10... wait
    "viste",       # v1,i1,s1,t1,e1 = 5
    "il",          # i1,l1 = 2
    "lo",          # l1,o1 = 2
    "le",          # l1,e1 = 2
    "per",         # p1,e1,r1 = 3
    "ore",         # o1,r1,e1 = 3
    "nel",         # n1,e1,l1 = 3
    "voi",         # v1,o1,i1 = 3  
    "mie",         # m1,i1,e1 = 3
    "sei",         # s1,e1,i1 = 3
    "tre",         # t1,r1,e1 = 3
    "me",          # m1,e1 = 2
    "vi",          # v1,i1 = 2
    "si",          # s1,i1 = 2
    "se",          # s1,e1 = 2
    "in",          # i1,n1 = 2
    "poi",         # p1,o1,i1 = 3
    "pile",        # p1,i1,l1,e1 = 4
    "mite",        # m1,i1,t1,e1 = 4
    "vile",        # v1,i1,l1,e1 = 4
    "olivo",       # o2,l1,i1,v1 = 5 - wait needs o2
    "spesso",      # needs s3... no
]

# Let me try a completely different approach - search for known anagrams online
# or just grind through combos that make sense

# Key insight: I need EXACTLY these letters: p2,r1,e5,c1,i4,t2,v2,o2,l2,s2,m2,n1
# Let me try building from "complessivi" or "complessive" type words

# "te lo promise vivi nel cielo estivo pm" - let me check
test5 = ["te", "lo", "promise", "vivi", "nel", "cielo", "estivo", "pm"]
r = remaining_after(test5)
print(f"'te lo promise vivi nel cielo estivo pm': remaining={r}")

# Let me try to just find any valid anagram with all real words
# Strategy: use 2-3 long words + short connectors

# "complessivo" (11) + remaining 15 letters
# Actually let me recount: c,o,m,p,l,e,s,s,i,v,o = 11 letters
# p2r1e5c1i4t2v2o2l2s2m2n1 - c1o2m1p1l1e1s2i1v1o(already counted) 
# Hmm "complessivo" uses: c1,o2,m1,p1,l1,e1,s2,i1,v1 = uses o2 (both o's!)
# remaining: p1,r1,e4,i3,t2,v1,l1,m1,n1 = 15 letters
# That's still a lot. Let me use it + a long word

# "primitive" = p1,r1,i2,m1,t1,v1,e1 = 7 (but is it Italian? "primitivo/a" yes, "primitive" = f.pl.)
# remaining after complessivo+primitive: e3,i1,t1,l1,n1 = 7
# "lentine" = no... "intele" no... "le notti" needs o... 
# "le tini" = l1,e1,t1,i1,n1,i1 needs i2 but only i1... 
# "linee" = l1,i1,n1,e2 = 5, remaining: t1,e1,i0... needs i0 but "linee" needs i1 which we have!
# After complessivo+primitive: e3,i1,t1,l1,n1
# "linee" uses l1,i1,n1,e2 = 5, remaining: e1,t1 = "te" or "et"
# "te" is Italian! (you, to you)

test6 = ["complessivo", "primitive", "linee", "te"]
print(f"'complessivo primitive linee te': {is_perfect_anagram(test6)}")
# "Complessivo, primitive linee te" - a bit odd but grammatically possible
# "Te, linee primitive complessivo" - nah

# Better: "Primitive e complessivo le tinte" ?  
# Let me try "e" separately
# complessivo + primitive = uses: c1,o2,m2,p2,l1,e2,s2,i3,v2,r1,t1 = 18... 
# Wait: complessivo=c1,o2,m1,p1,l1,e1,s2,i1,v1 + primitive=p1,r1,i2,m1,t1,v1,e1
# Combined: c1,o2,m2,p2,l1,e2,s2,i3,v2,r1,t1 = 19 letters
# target: p2,r1,e5,c1,i4,t2,v2,o2,l2,s2,m2,n1 = 26
# remaining: e3,i1,t1,l1,n1 = 7 ✓ (matches what I said)

# "nel" + "lite" = n1,e1,l1 + l1,i1,t1,e1 = n1,e2,l2,i1,t1 = 7... but I need e3,i1,t1,l1,n1
# Combined needs: e3,i1,t1,l1,n1 = 7
# "nel lite" gives: n1,e2,l2,i1,t1 = 7 letters but l2 while I only have l1!
# Doh.

# "lenti" + "ne" = l1,e1,n1,t1,i1 + n1,e1 = l1,e2,n2,t1,i1 = 7 but n2 while I have n1!
# "enel" + "ti" = wait, let me just check: remaining is e3,i1,t1,l1,n1
# Words using exactly e3,i1,t1,l1,n1:
# "lentine" = no... "netlite" no...  
# "elite" + "n" no...
# "it" + "nelle" = i1,t1 + n1,e2,l2 needs l2 but only l1
# "tile" + "ne" + "e"? = t1,i1,l1,e1 + n1,e1 + e1 = t1,i1,l1,e3,n1 = 7 ✓!
# "ne" is Italian (of it), "e" is Italian (and), "tile" hmm not standard Italian

# "etile" = e2,t1,i1,l1 = 5 (not really Italian alone - it's a chemistry suffix)
# "lente" + "i" = l1,e2,n1,t1 + i1 = 6... that's only 6, need 7
# Hmm "lente" = l1,e2,n1,t1,e... wait l,e,n,t,e = 5 letters: l1,e2,n1,t1 ✓
# + "i" = 1 letter, total 6. I need 7.

# Let me accept "linee te" - "linee" (lines) and "te" (you) are both real Italian
# Phrase: "Complessivo, primitive linee te" or rearranged:
# "Te le primitive linee complessivo" - doesn't work grammatically

# Better arrangement: rethink the whole thing

# SIMPLEST APPROACH: find word combos programmatically
# Let me just brute force with a small Italian dictionary

italian_words_subset = [
    "il", "lo", "la", "le", "li", "i", "e", "o", "in", "me", "mi", "te", "ti",
    "si", "se", "vi", "ci", "ne", "per", "con", "sei", "tre", "poi", "ore", "nel",
    "voi", "noi", "mie", "vie", "pie", "mise", "vise", "lite", "mite", "pile",
    "vile", "tile", "seme", "rime", "pive", "olmo", "elmo", "mole", "sole",
    "pole", "melo", "velo", "pelo", "telo", "lino", "vino", "sino", "pino",
    "neve", "leve", "rete", "sete", "note", "vite", "site", "lime", "cime",
    "some", "come", "nome", "volte", "molte", "colte", "poste", "mosse",
    "svelte", "precise", "semplice", "completi", "movimenti", "primitivo",
    "primitive", "sportive", "svestire", "spolveri", "complessive",
    "complessivi", "complessivo", "improvvise", "percepisco", "sentimento",
    "televisore", "televisori", "televisioni", "ripetitivo",
    "percepimento", "imprevisto", "impreviste", "promettevi",
    "smettere", "smettevi", "permissive", "possessive", "ristorni",
    "esplicito", "implicite", "implicito", "sconvolte", "coinvolte",
    "risolvete", "promissive", "primissime",  "completissime",
    "semplicissime", "primitivismo", "espressivo", "espressivi",
    "emissive", "emissivo", "remissive", "permessive",
    "competitivo", "competitivi", "competitive", "ripetitive",
]

# Filter to only words that can be formed from our target letters
def can_form(word, available):
    return not (Counter(word.lower()) - available)

valid_words = [w for w in italian_words_subset if can_form(w, target)]
print(f"\nParole valide dal dizionario: {len(valid_words)}")
print(valid_words)

# Now try all combinations of 2-5 words from valid_words
from itertools import combinations_with_replacement

print("\n=== RICERCA COMBINAZIONI PERFETTE ===\n")
found = []

# Try pairs
for i, w1 in enumerate(valid_words):
    r1 = remaining_after([w1])
    if r1 is None:
        continue
    for w2 in valid_words[i:]:
        r2 = remaining_after([w1, w2])
        if r2 is None:
            continue
        if sum(r2.values()) == 0:
            found.append([w1, w2])
            continue
        # Try triples
        for w3 in valid_words:
            r3 = remaining_after([w1, w2, w3])
            if r3 is None:
                continue
            if sum(r3.values()) == 0:
                found.append([w1, w2, w3])
                continue
            if sum(r3.values()) <= 6:
                # Try quads
                for w4 in valid_words:
                    r4 = remaining_after([w1, w2, w3, w4])
                    if r4 is None:
                        continue
                    if sum(r4.values()) == 0:
                        found.append([w1, w2, w3, w4])

# This might be slow, let's limit output
if len(found) > 50:
    print(f"Trovate {len(found)} combinazioni, mostro le prime 50:")
    for f in found[:50]:
        print(f"  ✅ {' '.join(f)}")
else:
    print(f"Trovate {len(found)} combinazioni:")
    for f in found:
        print(f"  ✅ {' '.join(f)}")
