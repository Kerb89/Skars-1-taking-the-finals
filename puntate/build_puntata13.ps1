# Build script for quiz_puntata13_misto.html
# Reads audio base64 files and assembles the final HTML

$ErrorActionPreference = "Stop"
$root = "c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS"

# Read audio files
Write-Host "Reading audio files..."
$bgMusic = Get-Content "$root\background_music\trivia_tension_b64.txt" -Raw
$glassAnimals = Get-Content "$root\canzoni\glass_animals_b64.txt" -Raw
$jungle = Get-Content "$root\canzoni\jungle_b64.txt" -Raw
$ariete = Get-Content "$root\canzoni\ariete_b64.txt" -Raw

# Trim whitespace
$bgMusic = $bgMusic.Trim()
$glassAnimals = $glassAnimals.Trim()
$jungle = $jungle.Trim()
$ariete = $ariete.Trim()

Write-Host "Building HTML..."

# Read the template
$template = Get-Content "$root\puntate\quiz_puntata13_template.html" -Raw

# Replace placeholders
$template = $template.Replace('__BG_MUSIC_B64__', $bgMusic)
$template = $template.Replace('__GLASS_ANIMALS_B64__', $glassAnimals)
$template = $template.Replace('__JUNGLE_B64__', $jungle)
$template = $template.Replace('__ARIETE_B64__', $ariete)

# Write final file
$template | Out-File "$root\puntate\quiz_puntata13_misto.html" -Encoding utf8

Write-Host "Done! quiz_puntata13_misto.html created."
