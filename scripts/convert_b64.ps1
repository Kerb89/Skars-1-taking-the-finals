$bytes = [System.IO.File]::ReadAllBytes('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\Canzone3.mp3')
$b64 = [Convert]::ToBase64String($bytes)
Write-Host "Lunghezza base64: $($b64.Length) caratteri"
[System.IO.File]::WriteAllText('c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni\canzone3_clean.txt', $b64)
Write-Host "Salvato in canzoni/canzone3_clean.txt"
