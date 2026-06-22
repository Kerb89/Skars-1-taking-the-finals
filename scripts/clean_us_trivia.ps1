# Script per rimuovere domande troppo US-specifiche dai database trivia
# Filtra domande che riguardano cultura generale specifica americana
# (NFL, NBA dettagliato, stati USA, presidenti minori, TV americana locale, ecc.)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
$inputDir = Join-Path $projectDir "trivial_pursuit"
$outputDir = Join-Path $projectDir "trivial_pursuit_clean"

# Crea cartella output
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Pattern US-specifici da filtrare (case-insensitive)
$usPatterns = @(
    # Sport americani specifici
    '\b(NFL|NFC|AFC)\b',
    '\bSuper Bowl\b',
    '\b(quarterback|touchdown|field goal|punt|wide receiver|tight end|linebacker|running back)\b',
    '\b(Yankees|Red Sox|Dodgers|Cubs|Mets|Cardinals|Giants|49ers|Patriots|Steelers|Cowboys|Eagles|Bears|Packers|Raiders|Dolphins|Broncos|Chiefs|Ravens|Colts|Bengals|Browns|Titans|Jaguars|Texans|Saints|Falcons|Buccaneers|Panthers|Seahawks|Rams|Vikings|Lions|Commanders|Chargers)\b',
    '\bMajor League Baseball\b',
    '\b(MLB|NBA|NHL)\b',
    '\bWorld Series\b',
    '\bHome Run\b',
    # Stati e geopolitica USA specifica
    '\b(Alabama|Alaska|Arizona|Arkansas|Connecticut|Delaware|Florida|Georgia|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Utah|Vermont|Virginia|West Virginia|Wisconsin|Wyoming)\b',
    '\bUS (state|president|constitution|amendment|congress|senate|supreme court)\b',
    '\bAmerican (Civil War|Revolution|Independence)\b',
    # Presidenti USA minori (lasciamo quelli famosi mondialmente)
    '\b(Millard Fillmore|Franklin Pierce|James Buchanan|Chester Arthur|Benjamin Harrison|William McKinley|Warren Harding|Calvin Coolidge|Herbert Hoover|Gerald Ford|James Polk|Zachary Taylor|Rutherford Hayes|James Garfield|William Taft|Grover Cleveland|Andrew Johnson|Martin Van Buren|John Tyler|William Henry Harrison)\b',
    # TV americana molto locale
    '\b(Jeopardy|Wheel of Fortune|The Price is Right|American Idol|Dancing with the Stars|The Bachelor|Bachelorette)\b',
    # Riferimenti US-only
    '\bPledge of Allegiance\b',
    '\bFourth of July\b',
    '\bThanksgiving\b',
    '\bMemorial Day\b',
    '\bLabor Day\b',
    '\b(SAT|ACT|GED)\b',
    '\bIvy League\b',
    '\b(DMV|IRS|FBI|CIA|NSA|DEA|ATF|USDA|EPA|FEMA|TSA|DHS|ICE)\b',
    # Vanity plates / US driving culture
    '\bvanity plate\b',
    '\b(freeway|interstate|highway patrol)\b'
)

# Combina tutti i pattern in un'unica regex
$combinedPattern = ($usPatterns -join '|')

$totalRemoved = 0
$totalKept = 0

foreach ($file in Get-ChildItem "$inputDir\*.json") {
    $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
    $originalCount = $content.Count
    
    # Filtra le domande
    $filtered = $content | Where-Object {
        $questionText = $_.question + " " + $_.answer + " " + ($_.choices -join " ")
        -not ($questionText -match $combinedPattern)
    }
    
    $filteredCount = $filtered.Count
    $removed = $originalCount - $filteredCount
    $totalRemoved += $removed
    $totalKept += $filteredCount
    
    # Salva il file pulito
    $filtered | ConvertTo-Json -Depth 10 | Set-Content "$outputDir\$($file.Name)" -Encoding UTF8
    
    Write-Host "$($file.Name): $originalCount -> $filteredCount (rimossi $removed)" -ForegroundColor $(if ($removed -gt 0) { "Yellow" } else { "Green" })
}

Write-Host ""
Write-Host "=== RIEPILOGO ===" -ForegroundColor Cyan
Write-Host "Domande totali originali: $($totalRemoved + $totalKept)"
Write-Host "Domande mantenute: $totalKept"
Write-Host "Domande rimosse (US-specific): $totalRemoved"
Write-Host "Output salvato in: $outputDir"
