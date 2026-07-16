$root = 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS'
$b64_4 = [System.IO.File]::ReadAllText("$root\canzoni\canzone4_clean.txt")
$b64_5 = [System.IO.File]::ReadAllText("$root\canzoni\canzone5_clean.txt")
$b64_6 = [System.IO.File]::ReadAllText("$root\canzoni\canzone6_clean.txt")

$htmlTop = [System.IO.File]::ReadAllText("$root\scripts\puntata3_top.html", [System.Text.Encoding]::UTF8)
$htmlBottom = [System.IO.File]::ReadAllText("$root\scripts\puntata3_bottom.html", [System.Text.Encoding]::UTF8)

$htmlFinal = $htmlTop.Replace('__AUDIO_4__', $b64_4).Replace('__AUDIO_5__', $b64_5).Replace('__AUDIO_6__', $b64_6)
$htmlFinal = $htmlFinal + $htmlBottom

[System.IO.File]::WriteAllText("$root\quiz_puntata3_misto.html", $htmlFinal, [System.Text.Encoding]::UTF8)
$size = (Get-Item "$root\quiz_puntata3_misto.html").Length / 1MB
Write-Host "Quiz Puntata 3 generato! Dimensione: $([math]::Round($size, 2)) MB"
