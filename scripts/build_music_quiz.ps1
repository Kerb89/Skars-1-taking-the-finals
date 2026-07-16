$b64_1 = [System.IO.File]::ReadAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone1_clean.txt')
$b64_2 = [System.IO.File]::ReadAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone2_clean.txt')
$b64_3 = [System.IO.File]::ReadAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone3_clean.txt')

$html = @"
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quizzone - Test Musica</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1923; color: #e0e6ed; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .container { max-width: 700px; width: 100%; }
        h1 { text-align: center; margin-bottom: 8px; font-size: 1.5rem; }
        .subtitle { text-align: center; color: #8899aa; font-size: 0.9rem; margin-bottom: 30px; }
        .question-card { background: #f8f9fa; border-radius: 16px; padding: 28px 24px; color: #1a1a2e; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); display: none; }
        .question-card.active { display: block; }
        .q-label { font-size: 0.8rem; font-weight: 600; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .q-text { font-size: 1.1rem; font-weight: 500; margin-bottom: 16px; }
        .audio-player { display: flex; align-items: center; gap: 12px; background: #1a1a2e; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; }
        .play-btn { width: 50px; height: 50px; border-radius: 50%; background: #4fc3f7; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; flex-shrink: 0; }
        .play-btn:hover { background: #29b6f6; }
        .play-btn svg { fill: #0f1923; width: 22px; height: 22px; }
        .audio-info { flex: 1; }
        .audio-info .status { color: #4fc3f7; font-weight: 600; font-size: 0.85rem; }
        .audio-bar { width: 100%; height: 4px; background: #37474f; border-radius: 2px; margin-top: 6px; overflow: hidden; }
        .audio-bar-fill { height: 100%; background: #4fc3f7; width: 0%; transition: width 0.1s linear; }
        .timer-display { color: #ffb74d; font-weight: 700; font-size: 1.1rem; min-width: 40px; text-align: right; }
        .options { display: flex; flex-direction: column; gap: 10px; }
        .option-btn { display: block; width: 100%; padding: 14px 18px; border: 2px solid #dee2e6; border-radius: 10px; background: #fff; color: #1a1a2e; font-size: 1rem; text-align: left; cursor: pointer; transition: all 0.2s; outline: none; }
        .option-btn:hover:not(.disabled) { border-color: #4fc3f7; background: #e3f7ff; }
        .option-btn.selected { border-color: #4fc3f7; background: #e3f7ff; font-weight: 600; }
        .option-btn.correct { border-color: #43a047; background: #e8f5e9; color: #2e7d32; font-weight: 600; }
        .option-btn.wrong { border-color: #e53935; background: #ffebee; color: #c62828; font-weight: 600; }
        .option-btn.disabled { cursor: default; opacity: 0.7; }
        .btn-row { margin-top: 16px; display: flex; gap: 10px; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; background: #4fc3f7; color: #0f1923; transition: background 0.2s; }
        .btn:hover { background: #29b6f6; }
        .btn:disabled { background: #546e7a; color: #90a4ae; cursor: not-allowed; }
        .feedback { margin-top: 12px; padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; font-weight: 500; display: none; }
        .feedback.visible { display: block; }
        .feedback.correct-fb { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
        .feedback.wrong-fb { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
        .result { background: #1a2a3a; border-radius: 12px; padding: 24px; text-align: center; display: none; }
        .result.visible { display: block; }
        .result h2 { margin-bottom: 16px; }
        .result .score { font-size: 2rem; color: #4fc3f7; font-weight: 700; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Quizzone — Test Musica</h1>
        <div class="subtitle">3 domande musicali con audio incorporato — 30 secondi a domanda</div>
        <div id="quizContainer"></div>
        <div class="result" id="result">
            <h2>Risultato</h2>
            <div class="score" id="finalScore"></div>
        </div>
    </div>
    <script>
    const musicQuiz = [
        {
            q: "Chi canta questa canzone?",
            audio: "data:audio/mp3;base64,$b64_1",
            opts: ["Dua Lipa", "Sam Smith", "Harry Styles", "Ed Sheeran"],
            ans: 1
        },
        {
            q: "Di quale artista e' questo brano?",
            audio: "data:audio/mp3;base64,$b64_2",
            opts: ["Bruno Mars", "Daft Punk", "The Weeknd", "Calvin Harris"],
            ans: 2
        },
        {
            q: "Quale artista italiano canta questa canzone?",
            audio: "data:audio/mp3;base64,$b64_3",
            opts: ["Mahmood", "Francesco Gabbani", "Maneskin", "Gianni Morandi"],
            ans: 1
        }
    ];

    let currentQ = 0;
    let correctCount = 0;
    let selectedOpt = -1;
    let confirmed = false;
    let timerInterval = null;
    let timerStarted = false;
    let timeLeft = 30;
    const TIMER_DURATION = 30;

    function renderQuiz() {
        const container = document.getElementById('quizContainer');
        let html = '';
        musicQuiz.forEach((item, i) => {
            const labels = ['A', 'B', 'C', 'D'];
            html += '<div class="question-card' + (i === 0 ? ' active' : '') + '" id="card' + i + '">';
            html += '<div class="q-label">Domanda ' + (i+1) + ' di 3</div>';
            html += '<div class="q-text">' + item.q + '</div>';
            html += '<div class="audio-player">';
            html += '<button class="play-btn" id="playBtn' + i + '" onclick="togglePlay(' + i + ')"><svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg></button>';
            html += '<div class="audio-info"><div class="status" id="status' + i + '">Premi &#9654; per ascoltare</div><div class="audio-bar"><div class="audio-bar-fill" id="bar' + i + '"></div></div></div>';
            html += '<div class="timer-display" id="timer' + i + '">30s</div>';
            html += '</div>';
            html += '<div class="options" id="opts' + i + '">';
            item.opts.forEach(function(opt, j) { html += '<button class="option-btn" onclick="selectOpt(' + i + ',' + j + ')">' + labels[j] + ') ' + opt + '</button>'; });
            html += '</div>';
            html += '<div class="feedback" id="fb' + i + '"></div>';
            html += '<div class="btn-row"><button class="btn" id="confirmBtn' + i + '" onclick="confirmAnswer(' + i + ')" disabled>Conferma</button><button class="btn" id="nextBtn' + i + '" onclick="nextQuestion()" style="display:none">Prossima &rarr;</button></div>';
            html += '</div>';
        });
        container.innerHTML = html;
    }

    let audios = [];
    function initAudios() {
        musicQuiz.forEach(function(item, i) { audios[i] = new Audio(item.audio); });
    }

    let progressInterval = null;

    function togglePlay(i) {
        if (confirmed) return;
        if (!audios[i]) return;
        const state = audios[i].paused;
        if (state) {
            audios[i].play();
            document.getElementById('status' + i).textContent = '\u266A In riproduzione...';
            document.getElementById('playBtn' + i).innerHTML = '<svg viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" fill="#0f1923"/><rect x="14" y="4" width="4" height="16" fill="#0f1923"/></svg>';
            startProgress(i);
            if (!timerStarted) { timerStarted = true; startTimer(i); }
        } else {
            audios[i].pause();
            document.getElementById('status' + i).textContent = 'In pausa';
            document.getElementById('playBtn' + i).innerHTML = '<svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21" fill="#0f1923"/></svg>';
            stopProgress();
        }
    }

    function startProgress(i) {
        stopProgress();
        progressInterval = setInterval(function() {
            if (!audios[i] || audios[i].paused) { stopProgress(); return; }
            var pct = (audios[i].currentTime / audios[i].duration) * 100;
            document.getElementById('bar' + i).style.width = pct + '%';
            if (audios[i].currentTime >= audios[i].duration) { stopProgress(); document.getElementById('status' + i).textContent = 'Terminato'; document.getElementById('playBtn' + i).innerHTML = '<svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21" fill="#0f1923"/></svg>'; }
        }, 100);
    }
    function stopProgress() { if (progressInterval) { clearInterval(progressInterval); progressInterval = null; } }

    function startTimer(i) {
        timeLeft = TIMER_DURATION;
        document.getElementById('timer' + i).textContent = timeLeft + 's';
        timerInterval = setInterval(function() {
            timeLeft--;
            document.getElementById('timer' + i).textContent = timeLeft + 's';
            if (timeLeft <= 5) document.getElementById('timer' + i).style.color = '#ef5350';
            if (timeLeft <= 0) { clearInterval(timerInterval); handleTimeout(i); }
        }, 1000);
    }

    function handleTimeout(i) {
        if (confirmed) return;
        confirmed = true;
        if (audios[i]) audios[i].pause();
        stopProgress();
        var btns = document.getElementById('opts' + i).querySelectorAll('.option-btn');
        btns.forEach(function(btn, j) { btn.classList.add('disabled'); if (j === musicQuiz[i].ans) btn.classList.add('correct'); });
        var fb = document.getElementById('fb' + i);
        fb.classList.add('visible', 'wrong-fb');
        var labels = ['A','B','C','D'];
        fb.textContent = '\u2717 Tempo scaduto! La risposta era ' + labels[musicQuiz[i].ans] + ') ' + musicQuiz[i].opts[musicQuiz[i].ans];
        document.getElementById('confirmBtn' + i).style.display = 'none';
        document.getElementById('nextBtn' + i).style.display = '';
    }

    function selectOpt(qi, oi) {
        if (confirmed) return;
        selectedOpt = oi;
        var btns = document.getElementById('opts' + qi).querySelectorAll('.option-btn');
        btns.forEach(function(btn, j) { btn.classList.toggle('selected', j === oi); });
        document.getElementById('confirmBtn' + qi).disabled = false;
    }

    function confirmAnswer(qi) {
        if (selectedOpt < 0 || confirmed) return;
        confirmed = true;
        clearInterval(timerInterval);
        if (audios[qi]) audios[qi].pause();
        stopProgress();
        var chosen = selectedOpt;
        var correct = musicQuiz[qi].ans;
        var isCorrect = chosen === correct;
        if (isCorrect) correctCount++;
        var btns = document.getElementById('opts' + qi).querySelectorAll('.option-btn');
        btns.forEach(function(btn, j) { btn.classList.add('disabled'); if (j === correct) btn.classList.add('correct'); if (j === chosen && !isCorrect) btn.classList.add('wrong'); });
        var fb = document.getElementById('fb' + qi);
        fb.classList.add('visible');
        var labels = ['A','B','C','D'];
        if (isCorrect) { fb.classList.add('correct-fb'); fb.textContent = '\u2713 Corretta!'; }
        else { fb.classList.add('wrong-fb'); fb.textContent = '\u2717 Sbagliata — era ' + labels[correct] + ') ' + musicQuiz[qi].opts[correct]; }
        document.getElementById('confirmBtn' + qi).style.display = 'none';
        document.getElementById('nextBtn' + qi).style.display = '';
    }

    function nextQuestion() {
        document.getElementById('card' + currentQ).classList.remove('active');
        currentQ++;
        if (currentQ >= musicQuiz.length) {
            var res = document.getElementById('result');
            res.classList.add('visible');
            document.getElementById('finalScore').textContent = correctCount + ' / 3 corrette';
        } else {
            document.getElementById('card' + currentQ).classList.add('active');
            selectedOpt = -1;
            confirmed = false;
            timerStarted = false;
            timeLeft = TIMER_DURATION;
        }
    }

    renderQuiz();
    initAudios();
    </script>
</body>
</html>
"@

[System.IO.File]::WriteAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\quiz_musica_test.html', $html, [System.Text.Encoding]::UTF8)
Write-Host "Quiz musicale generato! Dimensione file:"
(Get-Item 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\quiz_musica_test.html').Length / 1MB
Write-Host "MB"
