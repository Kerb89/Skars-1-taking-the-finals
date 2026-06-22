# Scarica sfondi HD da Unsplash per ogni categoria
# Esegui con: powershell -ExecutionPolicy Bypass -File download_backgrounds.ps1

$outDir = "c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS\category_backgrounds"

# Unsplash permette download diretto con dimensioni specifiche via URL
# Formato: https://unsplash.com/photos/{id}/download?w=1920
$images = @{
    "geografia.jpg"    = "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1920&q=80"
    "tecnologia.jpg"   = "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920&q=80"
    "scienze.jpg"      = "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=1920&q=80"
    "sport.jpg"        = "https://images.unsplash.com/photo-1461896836934-bd45ba8b2cda?w=1920&q=80"
    "storia.jpg"       = "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=1920&q=80"
    "cibo.jpg"         = "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=1920&q=80"
    "attualita.jpg"    = "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=1920&q=80"
    "matematica.jpg"   = "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1920&q=80"
    "musica.jpg"       = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1920&q=80"
    "cinema.jpg"       = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1920&q=80"
    "letteratura.jpg"  = "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1920&q=80"
    "arte.jpg"         = "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=1920&q=80"
    "inglese.jpg"      = "https://images.unsplash.com/photo-1543168256-418811576931?w=1920&q=80"
    "lingue.jpg"       = "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1920&q=80"
    "anagrammi.jpg"    = "https://images.unsplash.com/photo-1585504198199-20277593b94f?w=1920&q=80"
    "dituttounpo.jpg"  = "https://images.unsplash.com/photo-1484069560501-87d72b0c3669?w=1920&q=80"
}

$client = New-Object System.Net.WebClient
$count = 0

foreach ($file in $images.Keys) {
    $outPath = Join-Path $outDir $file
    Write-Host "Scaricando $file..." -NoNewline
    try {
        $client.DownloadFile($images[$file], $outPath)
        $size = [math]::Round((Get-Item $outPath).Length / 1KB, 1)
        Write-Host " OK ($size KB)" -ForegroundColor Green
        $count++
    } catch {
        Write-Host " ERRORE: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Scaricate $count/16 immagini ===" -ForegroundColor Cyan
$totalSize = [math]::Round((Get-ChildItem "$outDir\*.jpg" | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Host "Dimensione totale: $totalSize MB"
