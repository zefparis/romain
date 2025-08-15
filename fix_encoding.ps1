# Script pour détecter et corriger les fichiers avec BOM
Write-Host "Détection des fichiers avec BOM..." -ForegroundColor Yellow

$bomFiles = @()
$extensions = @("*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.json", "*.html", "*.css", "*.md", "*.txt")

foreach ($ext in $extensions) {
    Get-ChildItem -Path "." -Recurse -Include $ext | ForEach-Object {
        $bytes = Get-Content $_.FullName -Raw -Encoding Byte -TotalCount 3
        if ($bytes -and $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            $bomFiles += $_.FullName
            Write-Host "BOM détecté: $($_.FullName)" -ForegroundColor Red
        }
    }
}

if ($bomFiles.Count -eq 0) {
    Write-Host "Aucun fichier avec BOM détecté." -ForegroundColor Green
} else {
    Write-Host "`nCorrection des fichiers avec BOM..." -ForegroundColor Yellow
    
    foreach ($file in $bomFiles) {
        try {
            # Lire le contenu sans BOM
            $content = Get-Content $file -Raw -Encoding UTF8
            # Réécrire sans BOM
            [System.IO.File]::WriteAllText($file, $content, [System.Text.UTF8Encoding]::new($false))
            Write-Host "Corrigé: $file" -ForegroundColor Green
        } catch {
            Write-Host "Erreur lors de la correction de $file : $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nCorrection terminée. $($bomFiles.Count) fichiers traités." -ForegroundColor Green
}

# Vérification finale
Write-Host "`nVérification finale..." -ForegroundColor Yellow
$remainingBomFiles = @()
foreach ($ext in $extensions) {
    Get-ChildItem -Path "." -Recurse -Include $ext | ForEach-Object {
        $bytes = Get-Content $_.FullName -Raw -Encoding Byte -TotalCount 3
        if ($bytes -and $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            $remainingBomFiles += $_.FullName
        }
    }
}

if ($remainingBomFiles.Count -eq 0) {
    Write-Host "✓ Tous les fichiers sont maintenant sans BOM." -ForegroundColor Green
} else {
    Write-Host "⚠ $($remainingBomFiles.Count) fichiers ont encore des problèmes BOM:" -ForegroundColor Red
    $remainingBomFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}
