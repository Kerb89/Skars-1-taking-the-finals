$root = 'c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\canzoni'

$files = @(
    @{ src = "$root\Rosa Chemical, Bdope - POLKA 3 (mp3cut.net).mp3"; out = "$root\canzone4_clean.txt" },
    @{ src = "$root\M83 'Midnight City' Official video (mp3cut.net).mp3"; out = "$root\canzone5_clean.txt" },
    @{ src = "$root\Foster The People - Pumped Up Kicks (Official Video) (mp3cut.net).mp3"; out = "$root\canzone6_clean.txt" }
)

foreach ($f in $files) {
    $bytes = [System.IO.File]::ReadAllBytes($f.src)
    $b64 = [Convert]::ToBase64String($bytes)
    [System.IO.File]::WriteAllText($f.out, $b64)
    Write-Host "$($f.out | Split-Path -Leaf): $($b64.Length) caratteri"
}
Write-Host "Tutte convertite!"
