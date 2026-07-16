$b64_1 = [System.IO.File]::ReadAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone1_clean.txt')
$b64_2 = [System.IO.File]::ReadAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone2_clean.txt')
$b64_3 = [System.IO.File]::ReadAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone3_clean.txt')

$htmlTop = Get-Content 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\puntata2_top.html' -Raw -Encoding UTF8
$htmlBottom = Get-Content 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\puntata2_bottom.html' -Raw -Encoding UTF8

$htmlFinal = $htmlTop.Replace('__AUDIO_1__', $b64_1).Replace('__AUDIO_2__', $b64_2).Replace('__AUDIO_3__', $b64_3)
$htmlFinal = $htmlFinal + $htmlBottom

[System.IO.File]::WriteAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\quiz_puntata2_misto.html', $htmlFinal, [System.Text.Encoding]::UTF8)
$size = (Get-Item 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\quiz_puntata2_misto.html').Length / 1MB
Write-Host "Quiz Puntata 2 generato! Dimensione: $([math]::Round($size, 2)) MB"
