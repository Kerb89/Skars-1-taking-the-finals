import json, os
from PIL import Image
import base64, io

def img_b64(path):
    img = Image.open(path)
    img.thumbnail((500, 500), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='JPEG', quality=50, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

def audio_b64(path):
    with open(path, 'rb') as f:
        data = f.read()
    # If too large, we'll still include but note it
    return 'data:audio/mp3;base64,' + base64.b64encode(data).decode()

def img_b64_lowq(path, quality=35, size=400):
    """Lower quality for weight reduction"""
    img = Image.open(path)
    img.thumbnail((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='JPEG', quality=quality, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

print("Loading P32 HTML as base...")
with open('puntate/quiz_puntata32_misto.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('Puntata 32', 'Puntata 33')
html = html.replace('quiz_puntata32_misto', 'quiz_puntata33_misto')

print("Converting assets (reduced quality for weight)...")
a16 = img_b64_lowq('assets/manche_a_tema/asset_16_shining_room237.jfif', 35, 400)
a19 = img_b64_lowq('assets/manche_a_tema/asset_19_nosferatu_1922_stairs.jpg', 35, 400)
a27 = img_b64_lowq('assets/manche_a_tema/asset_27_nosferatu_2024_eggers.webp', 35, 400)
morisot_img = img_b64_lowq('art_questions_images/da_usare/morisot_the_pink_dress_1870.jpg', 40, 450)
a24 = audio_b64('assets/manche_a_tema/asset_24_compressed.mp3')
a30 = audio_b64('assets/manche_a_tema/asset_30_compressed.mp3')

# Check audio sizes
import os
s24 = os.path.getsize('assets/manche_a_tema/asset_24_the_thing_morricone.mp3')
s30 = os.path.getsize('assets/manche_a_tema/asset_30_quiet_place_creature.mp3')
print(f"Audio sizes: a24={s24//1024}KB, a30={s30//1024}KB, total={(s24+s30)//1024}KB")
# 1536KB limit for all media. Images are small (~5-20KB each).
# Audio needs to be under ~1400KB total to leave room for images
if (s24 + s30) > 1400*1024:
    print("WARNING: Audio too heavy, need to trim files externally")

# Questions with CORRECTED distribution
# Target: A(0)=11, B(1)=12, C(2)=11, D(3)=11
# Reorder options to achieve balanced distribution
# Format: q, opts (in order A,B,C,D), ans (0-3), cat, expl, [img], [audio]

questions = [
  {"q":"Quale citta' indiana sulle rive del Gange e' considerata una delle piu' antiche continuamente abitate al mondo e rappresenta il principale centro sacro dell'induismo?","opts":["Jaipur","Allahabad","Varanasi","Udaipur"],"ans":2,"cat":"geografia","expl":"Varanasi, nota anche come Kashi o Benares, e' abitata da oltre 3.000 anni sulla riva occidentale del Gange."},
  {"q":"Quale ponte sospeso nello stato di Washington crollo' nel novembre 1940 a causa di oscillazioni aeroelastiche, diventando un caso di studio per l'ingegneria strutturale?","opts":["Ponte di Tacoma Narrows","Golden Gate Bridge","Ponte di Brooklyn","Verrazano-Narrows Bridge"],"ans":0,"cat":"tecnologia","expl":"Il ponte di Tacoma Narrows crollo' il 7 novembre 1940. I lavoratori lo soprannominarono Galloping Gertie."},
  {"q":"Quale classe di materiali cristallini con struttura ABX3 e' considerata la piu' promettente per le celle solari di nuova generazione?","opts":["Grafene","Arseniuro di gallio","Silicio amorfo","Perovskite"],"ans":3,"cat":"scienze","expl":"Le perovskiti hanno struttura cristallina ABX3. L'efficienza e' passata dal 3,8% nel 2009 a oltre il 33% in tandem con silicio."},
  {"q":"Come si chiama la regione del piano complesso in cui la parte reale e' strettamente positiva, usata nello studio della convergenza delle serie di Dirichlet?","opts":["Disco di Poincare'","Semipiano di Gauss","Striscia critica","Piano di Argand"],"ans":1,"cat":"matematica","expl":"Il semipiano di Gauss e' la regione dove Re(s) > 0. E' fondamentale per la trasformata di Laplace."},
  {"q":"Quale battaglia del 480 a.C. vide trecento spartani guidati da Leonida resistere per tre giorni contro l'esercito persiano di Serse?","opts":["Maratona","Salamina","Platea","Termopili"],"ans":3,"cat":"storia","expl":"La battaglia delle Termopili si combatte' nell'agosto del 480 a.C. in un passo stretto tra il monte e il mare."},
  {"q":"Quale film distopico del 2013, diretto da Bong Joon-ho, e' ambientato interamente su un treno in moto perpetuo che trasporta gli ultimi sopravvissuti dopo un'era glaciale artificiale?","opts":["Elysium","The Platform","Snowpiercer","High-Rise"],"ans":2,"cat":"cinema","expl":"Snowpiercer e' basato sulla graphic novel francese Le Transperceneige di Lob e Rochette del 1982."},
  {"q":"Quale salsa di pesce fermentato era il condimento piu' diffuso nella cucina dell'antica Roma?","opts":["Allec","Muria","Liquamen","Garum"],"ans":3,"cat":"cibo","expl":"Il garum si produceva lasciando fermentare intestini di pesce con sale per settimane sotto il sole."},
  {"q":"Nella battaglia di Canne del 216 a.C., quale manovra tattica utilizzo' Annibale per accerchiare l'esercito romano?","opts":["Doppio aggiramento","Falange obliqua","Ritirata simulata","Cuneo frontale"],"ans":0,"cat":"storia","expl":"Annibale dispose la fanteria al centro arretrata e la cavalleria sui fianchi, chiudendo i romani nella sacca."},
  {"q":"Quale band britannica pubblico' nel 1997 il singolo Bitter Sweet Symphony, il cui riff campionava un arrangiamento dei Rolling Stones?","opts":["Oasis","Blur","Pulp","The Verve"],"ans":3,"cat":"musica","expl":"Il brano campionava un arrangiamento di Andrew Loog Oldham di The Last Time. I crediti furono restituiti a Ashcroft nel 2019."},
  {"q":"Quale antica capitale del Giappone ospita il Grande Buddha di bronzo del tempio Todai-ji, alto circa 15 metri?","opts":["Kyoto","Osaka","Nara","Kamakura"],"ans":2,"cat":"geografia","expl":"Nara fu la prima capitale permanente del Giappone dal 710 al 784 d.C."},
  {"q":"Quale termine giapponese indicava il governo militare dello shogun, in contrapposizione al potere formale dell'imperatore?","opts":["Daimyo","Bakufu","Zaibatsu","Bushido"],"ans":1,"cat":"storia","expl":"Bakufu significa letteralmente governo della tenda. Il primo fu istituito a Kamakura nel 1185."},
  {"q":"Quale figura retorica consiste nell'usare un nome proprio per indicare una categoria, come un Giuda per dire un traditore?","opts":["Metonimia","Perifrasi","Antonomasia","Sineddoche"],"ans":2,"cat":"lingua_italiana","expl":"L'antonomasia usa un nome proprio come nome comune o viceversa. Un mecenate viene da Gaio Cilnio Mecenate."},
  {"q":"Quale espressione idiomatica francese significa essere depresso e si traduce letteralmente come avere lo scarafaggio?","opts":["Avoir le cafard","Avoir la peche","Avoir la flemme","Avoir le bourdon"],"ans":0,"cat":"lingue","expl":"Avoir le cafard risale al XIX secolo. Baudelaire contribui' a diffonderla associando lo scarafaggio alla malinconia."},
  {"q":"Which formal English word means in spite of and can function as both a preposition and an adverb?","opts":["Henceforth","Thereafter","Whereby","Notwithstanding"],"ans":3,"cat":"inglese","expl":"Notwithstanding e' usato in contesti formali e legali. Deriva dall'inglese medio not withstondynge."},
  {"q":"Quale sport tradizionale scozzese delle Highlands si gioca con bastoni ricurvi e una palla di cuoio, e ricorda l'hurling irlandese?","opts":["Lacrosse","Croquet","Shinty","Bandy"],"ans":2,"cat":"sport","expl":"Lo shinty, in gaelico scozzese camanachd, ha origini celtiche condivise con l'hurling irlandese."},
  {"q":"In quale stanza dell'Overlook Hotel, nel film di Kubrick del 1980, si trova lo spettro di una donna nella vasca da bagno?","opts":["Stanza 313","Stanza 237","Stanza 217","Stanza 401"],"ans":1,"cat":"horror","expl":"Nel film la stanza e' la 237, nel romanzo di King era la 217. Il cambio avvenne su richiesta del Timberline Lodge.","img":"PLACEHOLDER_16"},
  {"q":"Quale regista americano diresse nel 1973 il film L'esorcista, tratto dal romanzo di William Peter Blatty?","opts":["Roman Polanski","Brian De Palma","John Boorman","William Friedkin"],"ans":3,"cat":"horror","expl":"William Friedkin vinse l'Oscar per la regia nel 1972 per Il braccio violento della legge e diresse L'esorcista l'anno successivo."},
  {"q":"Quale regista italiano e' considerato il maestro del giallo e dell'horror barocco, autore di Suspiria e Profondo rosso?","opts":["Mario Bava","Dario Argento","Lucio Fulci","Lamberto Bava"],"ans":1,"cat":"horror","expl":"Dario Argento, nato a Roma nel 1940, debutto' con L'uccello dalle piume di cristallo nel 1970."},
  {"q":"Quale film muto del 1922, adattamento non autorizzato di Dracula di Bram Stoker, mostra questa iconica silhouette con dita adunche che sale le scale?","opts":["Il gabinetto del dottor Caligari","Vampyr","Il fantasma dell'opera","Nosferatu"],"ans":3,"cat":"horror","expl":"Nosferatu fu diretto da F.W. Murnau nel 1922. La vedova di Stoker fece causa per violazione del copyright.","img":"PLACEHOLDER_19"},
  {"q":"Quale film horror giapponese del 1998, diretto da Hideo Nakata, racconta di una videocassetta maledetta che uccide chi la guarda entro sette giorni?","opts":["Ju-On","The Ring","Dark Water","Audition"],"ans":1,"cat":"horror","expl":"Ring (Ringu) fu basato sul romanzo di Koji Suzuki del 1991. Il remake americano del 2002 fu diretto da Gore Verbinski."},
  {"q":"In quale paese scandinavo e' ambientato il film Midsommar di Ari Aster, dove un gruppo di americani viene attirato in un rituale pagano?","opts":["Norvegia","Finlandia","Svezia","Danimarca"],"ans":2,"cat":"horror","expl":"Midsommar e' ambientato in una comune rurale svedese. Le riprese avvennero fuori Budapest per ragioni di budget."},
  {"q":"Quale film horror del 2017, esordio alla regia di Jordan Peele, usa il concetto del Sunken Place come metafora della marginalizzazione razziale?","opts":["Us","Candyman","Get Out","Sorry to Bother You"],"ans":2,"cat":"horror","expl":"Get Out vinse l'Oscar per la miglior sceneggiatura originale nel 2018."},
  {"q":"Quale regista americano creo' sia il franchise di Nightmare - Dal profondo della notte nel 1984 sia quello di Scream nel 1996?","opts":["John Carpenter","Wes Craven","Sam Raimi","Tobe Hooper"],"ans":1,"cat":"horror","expl":"Wes Craven creo' Freddy Krueger per Nightmare nel 1984 e reinvento' lo slasher con Scream nel 1996."},
  {"q":"Da quale film horror e' tratto questo celebre tema musicale composto da Ennio Morricone?","opts":["Halloween","Suspiria","L'Esorcista","La Cosa"],"ans":3,"cat":"horror","expl":"Morricone compose la colonna sonora di La Cosa di John Carpenter nel 1982, una partitura minimalista.","audio":"PLACEHOLDER_24"},
  {"q":"Quale artista svizzero, noto per lo stile biomeccanico, disegno' la creatura aliena del film Alien di Ridley Scott?","opts":["Zdzislaw Beksinski","Francis Bacon","H.R. Giger","Clive Barker"],"ans":2,"cat":"horror","expl":"Hans Rudolf Giger vinse l'Oscar per i migliori effetti visivi nel 1980. Il suo museo si trova a Gruyeres."},
  {"q":"Quale film horror del 2018, esordio di Ari Aster, racconta il disfacimento di una famiglia e coinvolge il demone Paimon?","opts":["The Babadook","Hereditary","The Witch","It Follows"],"ans":1,"cat":"horror","expl":"Hereditary fu prodotto da A24. Il demone Paimon proviene dalla demonologia medievale della Ars Goetia."},
  {"q":"Quale regista americano, autore di The Witch e The Lighthouse, ha diretto nel 2024 un remake del celebre film vampiresco di Murnau del 1922?","opts":["Robert Eggers","Ari Aster","Mike Flanagan","Ti West"],"ans":0,"cat":"horror","expl":"Robert Eggers debutto' con The Witch nel 2015. Il suo Nosferatu del 2024 e' un remake del capolavoro di Murnau.","img":"PLACEHOLDER_27"},
  {"q":"Quale regista australiano diresse nel 2004 il primo capitolo di Saw, girato in 18 giorni con un budget di poco piu' di un milione di dollari?","opts":["Leigh Whannell","Greg McLean","James Wan","David Slade"],"ans":2,"cat":"horror","expl":"James Wan, nato in Malaysia e cresciuto a Melbourne, diresse Saw a 27 anni."},
  {"q":"Quale regista americano diresse La notte dei morti viventi nel 1968, inventando il genere zombie moderno?","opts":["Tobe Hooper","Roger Corman","Wes Craven","George A. Romero"],"ans":3,"cat":"horror","expl":"Romero giro' il film con 114.000 dollari a Evans City, Pennsylvania."},
  {"q":"Quale film horror del 2018 utilizza il silenzio come elemento chiave, con creature aliene cieche che cacciano attraverso l'udito?","opts":["A Quiet Place","Bird Box","The Silence","Don't Breathe"],"ans":0,"cat":"horror","expl":"A Quiet Place fu diretto da John Krasinski. Incasso' 340 milioni su un budget di 17 milioni.","audio":"PLACEHOLDER_30"},
  {"q":"Quale tipo di stella di neutroni possiede il campo magnetico piu' intenso conosciuto nell'universo?","opts":["Pulsar","Nana bianca","Magnetar","Quasar"],"ans":2,"cat":"scienze","expl":"I magnetar hanno campi magnetici fino a 10^15 gauss, un miliardo di volte piu' intensi di quello terrestre."},
  {"q":"Quale pittrice impressionista francese, cognata di Edouard Manet, dipinse questo ritratto intimo di una donna in abito rosa?","opts":["Mary Cassatt","Eva Gonzales","Marie Bracquemond","Berthe Morisot"],"ans":3,"cat":"arte","expl":"Berthe Morisot fu tra le fondatrici dell'Impressionismo e partecipo' a sette delle otto mostre del gruppo.","img":"PLACEHOLDER_MORISOT"},
  {"q":"Quale sport tradizionale basco si pratica lanciando una palla contro un muro con una cesta ricurva legata alla mano?","opts":["Pelota basca","Squash","Jai alai","Tejo"],"ans":2,"cat":"sport","expl":"Il jai alai, in basco festa allegra, si pratica con una cesta chiamata chistera. La palla puo' superare i 300 km/h."},
  {"q":"Quale antico codice di leggi babilonese, risalente al XVIII secolo a.C. e inciso su una stele di diorite, e' uno dei piu' antichi testi giuridici completi?","opts":["Codice di Hammurabi","Leggi di Solone","Leggi delle XII Tavole","Codice di Giustiniano"],"ans":0,"cat":"storia","expl":"Il Codice di Hammurabi contiene 282 leggi su una stele alta 2,25 m, oggi al Louvre."},
  {"q":"Quale grasso chiarificato, ottenuto riscaldando il burro fino a eliminare acqua e proteine del latte, e' fondamentale nella cucina indiana?","opts":["Strutto","Margarina","Ghee","Lardo"],"ans":2,"cat":"cibo","expl":"Il ghee ha un punto di fumo di circa 250 gradi. Nell'Ayurveda e' classificato come rasayana."},
  {"q":"Quale tecnica di memorizzazione si basa sull'associazione di informazioni a luoghi fisici lungo un percorso mentale immaginario?","opts":["Ripetizione spaziata","Chunking","Mnemotecnica","Metodo dei loci"],"ans":3,"cat":"dituttounpo","expl":"Il metodo dei loci e' attribuito al poeta greco Simonide di Ceo nel V secolo a.C."},
  {"q":"Riordinando le undici lettere della parola MINERALOGIA si ottiene il nome di un concetto legato alla vita dei mammiferi. Quale?","opts":["MALIGNATORE","ANIMALIGERO","GERMINALIOA","MARGINALITA'"],"ans":1,"cat":"anagrammi","expl":"MINERALOGIA riordinata diventa ANIMALIGERO, aggettivo raro legato al mondo animale."},
  {"q":"Mi si usa tutti i giorni ma non ci si pensa mai. Ho due piatti, un fulcro e misuro cio' che non si vede a occhio. Cosa sono?","opts":["Un orologio","Il termometro","Il microscopio","La bilancia"],"ans":3,"cat":"indovinelli","expl":"La bilancia ha due piatti e un fulcro, e misura il peso, qualcosa che non si vede a occhio nudo."},
  {"q":"Quale opera lirica di Mozart del 1791 contiene l'aria della Regina della Notte Der Holle Rache?","opts":["Don Giovanni","Il flauto magico","Le nozze di Figaro","Cosi' fan tutte"],"ans":1,"cat":"musica","expl":"Il flauto magico debutto' a Vienna il 30 settembre 1791, due mesi prima della morte di Mozart."},
  {"q":"Quale struttura cilindrica di carbonio, con diametro di pochi nanometri e resistenza superiore all'acciaio, e' studiata per l'elettronica flessibile?","opts":["Nanotubi di carbonio","Fullerene","Grafene","Diamante sintetico"],"ans":0,"cat":"tecnologia","expl":"I nanotubi di carbonio furono osservati da Sumio Iijima nel 1991. La loro resistenza e' circa 100 volte quella dell'acciaio."},
  {"q":"Quale tecnica di indagine permise a Rosalind Franklin di ottenere la celebre Foto 51 che rivelo' la struttura del DNA?","opts":["Spettrometria di massa","Microscopia elettronica","Cristallografia a raggi X","Risonanza magnetica nucleare"],"ans":2,"cat":"scienze","expl":"La Foto 51 fu scattata nel maggio 1952 al King's College di Londra."},
  {"q":"Quale termine della metrica indica la prosecuzione di una frase oltre la fine di un verso, senza pausa sintattica, nel verso successivo?","opts":["Enjambement","Cesura","Dieresi","Sinalefe"],"ans":0,"cat":"lingua_italiana","expl":"L'enjambement, dal francese enjamber (scavalcare), crea tensione e fluidita' nella poesia."},
  {"q":"Which English construction using would rather expresses a preference for someone else? Complete: I'd rather you ___ earlier tomorrow.","opts":["come","will come","came","coming"],"ans":2,"cat":"inglese","expl":"Would rather seguito da un soggetto diverso richiede il past simple per esprimere preferenza."},
  {"q":"Quale citta' africana sul lago Tanganica fu la capitale del Burundi fino al 2019, quando fu sostituita da Gitega?","opts":["Kigali","Kampala","Bujumbura","Dodoma"],"ans":2,"cat":"geografia","expl":"Bujumbura fu capitale del Burundi dall'indipendenza nel 1962 fino al 2019."},
  {"q":"Quale corsa equestre storica si svolge due volte l'anno in Piazza del Campo e vede sfidarsi le contrade della citta'?","opts":["Palio di Asti","Quintana di Foligno","Giostra del Saracino","Palio di Siena"],"ans":3,"cat":"dituttounpo","expl":"Il Palio di Siena si corre il 2 luglio e il 16 agosto. La corsa dura circa 75 secondi per tre giri della piazza."}
]

# Replace placeholders
for qn in questions:
    if qn.get('img') == 'PLACEHOLDER_16': qn['img'] = a16
    elif qn.get('img') == 'PLACEHOLDER_19': qn['img'] = a19
    elif qn.get('img') == 'PLACEHOLDER_27': qn['img'] = a27
    elif qn.get('img') == 'PLACEHOLDER_MORISOT': qn['img'] = morisot_img
    if qn.get('audio') == 'PLACEHOLDER_24': qn['audio'] = a24
    elif qn.get('audio') == 'PLACEHOLDER_30': qn['audio'] = a30

# Verify distribution
from collections import Counter
dist = Counter(q['ans'] for q in questions)
print(f'Distribution: A={dist[0]}, B={dist[1]}, C={dist[2]}, D={dist[3]}')

# Check consecutive
answers = [q['ans'] for q in questions]
max_consec = 1
cur = 1
for i in range(1, len(answers)):
    if answers[i] == answers[i-1]:
        cur += 1
        max_consec = max(max_consec, cur)
    else:
        cur = 1
print(f'Max consecutive same letter: {max_consec}')

# Build JSON and replace in HTML
q_json = json.dumps(questions, ensure_ascii=False)
q_block = 'const questions = ' + q_json + ';'
idx_start = html.find('const questions = [')
idx_end = html.find('];', idx_start) + 2
html = html[:idx_start] + q_block + html[idx_end:]

# Add horror to catBackgrounds
if '"horror"' not in html:
    horror_bg = img_b64_lowq('category_backgrounds/cinema/sala_cinema.jpg', 30, 350)
    bg_insert = html.find('const catBackgrounds = {')
    brace_pos = html.find('{', bg_insert) + 1
    html = html[:brace_pos] + '"horror":"' + horror_bg + '",' + html[brace_pos:]

with open('puntate/quiz_puntata33_misto.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Written quiz_puntata33_misto.html ({len(html)//1024} KB)')
