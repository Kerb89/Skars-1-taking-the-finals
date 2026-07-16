$root = 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS'

$htmlTop = [System.IO.File]::ReadAllText("$root\scripts\puntata5_top.html", [System.Text.Encoding]::UTF8)
$questions = [System.IO.File]::ReadAllText("$root\scripts\puntata5_questions.js", [System.Text.Encoding]::UTF8)
$backgrounds = [System.IO.File]::ReadAllText("$root\scripts\puntata5_backgrounds.js", [System.Text.Encoding]::UTF8)
$htmlBottom = [System.IO.File]::ReadAllText("$root\scripts\puntata5_bottom.html", [System.Text.Encoding]::UTF8)

# Structure: top (has "const quizData = [") + questions (has "];") + backgrounds + bottom
$htmlFinal = $htmlTop + $questions + "`n" + $backgrounds + "`n" + $htmlBottom

[System.IO.File]::WriteAllText("$root\quiz_puntata5_misto.html", $htmlFinal, [System.Text.Encoding]::UTF8)
$size = (Get-Item "$root\quiz_puntata5_misto.html").Length / 1MB
Write-Host "Quiz Puntata 5 generato! Dimensione: $([math]::Round($size, 2)) MB"
