$root = 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS'
$b64_7 = [System.IO.File]::ReadAllText("$root\canzoni\canzone7_clean.txt")
$b64_8 = [System.IO.File]::ReadAllText("$root\canzoni\canzone8_clean.txt")

$htmlTop = [System.IO.File]::ReadAllText("$root\scripts\puntata4_top.html", [System.Text.Encoding]::UTF8)
$backgrounds = [System.IO.File]::ReadAllText("$root\scripts\puntata4_backgrounds.js", [System.Text.Encoding]::UTF8)
$questions = [System.IO.File]::ReadAllText("$root\scripts\puntata4_questions.js", [System.Text.Encoding]::UTF8)
$htmlBottom = [System.IO.File]::ReadAllText("$root\scripts\puntata4_bottom.html", [System.Text.Encoding]::UTF8)

# Structure: top (has "const quizData = [") + questions (has "];") + backgrounds + bottom
$htmlFinal = $htmlTop + $questions + "`n" + $backgrounds + "`n" + $htmlBottom
$htmlFinal = $htmlFinal.Replace('__AUDIO_7__', $b64_7).Replace('__AUDIO_8__', $b64_8)

[System.IO.File]::WriteAllText("$root\quiz_puntata4_misto.html", $htmlFinal, [System.Text.Encoding]::UTF8)
$size = (Get-Item "$root\quiz_puntata4_misto.html").Length / 1MB
Write-Host "Quiz Puntata 4 generato! Dimensione: $([math]::Round($size, 2)) MB"
