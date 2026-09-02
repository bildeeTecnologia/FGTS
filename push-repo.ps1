# Script para fazer push do repositório FGTS WEB para bildeeTecnologia/FGTS

Write-Host "=== Push do Repositório FGTS WEB ===" -ForegroundColor Green
Write-Host ""

# Status atual
Write-Host "Status atual do Git:" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "=== Executando Push ===" -ForegroundColor Green
Write-Host ""

# Fazer push
git push -u origin main

Write-Host ""
Write-Host "=== Push Concluído ===" -ForegroundColor Green
Write-Host "Se solicitado, use suas credenciais GitHub:" -ForegroundColor Yellow
Write-Host "  - Username: seu usuário GitHub"
Write-Host "  - Password: seu Personal Access Token (não a senha do GitHub)"
Write-Host ""
