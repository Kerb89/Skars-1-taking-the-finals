"""
Genera la puntata 19 - Focus sulle categorie meno usate:
indovinelli, arte (con immagini!), inglese, anagrammi, lingua_italiana, cibo, lingue, tecnologia
+ alcune domande dalle categorie normali per bilanciare

Distribuzione (45 domande):
- arte: 5 (di cui 3 con immagine)
- indovinelli: 4
- inglese: 4
- anagrammi: 4
- lingua_italiana: 4
- cibo: 4
- lingue: 4
- tecnologia: 4
- matematica: 3
- letteratura: 3
- cinema: 2
- dituttounpo: 2
- sport: 1
- storia: 1
"""
import json, os, base64, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, "art_questions_images", "da_usare")
TEMPLATE_PATH = os.path.join(BASE, "template", "quiz_template.html")
OUTPUT_PATH = os.path.join(BASE, "puntate", "quiz_puntata19_misto.html")

def load_img_b64(fname):
    path = os.path.join(IMG_DIR, fname.replace('.jpg', '_b64.txt'))
    with open(path, 'r') as f:
        return 'data:image/jpeg;base64,' + f.read()

# Carica immagini
van_gogh_img = load_img_b64('van_gogh_autoritratto_cappello_1887.jpg')
caravaggio_img = load_img_b64('caravaggio_The_Musicians_1597.jpg')
el_greco_img = load_img_b64('el_greco_vista_toledo_1600.jpg')

questions = [
    # === ARTE (5) ===
    {"q": "🖼️ DOMANDA VISIVA — Quale pittore ha realizzato questo autoritratto con cappello di paglia, conservato al Metropolitan Museum di New York?",
     "opts": ["Paul Cézanne", "Vincent van Gogh", "Paul Gauguin", "Édouard Manet"], "ans": 1, "cat": "arte", "img": van_gogh_img},
    
    {"q": "🖼️ DOMANDA VISIVA — Quale pittore italiano del Cinquecento ha dipinto questo quadro intitolato \"I Musicisti\", conservato al Metropolitan Museum?",
     "opts": ["Caravaggio", "Tiziano", "Raffaello", "Tintoretto"], "ans": 0, "cat": "arte", "img": caravaggio_img},
    
    {"q": "🖼️ DOMANDA VISIVA — Quale pittore di origine greca, attivo in Spagna, ha dipinto questa celebre \"Veduta di Toledo\" intorno al 1600?",
     "opts": ["Diego Velázquez", "Francisco Goya", "El Greco", "Bartolomé Esteban Murillo"], "ans": 2, "cat": "arte", "img": el_greco_img},
    
    {"q": "Quale corrente artistica, nata a Milano nel 1909 con il manifesto di Filippo Tommaso Marinetti, esaltava la velocità, la tecnologia e il dinamismo?",
     "opts": ["Cubismo", "Futurismo", "Dadaismo", "Espressionismo"], "ans": 1, "cat": "arte"},
    
    {"q": "Quale pittore olandese del XVII secolo è celebre per i suoi interni domestici pervasi da una luce morbida e per \"La ragazza con l'orecchino di perla\"?",
     "opts": ["Rembrandt van Rijn", "Frans Hals", "Johannes Vermeer", "Pieter de Hooch"], "ans": 2, "cat": "arte"},

    # === INDOVINELLI (4) ===
    {"q": "Più ne togli, più divento grande. Cosa sono?",
     "opts": ["Un debito", "Una buca", "Una fila", "Un'ombra"], "ans": 1, "cat": "indovinelli"},
    
    {"q": "Ho le mani ma non posso applaudire, ho un viso ma non posso sorridere. Cosa sono?",
     "opts": ["Un orologio", "Un manichino", "Uno specchio", "Un guanto"], "ans": 0, "cat": "indovinelli"},
    
    {"q": "Qual è quella cosa che quando la nomini, smette di esistere?",
     "opts": ["Il silenzio", "Il buio", "Il vuoto", "Il sonno"], "ans": 0, "cat": "indovinelli"},
    
    {"q": "Un contadino ha 17 pecore. Tutte tranne 9 scappano. Quante ne rimangono?",
     "opts": ["8", "17", "9", "0"], "ans": 2, "cat": "indovinelli"},

    # === INGLESE (4) ===
    {"q": "Quale delle seguenti frasi usa correttamente il Third Conditional?",
     "opts": ["If I would have known, I would go", "If I had known, I would have gone", "If I knew, I would have gone", "If I have known, I would go"], "ans": 1, "cat": "inglese"},
    
    {"q": "Quale parola inglese significa \"to deliberately postpone doing something\"?",
     "opts": ["Procrastinate", "Elaborate", "Exaggerate", "Deteriorate"], "ans": 0, "cat": "inglese"},
    
    {"q": "Completa correttamente: \"She suggested ___ the meeting to Friday.\"",
     "opts": ["to postpone", "postponing", "postpone", "to postponing"], "ans": 1, "cat": "inglese"},
    
    {"q": "Quale espressione idiomatica inglese significa \"rivelare un segreto accidentalmente\"?",
     "opts": ["Break the ice", "Let the cat out of the bag", "Hit the nail on the head", "Bite the bullet"], "ans": 1, "cat": "inglese"},

    # === ANAGRAMMI (4) ===
    {"q": "\"CASTAGNE\" è l'anagramma di quale parola italiana?",
     "opts": ["Stagnare", "Scagnate", "Stancage", "Scatagne"], "ans": 0, "cat": "anagrammi"},
    
    {"q": "\"PREDONI\" è l'anagramma di quale parola italiana?",
     "opts": ["Prondie", "Rompendo", "Riposte", "Prendiò"], "ans": 0, "cat": "anagrammi"},
    
    {"q": "\"COSTIERA\" è l'anagramma di quale parola italiana?",
     "opts": ["Ricostae", "Esorcista", "Ostacire", "Costaire"], "ans": 1, "cat": "anagrammi"},
    
    {"q": "\"SVENTOLA\" è l'anagramma di quale parola italiana?",
     "opts": ["Tavolens", "Voltesna", "Solventa", "Svelaton"], "ans": 2, "cat": "anagrammi"},

    # === LINGUA ITALIANA (4) ===
    {"q": "Qual è il plurale corretto di \"tempio\"?",
     "opts": ["Tempi", "Templi", "Tempii", "Tempi e templi sono entrambi corretti"], "ans": 3, "cat": "lingua_italiana"},
    
    {"q": "Quale figura retorica accosta due termini di significato opposto, come \"ghiaccio bollente\"?",
     "opts": ["Paradosso", "Ossimoro", "Antitesi", "Iperbole"], "ans": 1, "cat": "lingua_italiana"},
    
    {"q": "Quale tempo verbale si usa nella frase: \"Se avessi studiato, avrei superato l'esame\"?",
     "opts": ["Congiuntivo imperfetto + condizionale presente", "Congiuntivo trapassato + condizionale passato", "Indicativo imperfetto + condizionale passato", "Congiuntivo presente + condizionale presente"], "ans": 1, "cat": "lingua_italiana"},
    
    {"q": "Quale termine indica una parola formata dall'unione di due parole esistenti, come \"capostazione\" o \"portafortuna\"?",
     "opts": ["Parola composta", "Neologismo", "Prestito linguistico", "Derivato"], "ans": 0, "cat": "lingua_italiana"},

    # === CIBO (4) ===
    {"q": "Quale spezia, ricavata dagli stigmi di un fiore della famiglia del croco, è la più costosa al mondo per peso?",
     "opts": ["Vaniglia", "Zafferano", "Cardamomo", "Cannella"], "ans": 1, "cat": "cibo"},
    
    {"q": "Il \"dashi\", brodo fondamentale della cucina giapponese, è tradizionalmente preparato con alga kombu e quale altro ingrediente?",
     "opts": ["Miso", "Tofu", "Katsuobushi (bonito essiccato)", "Funghi shiitake"], "ans": 2, "cat": "cibo"},
    
    {"q": "Quale formaggio italiano DOP, prodotto esclusivamente in Sardegna, è noto per contenere larve vive di mosca casearia?",
     "opts": ["Pecorino sardo", "Casu marzu", "Fiore sardo", "Canestrato pugliese"], "ans": 1, "cat": "cibo"},
    
    {"q": "Quale processo chimico, scoperto da Louis Pasteur, consiste nel riscaldare un liquido per eliminare microrganismi patogeni senza alterarne significativamente il sapore?",
     "opts": ["Fermentazione", "Pastorizzazione", "Liofilizzazione", "Sterilizzazione"], "ans": 1, "cat": "cibo"},

    # === LINGUE (4) ===
    {"q": "In giapponese, cosa significa \"侘寂\" (wabi-sabi)?",
     "opts": ["L'arte della guerra e della strategia", "La bellezza nell'imperfezione e nella transitorietà", "Il rispetto verso gli anziani e la tradizione", "L'armonia tra uomo e natura"], "ans": 1, "cat": "lingue"},
    
    {"q": "Quale lingua ha più parlanti nativi al mondo?",
     "opts": ["Inglese", "Hindi", "Spagnolo", "Cinese mandarino"], "ans": 3, "cat": "lingue"},
    
    {"q": "In portoghese, cosa significa \"saudade\"?",
     "opts": ["Felicità improvvisa", "Nostalgia profonda per qualcosa di assente", "Gratitudine verso il destino", "Paura dell'ignoto"], "ans": 1, "cat": "lingue"},
    
    {"q": "Quale parola svedese, diventata famosa grazie a IKEA, indica una pausa caffè rituale con dolcetti?",
     "opts": ["Hygge", "Lagom", "Fika", "Smörgåsbord"], "ans": 2, "cat": "lingue"},

    # === TECNOLOGIA (4) ===
    {"q": "Quale protocollo di rete, operante al livello di trasporto, garantisce la consegna ordinata e affidabile dei pacchetti grazie al meccanismo di handshake a tre vie?",
     "opts": ["UDP", "TCP", "ICMP", "HTTP"], "ans": 1, "cat": "tecnologia"},
    
    {"q": "In quale anno Tim Berners-Lee pubblicò la prima pagina web al mondo, ospitata al CERN di Ginevra?",
     "opts": ["1989", "1991", "1993", "1995"], "ans": 1, "cat": "tecnologia"},
    
    {"q": "Quale struttura dati utilizza il principio LIFO (Last In, First Out)?",
     "opts": ["Coda (queue)", "Pila (stack)", "Lista concatenata", "Albero binario"], "ans": 1, "cat": "tecnologia"},
    
    {"q": "Quale azienda sviluppò il primo microprocessore commerciale, l'Intel 4004, nel 1971?",
     "opts": ["IBM", "Intel", "Texas Instruments", "Motorola"], "ans": 1, "cat": "tecnologia"},

    # === MATEMATICA (3) ===
    {"q": "Qual è il risultato di 15² − 12²?",
     "opts": ["81", "69", "56", "91"], "ans": 0, "cat": "matematica"},
    
    {"q": "Se un triangolo ha lati di 3, 4 e 5 cm, qual è la sua area in cm²?",
     "opts": ["6", "10", "12", "7.5"], "ans": 0, "cat": "matematica"},
    
    {"q": "Quale numero primo viene subito dopo 89?",
     "opts": ["91", "93", "97", "101"], "ans": 2, "cat": "matematica"},

    # === LETTERATURA (3) ===
    {"q": "Quale scrittore giapponese, autore di \"Norwegian Wood\" e \"Kafka sulla spiaggia\", è tra i più tradotti al mondo e perenne candidato al Nobel?",
     "opts": ["Haruki Murakami", "Yukio Mishima", "Kenzaburō Ōe", "Banana Yoshimoto"], "ans": 0, "cat": "letteratura"},
    
    {"q": "Chi scrisse \"Il processo\" e \"La metamorfosi\", opere emblematiche dell'angoscia esistenziale del Novecento?",
     "opts": ["Robert Musil", "Franz Kafka", "Thomas Mann", "Hermann Hesse"], "ans": 1, "cat": "letteratura"},
    
    {"q": "Quale poetessa statunitense, vissuta in quasi totale isolamento, scrisse circa 1800 poesie pubblicate in gran parte postume nel 1886?",
     "opts": ["Sylvia Plath", "Emily Dickinson", "Maya Angelou", "Anne Sexton"], "ans": 1, "cat": "letteratura"},

    # === CINEMA (2) ===
    {"q": "Quale regista sudcoreano ha vinto l'Oscar al Miglior Film nel 2020 con \"Parasite\", primo film non in lingua inglese a ricevere il premio?",
     "opts": ["Park Chan-wook", "Bong Joon-ho", "Lee Chang-dong", "Kim Ki-duk"], "ans": 1, "cat": "cinema"},
    
    {"q": "In quale film del 1999, diretto dalle sorelle Wachowski, il protagonista scopre che la realtà è una simulazione informatica?",
     "opts": ["Dark City", "The Matrix", "eXistenZ", "The Thirteenth Floor"], "ans": 1, "cat": "cinema"},

    # === DI TUTTO UN PO' (2) ===
    {"q": "Quale disciplina filosofica studia la natura della conoscenza, le sue fonti e i suoi limiti?",
     "opts": ["Ontologia", "Epistemologia", "Etica", "Estetica"], "ans": 1, "cat": "dituttounpo"},
    
    {"q": "Quale unità di misura del Sistema Internazionale corrisponde alla forza necessaria per accelerare una massa di 1 kg di 1 m/s²?",
     "opts": ["Joule", "Watt", "Newton", "Pascal"], "ans": 2, "cat": "dituttounpo"},

    # === SPORT (1) ===
    {"q": "In quale sport si disputa la Ryder Cup, competizione biennale tra una selezione europea e una statunitense?",
     "opts": ["Tennis", "Golf", "Vela", "Polo"], "ans": 1, "cat": "sport"},

    # === STORIA (1) ===
    {"q": "Quale trattato del 1648 pose fine alla Guerra dei Trent'anni, ridisegnando la mappa politica dell'Europa e stabilendo il principio di sovranità nazionale?",
     "opts": ["Pace di Vestfalia", "Trattato di Utrecht", "Pace di Augusta", "Congresso di Vienna"], "ans": 0, "cat": "storia"},
]

print(f"Totale domande: {len(questions)}")

# Conta per categoria
from collections import Counter
cats = Counter(q['cat'] for q in questions)
print("\nDistribuzione categorie:")
for cat, n in cats.most_common():
    print(f"  {cat}: {n}")

# Genera HTML
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template = f.read()

title = "Puntata 19 \u2014 Misto"
subtitle = f"Misto \u2014 {len(questions)} domande \u2014 20s timer"
filename = "quiz_puntata19_misto"

# Category backgrounds (usa path relativi come puntata 17-18)
cat_bgs = {
    'musica':['../category_backgrounds/musica_1.jpg','../category_backgrounds/musica_2.jpg','../category_backgrounds/musica_3.jpg'],
    'geografia':['../category_backgrounds/geografia_1.jpg','../category_backgrounds/geografia_2.jpg','../category_backgrounds/geografia_3.jpg'],
    'scienze':['../category_backgrounds/scienze_1.jpg','../category_backgrounds/scienze_2.jpg','../category_backgrounds/scienze_3.jpg'],
    'storia':['../category_backgrounds/storia_1.jpg','../category_backgrounds/storia_2.jpg','../category_backgrounds/storia_3.jpg'],
    'dituttounpo':['../category_backgrounds/dituttounpo_1.jpg','../category_backgrounds/dituttounpo_2.jpg','../category_backgrounds/dituttounpo_1.jpg'],
    'sport':['../category_backgrounds/sport_1.jpg','../category_backgrounds/sport_2.jpg','../category_backgrounds/sport_3.jpg'],
    'letteratura':['../category_backgrounds/letteratura_1.jpg','../category_backgrounds/letteratura_2.jpg','../category_backgrounds/letteratura_3.jpg'],
    'matematica':['../category_backgrounds/matematica_1.jpg','../category_backgrounds/matematica_1.jpg','../category_backgrounds/matematica_3.jpg'],
    'cinema':['../category_backgrounds/cinema_1.jpg','../category_backgrounds/cinema_2.jpg','../category_backgrounds/cinema_3.jpg'],
    'lingua_italiana':['../category_backgrounds/lingua_italiana_1.jpg','../category_backgrounds/lingua_italiana_2.jpg','../category_backgrounds/lingua_italiana_3.jpg'],
    'lingue_straniere':['../category_backgrounds/lingue_1.jpg','../category_backgrounds/lingue_2.jpg','../category_backgrounds/lingue_3.jpg'],
    'lingue':['../category_backgrounds/lingue_1.jpg','../category_backgrounds/lingue_2.jpg','../category_backgrounds/lingue_3.jpg'],
    'inglese':['../category_backgrounds/inglese_1.jpg','../category_backgrounds/inglese_2.jpg','../category_backgrounds/inglese_3.jpg'],
    'anagrammi':['../category_backgrounds/anagrammi_1.jpg','../category_backgrounds/anagrammi_2.jpg','../category_backgrounds/anagrammi_1.jpg'],
    'attualita':['../category_backgrounds/attualita_1.jpg','../category_backgrounds/attualita_2.jpg','../category_backgrounds/attualita_1.jpg'],
    'cibo':['../category_backgrounds/cibo_1.jpg','../category_backgrounds/cibo_2.jpg','../category_backgrounds/cibo_3.jpg'],
    'indovinelli':['../category_backgrounds/dituttounpo_1.jpg','../category_backgrounds/dituttounpo_2.jpg','../category_backgrounds/dituttounpo_1.jpg'],
    'arte':['../category_backgrounds/arte_1.jpg','../category_backgrounds/arte_2.jpg','../category_backgrounds/arte_3.jpg'],
    'tecnologia':['../category_backgrounds/tecnologia_1.jpg','../category_backgrounds/tecnologia_2.jpg','../category_backgrounds/tecnologia_3.jpg']
}

cat_labels = {
    "musica":"Musica","geografia":"Geografia","scienze":"Scienze","storia":"Storia",
    "dituttounpo":"Di tutto un po'","sport":"Sport","letteratura":"Letteratura",
    "matematica":"Matematica","cinema":"Cinema","lingua_italiana":"Lingua italiana",
    "lingue_straniere":"Lingue straniere","inglese":"Inglese","anagrammi":"Anagrammi",
    "attualita":"Attualità","cibo":"Cibo e benessere","indovinelli":"Indovinelli",
    "arte":"Arte","tecnologia":"Tecnologia","lingue":"Lingue straniere"
}

cat_colors = {
    "geografia":"#1a3a5c","tecnologia":"#0d3b2e","scienze":"#1b4d5c","sport":"#5c2a0d",
    "storia":"#4a3b1f","cibo":"#5c1a1a","attualita":"#2a3545","matematica":"#1a2a1a",
    "musica":"#3d1a4a","cinema":"#3d0d0d","letteratura":"#3d2a1a","arte":"#2a2a4a",
    "inglese":"#1a1a4a","lingue_straniere":"#4a3a1a","lingue":"#4a3a1a",
    "lingua_italiana":"#1a1a4a","anagrammi":"#2a3d1a","indovinelli":"#3d3d0d",
    "dituttounpo":"#2a1a3d"
}

# Sostituisci nel template
html = template
html = html.replace('{{PUNTATA_TITLE}}', title)
html = html.replace('{{SUBTITLE}}', subtitle)
html = html.replace('{{FILENAME}}', filename)

# Questions JSON e catBackgrounds vanno nel tag script
questions_json = json.dumps(questions, ensure_ascii=False)
cat_bgs_json = json.dumps(cat_bgs)
cat_labels_json = json.dumps(cat_labels, ensure_ascii=False)
cat_colors_json = json.dumps(cat_colors)

# Cerca il pattern nel template per inserire i dati
# Il template ha placeholder diversi, controlliamo
if '{{QUESTIONS_JSON}}' in html:
    html = html.replace('{{QUESTIONS_JSON}}', questions_json)
    html = html.replace('{{CATEGORY_BACKGROUNDS_JSON}}', cat_bgs_json)
    print("\nUsato template con placeholder")
else:
    # Inserisci direttamente come nella puntata 17/18
    script_block = f'''<script>const QUIZ_META={{title:"{title}",filename:"{filename}",timerDefault:20,timerAudio:30,timerIndovinello:30}}; const questions={questions_json}; const catLabels = {cat_labels_json};
const catBackgrounds = {cat_bgs_json};

const catNames = catLabels;
const catColors = {cat_colors_json};'''
    # Trova dove inserire
    print("\nTemplate senza placeholder standard, serve approccio diverso")

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(OUTPUT_PATH) // 1024
print(f"\nSalvato: {OUTPUT_PATH} ({size_kb} KB)")
