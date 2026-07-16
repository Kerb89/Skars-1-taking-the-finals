$newCSS = @"
        /* Tablet e smartphone larghi (< 768px) */
        @media (max-width: 768px) {
            body { padding: 16px; }
            .container { max-width: 100%; }
            .question-card { padding: 24px 20px; }
            .header h1 { font-size: 1.4rem; }
            .option-btn { padding: 16px 18px; font-size: 1rem; }
        }
        /* Smartphone standard (< 500px) */
        @media (max-width: 500px) {
            body { padding: 10px; }
            .header h1 { font-size: 1.2rem; }
            .header .subtitle { font-size: 0.8rem; }
            .question-card { padding: 18px 14px; border-radius: 12px; }
            .question-text { font-size: 1rem; line-height: 1.45; margin-bottom: 16px; }
            .question-number { font-size: 0.7rem; }
            .question-category { font-size: 0.65rem; padding: 2px 8px; }
            .score-bar { padding: 10px 14px; border-radius: 10px; gap: 6px; }
            .score-bar .score { font-size: 1.1rem; }
            .score-bar .progress { font-size: 0.8rem; }
            .timer-bar { width: 70px; }
            .timer-text { font-size: 0.8rem; }
            .option-btn { padding: 14px 14px; font-size: 0.95rem; border-radius: 8px; }
            .btn { padding: 12px 18px; font-size: 0.9rem; }
            .btn-multiplier { padding: 8px 12px; font-size: 0.8rem; }
            .btn-contest { padding: 8px 12px; font-size: 0.8rem; }
            .intro-content { padding: 28px 18px; border-radius: 12px; }
            .intro-content .intro-cat { font-size: 0.7rem; }
            .intro-content .intro-q { font-size: 1rem; line-height: 1.4; }
            .intro-content .intro-hint { font-size: 0.75rem; }
            .feedback { font-size: 0.85rem; padding: 8px 12px; }
            .name-card { padding: 28px 20px; }
            .name-card h2 { font-size: 1.1rem; }
            .summary-stats { grid-template-columns: repeat(2, 1fr); gap: 8px; }
            .stat-card { padding: 12px; }
            .stat-card .stat-value { font-size: 1.2rem; }
            .stat-card .stat-label { font-size: 0.65rem; }
            .summary-list { padding: 12px; }
            .summary-item { font-size: 0.8rem; }
        }
        /* Smartphone piccoli tipo iPhone SE (< 375px) */
        @media (max-width: 375px) {
            body { padding: 6px; }
            .header h1 { font-size: 1.05rem; }
            .question-card { padding: 14px 10px; }
            .question-text { font-size: 0.92rem; }
            .option-btn { padding: 12px 10px; font-size: 0.88rem; }
            .score-bar { padding: 8px 10px; }
            .score-bar .score { font-size: 1rem; }
            .timer-bar { width: 60px; }
            .btn { padding: 10px 14px; font-size: 0.85rem; }
            .intro-content .intro-q { font-size: 0.92rem; }
            .name-card { padding: 20px 14px; width: 95%; }
            .summary-stats { grid-template-columns: repeat(2, 1fr); gap: 6px; }
        }
"@

$files = Get-ChildItem "puntate\*.html"
$count = 0

foreach ($f in $files) {
    $content = [System.IO.File]::ReadAllText($f.FullName)
    if ($content -match '@media \(max-width:\s*500px\)') {
        $content = $content -replace '@media \(max-width:\s*500px\)\s*\{[^\n]+\}', $newCSS
        [System.IO.File]::WriteAllText($f.FullName, $content)
        $count++
        Write-Host "Updated: $($f.Name)"
    } else {
        Write-Host "Skipped (no match): $($f.Name)"
    }
}
Write-Host "`nTotal updated: $count"
