import json, os

for f in ['mattia.json','jacopo.json','tato.json']:
    p = os.path.join('stats','players',f)
    with open(p,'r',encoding='utf-8') as fh:
        d = json.load(fh)
    name = f.replace('.json','').upper()
    print(f"{name}: {d['totalGames']} partite | {d['totalCorrect']}/{d['totalQuestions']} ({d['avgPercentage']}%) | {d['totalScore']} pt | {d['avgTime']}s")
    for g in d.get('games',[]):
        qid = g['quizId'].replace('quiz_puntata','P').replace('_misto','')
        print(f"  {qid}: {g['correct']}/{g['total']} ({g['percentage']}%) - {g['score']}pt")
    print()
