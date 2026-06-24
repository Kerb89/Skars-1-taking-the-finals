$root = 'd:\PROGETTO SKARS'
$bgDir = "$root\category_backgrounds"
$scriptsDir = "$root\scripts"
$outFile = "$root\vecchie_puntate\quiz_puntata7_misto.html"

# Categories used in this quiz
$categories = @(
    'sport', 'tecnologia', 'scienze', 'storia', 'cibo',
    'dituttounpo', 'matematica', 'musica', 'anagrammi',
    'letteratura', 'arte', 'lingua_italiana', 'lingue',
    'inglese', 'geografia', 'cinema'
)

# Build catBackgrounds JS object
$bgEntries = @()
foreach ($cat in $categories) {
    $imgFile = "$bgDir\$cat.jpg"
    if (Test-Path $imgFile) {
        $bytes = [System.IO.File]::ReadAllBytes($imgFile)
        $b64 = [System.Convert]::ToBase64String($bytes)
        $bgEntries += """$cat"":""data:image/jpeg;base64,$b64"""
    } else {
        Write-Host "WARNING: No image for category '$cat' at $imgFile"
    }
}
$bgJS = "const catBackgrounds = {" + ($bgEntries -join ",`n") + "};"

# Read HTML parts
$htmlTop = [System.IO.File]::ReadAllText("$scriptsDir\puntata7_top.html", [System.Text.Encoding]::UTF8)
$questionsJS = [System.IO.File]::ReadAllText("$scriptsDir\puntata7_questions.js", [System.Text.Encoding]::UTF8)
$htmlBottom = [System.IO.File]::ReadAllText("$scriptsDir\puntata7_bottom.html", [System.Text.Encoding]::UTF8)

# Assemble: top (opens questions array) + questions + backgrounds + bottom
$htmlFinal = $htmlTop + $questionsJS + "`n" + $bgJS + "`n" + $htmlBottom

[System.IO.File]::WriteAllText($outFile, $htmlFinal, [System.Text.Encoding]::UTF8)
$size = (Get-Item $outFile).Length / 1MB
Write-Host "Quiz Puntata 7 generato con successo! Dimensione: $([math]::Round($size, 2)) MB"
Write-Host "File: $outFile"
