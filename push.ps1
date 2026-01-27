# PowerShell script to run git push
cd $PSScriptRoot
git add -A
Write-Host "Pushing to origin main..." -ForegroundColor Cyan
git push origin main
Write-Host "Done!" -ForegroundColor Green
Read-Host "Press Enter to exit"
