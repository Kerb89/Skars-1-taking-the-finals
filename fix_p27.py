import re

f = open('puntate/quiz_puntata27_misto.md', 'rb')
raw = f.read()
f.close()

# Decode as cp1252 (Windows default from PowerShell)
text = raw.decode('cp1252')

# Fix D38 question and options
text = text.replace(
    "Un uomo abita al decimo piano. Ogni mattina prende l\u2019ascensore e scende al piano terra. La sera, quando torna, prende l\u2019ascensore fino al settimo piano e poi sale a piedi. Perch\u00e9?",
    "Cosa ha un cuore che non batte?"
)
text = text.replace("L\u2019ascensore si ferma sempre al settimo", "Un orologio")
text = text.replace("Vuole fare esercizio fisico", "Un carciofo")
text = text.replace("\u00c8 troppo basso per raggiungere il pulsante del decimo piano", "Un vulcano")
text = text.replace("Il settimo piano \u00e8 quello dei suoi amici", "Una candela")

# Fix D38 solution
text = text.replace(
    "38. C\r\n> Spiegazione: L\u2019uomo \u00e8 troppo basso per premere il pulsante del decimo piano, ma raggiunge quello del settimo.",
    "38. B\r\n> Spiegazione: Il carciofo ha un cuore (la parte interna tenera) ma non batte."
)

# Fix D16 solution
text = text.replace(
    "La Bolivia \u00e8 uno dei due paesi sudamericani senza accesso al mare, insieme al Paraguay.",
    "Il Bangladesh ha oltre 170 milioni di abitanti su 148.000 km\u00b2, con densit\u00e0 circa 1.150 ab/km\u00b2."
)

# Fix D18 solution
text = text.replace(
    "Le ghiandole surrenali producono oltre 50 ormoni, tra cui cortisolo, aldosterone e adrenalina.",
    "La dopamina \u00e8 coinvolta nel sistema mesolimbico e gioca un ruolo chiave nelle dipendenze."
)

# Fix D34 solution
old34 = "La luce blu ha lunghezza d\u2019onda corta e viene diffusa maggiormente dall\u2019atmosfera; al tramonto il percorso lungo filtra il blu lasciando il rosso."
new34 = "Nel legame ionico gli ioni di segno opposto si attraggono elettrostaticamente, formando reticoli cristallini."
text = text.replace(old34, new34)

# Write as UTF-8
f = open('puntate/quiz_puntata27_misto.md', 'w', encoding='utf-8')
f.write(text)
f.close()
print('Fix completato')
