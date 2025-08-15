# Script PowerShell pour pousser vers GitHub
Write-Host "🔧 Configuration du repository Git..." -ForegroundColor Yellow

# Vérifier si on est dans un repo git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Pas de repository Git détecté. Initialisation..." -ForegroundColor Red
    git init
    Write-Host "✅ Repository Git initialisé." -ForegroundColor Green
}

# Ajouter tous les fichiers
Write-Host "📁 Ajout des fichiers..." -ForegroundColor Yellow
git add .

# Commit si nécessaire
$status = git status --porcelain
if ($status) {
    Write-Host "💾 Création du commit..." -ForegroundColor Yellow
    git commit -m "Fix encoding issues and add UTF-8 declarations"
    Write-Host "✅ Commit créé." -ForegroundColor Green
} else {
    Write-Host "ℹ️ Aucun changement à commiter." -ForegroundColor Blue
}

# Vérifier si le remote origin existe
$remotes = git remote
if ($remotes -notcontains "origin") {
    Write-Host "🌐 Ajout du remote origin..." -ForegroundColor Yellow
    git remote add origin "https://github.com/zefparis/romain.git"
    Write-Host "✅ Remote origin ajouté." -ForegroundColor Green
} else {
    Write-Host "ℹ️ Remote origin déjà configuré." -ForegroundColor Blue
}

# Renommer la branche en main
Write-Host "🔄 Configuration de la branche main..." -ForegroundColor Yellow
git branch -M main

# Push vers GitHub
Write-Host "🚀 Push vers GitHub..." -ForegroundColor Yellow
try {
    git push -u origin main
    Write-Host "✅ Push réussi vers https://github.com/zefparis/romain.git" -ForegroundColor Green
    Write-Host "🎉 Votre code est maintenant sur GitHub!" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Erreur lors du push: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Vérifiez vos permissions GitHub et votre authentification." -ForegroundColor Yellow
}

Write-Host "`n📊 Statut final du repository:" -ForegroundColor Yellow
git status
